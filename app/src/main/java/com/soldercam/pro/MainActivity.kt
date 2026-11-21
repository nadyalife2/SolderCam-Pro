package com.soldercam.pro

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.ImageFormat
import android.graphics.SurfaceTexture
import android.hardware.camera2.*
import android.media.ImageReader
import android.media.MediaRecorder
import android.os.*
import android.util.Log
import android.view.Surface
import android.view.TextureView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import com.soldercam.pro.databinding.ActivityMainBinding
import java.io.File
import java.io.FileOutputStream

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var cameraManager: CameraManager
    private var cameraDevice: CameraDevice? = null
    private var captureSession: CameraCaptureSession? = null
    private lateinit var previewRequestBuilder: CaptureRequest.Builder

    private var backgroundThread: HandlerThread? = null
    private var backgroundHandler: Handler? = null

    private var mainCameraId: String = "0"
    private var cameraCharacteristics: CameraCharacteristics? = null
    private var minFocusDistance: Float = 10.0f
    private var isRecording = false
    private var mediaRecorder: MediaRecorder? = null
    private var rawImageReader: ImageReader? = null

    private var isRawSensorMode = true
    private var isAeAwbLocked = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        cameraManager = getSystemService(Context.CAMERA_SERVICE) as CameraManager
        setupListeners()
    }

    private fun setupListeners() {
        // Ползунок ручного микрофокуса
        binding.sliderFocus.addOnChangeListener { _, value, _ ->
            binding.tvFocusLabel.text = String.format("MF: %.2f dpt", value)
            updateManualFocus(value)
        }

        // Кнопка включения/выключения чистого сенсора (без шумодава и шарпенинга)
        binding.btnRawProcessing.setOnClickListener {
            isRawSensorMode = !isRawSensorMode
            if (isRawSensorMode) {
                binding.btnRawProcessing.text = "Чистый сенсор: ВКЛ"
                binding.btnRawProcessing.setTextColor(getColor(R.color.neon_green))
            } else {
                binding.btnRawProcessing.text = "Сток обработка"
                binding.btnRawProcessing.setTextColor(getColor(R.color.white))
            }
            applySensorSettings()
        }

        // Блокировка экспозиции и баланса белого (припой не меняет цвет)
        binding.btnLockExposure.setOnClickListener {
            isAeAwbLocked = !isAeAwbLocked
            if (isAeAwbLocked) {
                binding.btnLockExposure.text = "AE/AWB: ЗАБЛОКИРОВАНО"
                binding.btnLockExposure.setTextColor(getColor(R.color.neon_green))
            } else {
                binding.btnLockExposure.text = "AE/AWB: АВТО"
                binding.btnLockExposure.setTextColor(getColor(R.color.white))
            }
            applyExposureLock()
        }

        // Съемка несжатого RAW DNG кадра для макро-инспекции
        binding.btnCaptureDng.setOnClickListener {
            captureRawDng()
        }

        // Диагностика аккумулятора OnePlus Nord N10 5G
                binding.btnBatteryDiag.setOnLongClickListener {
            ClusterNodeManager.showCleanTermuxDialog(this)
            true
        }

        binding.btnBatteryDiag.setOnClickListener {
            startActivity(android.content.Intent(this, BatteryDiagnosticsActivity::class.java))
        }

        // Журнал багов, крашей и тестов
        binding.btnBugTracker.setOnClickListener {
            startActivity(android.content.Intent(this, BugTrackerActivity::class.java))
        }

        // Запись видео 60 Mbps
        binding.fabRecord.setOnClickListener {
            if (isRecording) {
                stopRecording()
            } else {
                startRecording()
            }
        }
    }

    private fun startBackgroundThread() {
        backgroundThread = HandlerThread("Camera2Background").also { it.start() }
        backgroundHandler = Handler(backgroundThread!!.looper)
    }

    private fun stopBackgroundThread() {
        backgroundThread?.quitSafely()
        try {
            backgroundThread?.join()
            backgroundThread = null
            backgroundHandler = null
        } catch (e: InterruptedException) {
            e.printStackTrace()
        }
    }

    private val surfaceTextureListener = object : TextureView.SurfaceTextureListener {
        override fun onSurfaceTextureAvailable(surface: SurfaceTexture, width: Int, height: Int) {
            openCamera()
        }
        override fun onSurfaceTextureSizeChanged(surface: SurfaceTexture, width: Int, height: Int) {}
        override fun onSurfaceTextureDestroyed(surface: SurfaceTexture): Boolean = true
        override fun onSurfaceTextureUpdated(surface: SurfaceTexture) {}
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 100) {
            val cameraGranted = grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED
            if (cameraGranted) {
                if (binding.textureView.isAvailable) {
                    openCamera()
                } else {
                    binding.textureView.surfaceTextureListener = surfaceTextureListener
                }
            } else {
                Toast.makeText(this, "Требуется разрешение камеры для работы", Toast.LENGTH_LONG).show()
            }
        }
    }

    @SuppressLint("MissingPermission")
    private fun openCamera() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.CAMERA, Manifest.permission.RECORD_AUDIO), 100)
            return
        }

        try {
            for (id in cameraManager.cameraIdList) {
                val chars = cameraManager.getCameraCharacteristics(id)
                val facing = chars.get(CameraCharacteristics.LENS_FACING)
                if (facing == CameraCharacteristics.LENS_FACING_BACK) {
                    mainCameraId = id
                    cameraCharacteristics = chars
                    minFocusDistance = chars.get(CameraCharacteristics.LENS_INFO_MINIMUM_FOCUS_DISTANCE) ?: 10.0f

                    setupRawReader(chars)

                    runOnUiThread {
                        val maxFocus = if (minFocusDistance > 0f) minFocusDistance else 10.0f
                        binding.sliderFocus.valueFrom = 0.0f
                        binding.sliderFocus.valueTo = maxFocus
                        binding.sliderFocus.value = (maxFocus * 0.7f).coerceIn(0f, maxFocus)
                    }
                    break
                }
            }

            cameraManager.openCamera(mainCameraId, object : CameraDevice.StateCallback() {
                override fun onOpened(camera: CameraDevice) {
                    cameraDevice = camera
                    startPreviewSession()
                }

                override fun onDisconnected(camera: CameraDevice) {
                    camera.close()
                    cameraDevice = null
                }

                override fun onError(camera: CameraDevice, error: Int) {
                    camera.close()
                    cameraDevice = null
                }
            }, backgroundHandler)

        } catch (e: Exception) {
            Log.e("SolderCam", "Ошибка открытия камеры: ${e.message}")
        }
    }

    private fun setupRawReader(chars: CameraCharacteristics) {
        val map = chars.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP)
        val rawSizes = map?.getOutputSizes(ImageFormat.RAW_SENSOR)
        if (!rawSizes.isNullOrEmpty()) {
            val safeRawSize = rawSizes.filter { it.width * it.height <= 16_000_000 }.maxByOrNull { it.width * it.height }
                ?: rawSizes.minByOrNull { it.width * it.height }
                ?: rawSizes[0]
            rawImageReader = ImageReader.newInstance(
                safeRawSize.width,
                safeRawSize.height,
                ImageFormat.RAW_SENSOR,
                1
            )
            rawImageReader?.setOnImageAvailableListener({ reader ->
                val image = reader.acquireLatestImage() ?: return@setOnImageAvailableListener
                saveDng(image)
            }, backgroundHandler)
        }
    }

    private fun startPreviewSession() {
        val texture = binding.textureView.surfaceTexture ?: return
        texture.setDefaultBufferSize(1920, 1080)
        val previewSurface = Surface(texture)

        try {
            previewRequestBuilder = cameraDevice!!.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
            previewRequestBuilder.addTarget(previewSurface)

            applySensorSettings()
            updateManualFocus(binding.sliderFocus.value)

            val surfaces = mutableListOf(previewSurface)
            rawImageReader?.surface?.let { surfaces.add(it) }

            cameraDevice!!.createCaptureSession(
                surfaces,
                object : CameraCaptureSession.StateCallback() {
                    override fun onConfigured(session: CameraCaptureSession) {
                        captureSession = session
                        captureSession?.setRepeatingRequest(previewRequestBuilder.build(), null, backgroundHandler)
                    }

                    override fun onConfigureFailed(session: CameraCaptureSession) {
                        Log.e("SolderCam", "Конфигурация превью завершилась ошибкой")
                    }
                },
                backgroundHandler
            )
        } catch (e: Exception) {
            Log.e("SolderCam", "Ошибка создания сессии", e)
        }
    }

    private fun applySensorSettings() {
        if (!::previewRequestBuilder.isInitialized) return
        if (isRawSensorMode) {
            // Отключаем размытие/шумодав ISP процессора Qualcomm
            previewRequestBuilder.set(CaptureRequest.NOISE_REDUCTION_MODE, CaptureRequest.NOISE_REDUCTION_MODE_OFF)
            // Отключаем ореолы искусственного шарпенинга
            previewRequestBuilder.set(CaptureRequest.EDGE_MODE, CaptureRequest.EDGE_MODE_OFF)
            // Ровная тональная кривая (без клиппинга бликов от припоя)
            previewRequestBuilder.set(CaptureRequest.TONEMAP_MODE, CaptureRequest.TONEMAP_MODE_FAST)
        } else {
            previewRequestBuilder.set(CaptureRequest.NOISE_REDUCTION_MODE, CaptureRequest.NOISE_REDUCTION_MODE_HIGH_QUALITY)
            previewRequestBuilder.set(CaptureRequest.EDGE_MODE, CaptureRequest.EDGE_MODE_HIGH_QUALITY)
        }
        applyRepeating()
    }

    private fun updateManualFocus(focusDistance: Float) {
        if (!::previewRequestBuilder.isInitialized) return
        previewRequestBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF)
        previewRequestBuilder.set(CaptureRequest.LENS_FOCUS_DISTANCE, focusDistance)
        applyRepeating()
    }

    private fun applyExposureLock() {
        if (!::previewRequestBuilder.isInitialized) return
        previewRequestBuilder.set(CaptureRequest.CONTROL_AE_LOCK, isAeAwbLocked)
        previewRequestBuilder.set(CaptureRequest.CONTROL_AWB_LOCK, isAeAwbLocked)
        applyRepeating()
    }

    private fun applyRepeating() {
        val session = captureSession ?: return
        if (!::previewRequestBuilder.isInitialized) return
        try {
            session.setRepeatingRequest(previewRequestBuilder.build(), null, backgroundHandler)
            BugTracker.currentCameraInfo = "OV64B активна | Фокус: ${String.format("%.2f", binding.sliderFocus.value)} dpt | Сенсор: $isRawSensorMode | AE/AWB Lock: $isAeAwbLocked"
        } catch (e: Exception) {
            Log.e("SolderCam", "Ошибка обновления запроса", e)
        }
    }

    private fun captureRawDng() {
        val device = cameraDevice ?: return
        val readerSurface = rawImageReader?.surface ?: run {
            Toast.makeText(this, "RAW формат не поддерживается данным потоком", Toast.LENGTH_SHORT).show()
            return
        }

        try {
            val captureBuilder = device.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE)
            captureBuilder.addTarget(readerSurface)
            captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF)
            captureBuilder.set(CaptureRequest.LENS_FOCUS_DISTANCE, binding.sliderFocus.value)

            captureSession?.capture(captureBuilder.build(), object : CameraCaptureSession.CaptureCallback() {
                override fun onCaptureCompleted(
                    session: CameraCaptureSession,
                    request: CaptureRequest,
                    result: TotalCaptureResult
                ) {
                    lastCaptureResult = result
                }
            }, backgroundHandler)

            Toast.makeText(this, "Снимок RAW сохранен!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Log.e("SolderCam", "Ошибка съемки RAW", e)
        }
    }

    private var lastCaptureResult: TotalCaptureResult? = null

    private fun saveDng(image: android.media.Image) {
        val result = lastCaptureResult
        val chars = cameraCharacteristics
        if (result == null || chars == null) {
            image.close()
            return
        }

        try {
            val targetDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES) ?: filesDir
            val dngFile = File(targetDir, "SOLDER_${System.currentTimeMillis()}.dng")
            val dngCreator = DngCreator(chars, result)
            dngCreator.use { creator ->
                FileOutputStream(dngFile).use { outStream ->
                    creator.writeImage(outStream, image)
                }
            }
            Log.d("SolderCam", "DNG сохранен: ${dngFile.absolutePath}")
            runOnUiThread {
                Toast.makeText(this, "RAW сохранен: ${dngFile.name}", Toast.LENGTH_SHORT).show()
            }
        } catch (e: Exception) {
            Log.e("SolderCam", "Ошибка записи DNG", e)
        } finally {
            image.close()
        }
    }

    private fun startRecording() {
        try {
            val moviesDir = getExternalFilesDir(Environment.DIRECTORY_MOVIES) ?: filesDir
            val videoFile = File(moviesDir, "SOLDER_${System.currentTimeMillis()}.mp4")
            mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                MediaRecorder(this)
            } else {
                @Suppress("DEPRECATION")
                MediaRecorder()
            }.apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setVideoSource(MediaRecorder.VideoSource.SURFACE)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setOutputFile(videoFile.absolutePath)
                setVideoEncodingBitRate(30_000_000) // 30 Mbps
                setVideoFrameRate(30)
                setVideoSize(1920, 1080)
                setVideoEncoder(MediaRecorder.VideoEncoder.H264)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                prepare()
            }

            val recorderSurface = mediaRecorder?.surface
            val texture = binding.textureView.surfaceTexture
            if (recorderSurface != null && texture != null && cameraDevice != null) {
                val previewSurface = Surface(texture)
                val surfaces = listOf(previewSurface, recorderSurface)

                cameraDevice?.createCaptureSession(surfaces, object : CameraCaptureSession.StateCallback() {
                    override fun onConfigured(session: CameraCaptureSession) {
                        captureSession = session
                        try {
                            val recordRequest = cameraDevice?.createCaptureRequest(CameraDevice.TEMPLATE_RECORD)?.apply {
                                addTarget(previewSurface)
                                addTarget(recorderSurface)
                                set(CaptureRequest.CONTROL_MODE, CameraMetadata.CONTROL_MODE_AUTO)
                            }
                            recordRequest?.let { session.setRepeatingRequest(it.build(), null, backgroundHandler) }
                            mediaRecorder?.start()
                            isRecording = true
                            runOnUiThread {
                                binding.tvStatus.text = "REC\n30 Mbps"
                                binding.fabRecord.setImageResource(android.R.drawable.ic_media_pause)
                                Toast.makeText(this@MainActivity, "Запись запущена", Toast.LENGTH_SHORT).show()
                            }
                        } catch (e: Exception) {
                            Log.e("SolderCam", "Ошибка запуска записи", e)
                            stopRecording()
                        }
                    }

                    override fun onConfigureFailed(session: CameraCaptureSession) {
                        runOnUiThread {
                            Toast.makeText(this@MainActivity, "Ошибка конфигурации видеопотока", Toast.LENGTH_SHORT).show()
                        }
                    }
                }, backgroundHandler)
            }
        } catch (e: Exception) {
            Log.e("SolderCam", "Ошибка MediaRecorder", e)
            Toast.makeText(this, "Сбой записи: ${e.message}", Toast.LENGTH_SHORT).show()
            isRecording = false
        }
    }

    private fun stopRecording() {
        if (!isRecording && mediaRecorder == null) return
        try {
            mediaRecorder?.apply {
                try {
                    stop()
                } catch (e: Exception) {
                    Log.w("SolderCam", "Исключение при остановке MediaRecorder: ${e.message}")
                }
                reset()
                release()
            }
            mediaRecorder = null
            startPreviewSession()
        } catch (e: Exception) {
            Log.e("SolderCam", "Сбой освобождения рекордера", e)
        } finally {
            isRecording = false
            runOnUiThread {
                binding.tvStatus.text = "СТОП\nГотов"
                binding.fabRecord.setImageResource(android.R.drawable.ic_media_play)
                Toast.makeText(this, "Видео сохранено в папку Movies", Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onResume() {
        super.onResume()
        startBackgroundThread()
        if (binding.textureView.isAvailable) {
            openCamera()
        } else {
            binding.textureView.surfaceTextureListener = surfaceTextureListener
        }
    }

    override fun onPause() {
        if (isRecording) {
            stopRecording()
        }
        captureSession?.close()
        captureSession = null
        cameraDevice?.close()
        cameraDevice = null
        rawImageReader?.close()
        rawImageReader = null
        stopBackgroundThread()
        super.onPause()
    }
}
