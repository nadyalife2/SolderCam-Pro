import re
import sys

TARGET_FILE = r"d:\для one plus nord n10\melvin_src\agent_orchestrator.py"

with open(TARGET_FILE, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update speakWithLowPitch and executeVoiceOutput
old_audio_block_start = "function playBurpSound() {"
old_audio_block_end = "// ========================================================\n        // 100% HANDS-FREE CONTINUOUS MICROPHONE LISTENER"

new_audio_block = """function playBurpSound() {
            try {
                burpAudio.currentTime = 0;
                const p = burpAudio.play();
                if (p !== undefined) p.catch(e => console.log('Burp notice:', e));
            } catch(e) {
                console.log('Burp audio catch:', e);
            }
        }

        function speakWithLowPitch(text) {
            let raw = text.trim();
            if (!raw) return;

            isBotSpeaking = true;
            speechBuffer = [];
            preRollQueue = [];
            silenceCount = 0;
            maxRmsInPhrase = 0;

            vadIndicator.classList.remove('recording', 'dialogue-active');
            vadText.textContent = (currentPersona === 'rick') ? 'РИК ГОВОРИТ...' : 'МЕЛВИН ГОВОРИТ...';

            const isRick = (currentPersona === 'rick');
            const hasBurp = isRick || /\\*рыгает\\*|\\*отрыжка\\*/i.test(raw);
            const cleanText = raw.replace(/\\*рыгает\\*|\\*отрыжка\\*/gi, '').trim();

            if (hasBurp) {
                playBurpSound();
                // Реплика начинается сразу после отрыжки (~550 мс)
                setTimeout(() => {
                    executeVoiceOutput(cleanText);
                }, 550);
            } else {
                executeVoiceOutput(cleanText);
            }
        }

        function executeVoiceOutput(spoken) {
            const isRick = (currentPersona === 'rick');
            // Естественные, разборчивые и низкие настройки для Google TTS
            const targetPitch = isRick ? 0.88 : 0.80;
            const targetRate = isRick ? 1.06 : 0.94;

            if (window.MelvinNativeBridge) {
                try {
                    if (typeof window.MelvinNativeBridge.setPitch === 'function') {
                        window.MelvinNativeBridge.setPitch(targetPitch);
                    }
                    if (typeof window.MelvinNativeBridge.setSpeechRate === 'function') {
                        window.MelvinNativeBridge.setSpeechRate(targetRate);
                    } else if (typeof window.MelvinNativeBridge.setRate === 'function') {
                        window.MelvinNativeBridge.setRate(targetRate);
                    }
                } catch(e) {
                    console.log('Bridge config error:', e);
                }
            }

            const words = spoken.trim().split(/\\s+/).filter(Boolean);
            const speechDurationMs = Math.max(1600, Math.round(words.length * 420 + 900));

            // Приоритет 1: Нативный мост приложения (Google Text-to-Speech на Android)
            // Мгновенный отклик (0 мс), чистый русский голос, никакой каши и тормозов
            if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.speak === 'function') {
                try {
                    window.MelvinNativeBridge.speak(spoken);
                    setTimeout(onBotSpeechFinished, speechDurationMs);
                    return;
                } catch(e) {
                    console.log('Native bridge speak notice:', e);
                }
            }

            // Приоритет 2: Web Speech API (встроенный синтез браузера / WebView)
            if ('speechSynthesis' in window) {
                try {
                    window.speechSynthesis.cancel();
                    const utter = new SpeechSynthesisUtterance(spoken);
                    utter.lang = 'ru-RU';
                    utter.rate = targetRate;
                    utter.pitch = targetPitch;

                    const voices = window.speechSynthesis.getVoices();
                    const ruMale = voices.find(v => v.lang.startsWith('ru') && (
                        v.name.includes('Male') || v.name.includes('Yuri') || v.name.includes('Pavel') ||
                        v.name.includes('Dmitry') || v.name.includes('Alexander')
                    )) || voices.find(v => v.lang.startsWith('ru'));
                    if (ruMale) utter.voice = ruMale;

                    utter.onend = onBotSpeechFinished;
                    utter.onerror = (e) => {
                        console.log('SpeechSynthesis error:', e);
                        onBotSpeechFinished();
                    };
                    window.speechSynthesis.speak(utter);
                    return;
                } catch(e) {
                    console.log('SpeechSynthesis notice:', e);
                }
            }

            // Приоритет 3: Серверный DSP-аудиопоток (/api/tts) при отсутствии Google TTS
            const ttsUrl = '/api/tts?text=' + encodeURIComponent(spoken) + '&persona=' + encodeURIComponent(currentPersona);
            const neuralAudio = new Audio(ttsUrl);
            neuralAudio.onended = onBotSpeechFinished;
            neuralAudio.onerror = () => {
                setTimeout(onBotSpeechFinished, speechDurationMs);
            };
            neuralAudio.play().catch(() => {
                setTimeout(onBotSpeechFinished, speechDurationMs);
            });
        }

        """

p1 = code.find(old_audio_block_start)
p2 = code.find(old_audio_block_end)
if p1 != -1 and p2 != -1:
    code = code[:p1] + new_audio_block + code[p2:]
    print("Audio playback block patched successfully!")
else:
    print(f"Error finding audio block: p1={p1}, p2={p2}")
    sys.exit(1)

# 2. Update Microphone Listener & Resampler & STT
old_stt_block_start = "function encodeWAV(samples, sampleRate) {"
old_stt_block_end = "// Start hands-free listener on load"

new_stt_block = """// Качественный антиалиасинг-ресемплер (48000/44100 Гц -> 16000 Гц)
        function resampleTo16k(audioBuffer, fromSampleRate) {
            if (!audioBuffer || audioBuffer.length === 0) return new Float32Array(0);
            if (fromSampleRate === 16000) return audioBuffer;

            const ratio = fromSampleRate / 16000;
            const newLength = Math.round(audioBuffer.length / ratio);
            const result = new Float32Array(newLength);
            let offsetResult = 0;
            let offsetBuffer = 0;

            while (offsetResult < result.length) {
                const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
                let accum = 0;
                let count = 0;
                for (let i = offsetBuffer; i < nextOffsetBuffer && i < audioBuffer.length; i++) {
                    accum += audioBuffer[i];
                    count++;
                }
                result[offsetResult] = count > 0 ? (accum / count) : audioBuffer[offsetBuffer];
                offsetResult++;
                offsetBuffer = nextOffsetBuffer;
            }
            return result;
        }

        function encodeWAV(samples, sampleRate) {
            const buffer = new ArrayBuffer(44 + samples.length * 2);
            const view = new DataView(buffer);

            function writeString(offset, string) {
                for (let i = 0; i < string.length; i++) {
                    view.setUint8(offset + i, string.charCodeAt(i));
                }
            }

            writeString(0, 'RIFF');
            view.setUint32(4, 36 + samples.length * 2, true);
            writeString(8, 'WAVE');
            writeString(12, 'fmt ');
            view.setUint32(16, 16, true);
            view.setUint16(20, 1, true); // PCM
            view.setUint16(22, 1, true); // Mono
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, sampleRate * 2, true);
            view.setUint16(32, 2, true);
            view.setUint16(34, 16, true);
            writeString(36, 'data');
            view.setUint32(40, samples.length * 2, true);

            let offset = 44;
            for (let i = 0; i < samples.length; i++, offset += 2) {
                const s = Math.max(-1, Math.min(1, samples[i]));
                view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            }
            return new Blob([buffer], { type: 'audio/wav' });
        }

        let audioStream = null;
        let audioContext = null;
        let isCapturingSpeech = false;
        let speechBuffer = [];
        let silenceCount = 0;
        let maxRmsInPhrase = 0;
        const PRE_ROLL_CHUNKS = 3; // ~750ms pre-speech audio buffer
        let preRollQueue = [];
        let isTranscribing = false;
        let isSendingChat = false;

        async function initHandsFreeWakeWord() {
            try {
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    vadText.textContent = 'МИКРОФОН НЕДОСТУПЕН';
                    return;
                }

                audioStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

                // Создаем контекст без принудительного sampleRate (берем аппаратную частоту устройства)
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const source = audioContext.createMediaStreamSource(audioStream);
                const processor = audioContext.createScriptProcessor(4096, 1, 1);
                
                // Маршрут через gain=0 во избежание акустической петли
                const zeroGain = audioContext.createGain();
                zeroGain.gain.value = 0;

                source.connect(processor);
                processor.connect(zeroGain);
                zeroGain.connect(audioContext.destination);

                processor.onaudioprocess = (e) => {
                    if (isBotSpeaking || isTranscribing || isSendingChat) {
                        speechBuffer = [];
                        silenceCount = 0;
                        maxRmsInPhrase = 0;
                        return;
                    }

                    const inputData = e.inputBuffer.getChannelData(0);
                    let sum = 0;
                    for (let i = 0; i < inputData.length; i++) {
                        sum += inputData[i] * inputData[i];
                    }
                    const rms = Math.sqrt(sum / inputData.length);

                    const isDialogueActive = Date.now() < dialogueActiveUntil;
                    // Оптимальные пороги VAD: 0.016 в ожидании, 0.012 в активном диалоге
                    const currentThreshold = isDialogueActive ? 0.012 : 0.016;

                    if (rms > currentThreshold) {
                        silenceCount = 0;
                        if (!isCapturingSpeech) {
                            isCapturingSpeech = true;
                            speechBuffer = [];
                            maxRmsInPhrase = rms;
                            for (let p of preRollQueue) {
                                speechBuffer.push(p);
                            }
                            vadIndicator.classList.add('recording');
                            vadText.textContent = isDialogueActive ? 'СЛУШАЮ КОМАНДУ...' : 'ЗАПИСЬ РЕЧИ...';
                        } else {
                            if (rms > maxRmsInPhrase) maxRmsInPhrase = rms;
                        }
                    } else if (isCapturingSpeech) {
                        silenceCount++;
                    } else {
                        preRollQueue.push(new Float32Array(inputData));
                        if (preRollQueue.length > PRE_ROLL_CHUNKS) {
                            preRollQueue.shift();
                        }
                    }

                    if (isCapturingSpeech) {
                        speechBuffer.push(new Float32Array(inputData));

                        // Завершение реплики: 7 чанков тишины (~1.7s) либо макс 28 чанков (~7s)
                        if (silenceCount >= 7 || speechBuffer.length >= 28) {
                            isCapturingSpeech = false;
                            vadIndicator.classList.remove('recording');

                            const captured = speechBuffer;
                            speechBuffer = [];
                            preRollQueue = [];
                            const peak = maxRmsInPhrase;
                            maxRmsInPhrase = 0;

                            // Минимум 3 чанка (~0.7s) и пик RMS >= 0.018
                            if (captured.length >= 3 && peak >= 0.018) {
                                vadText.textContent = 'РАСПОЗНАВАНИЕ...';

                                let totalLen = 0;
                                for (let b of captured) totalLen += b.length;
                                const flat = new Float32Array(totalLen);
                                let off = 0;
                                for (let b of captured) {
                                    flat.set(b, off);
                                    off += b.length;
                                }

                                processSpeechChunk(flat, isDialogueActive);
                            } else {
                                console.log('[Hands-Free] Discarded noise/too short:', captured.length, 'chunks, peak RMS:', peak);
                                if (isDialogueActive) {
                                    vadIndicator.classList.add('dialogue-active');
                                    vadText.textContent = 'ДИАЛОГ: ГОВОРИТЕ...';
                                } else {
                                    vadIndicator.classList.remove('dialogue-active');
                                    vadText.textContent = 'СЛУШАЮ: "МЕЛВИН / РИК"';
                                }
                            }
                        }
                    } else {
                        if (isDialogueActive) {
                            vadIndicator.classList.add('dialogue-active');
                            vadText.textContent = 'ДИАЛОГ: ГОВОРИТЕ...';
                        } else {
                            vadIndicator.classList.remove('dialogue-active');
                            vadText.textContent = 'СЛУШАЮ: "МЕЛВИН / РИК"';
                        }
                    }
                };

                vadText.textContent = 'СЛУШАЮ: "МЕЛВИН / РИК"';
                console.log('[Hands-Free] Mic listener running continuously!');
            } catch(e) {
                console.log('[Hands-Free] Mic init error:', e);
                vadText.textContent = 'ОШИБКА МИКРОФОНА';
            }
        }

        async function processSpeechChunk(samples, wasDialogueActive) {
            if (isTranscribing) return;
            isTranscribing = true;
            try {
                // Преобразование аппаратной частоты (48/44.1 кГц) в точные 16000 Гц
                const hardwareRate = (audioContext && audioContext.sampleRate) ? audioContext.sampleRate : 48000;
                const resampled = resampleTo16k(samples, hardwareRate);
                const wavBlob = encodeWAV(resampled, 16000);

                const res = await fetch('/transcribe_audio', {
                    method: 'POST',
                    body: wavBlob
                });
                const data = await res.json();

                if (data.status === 'ok' && data.text) {
                    const text = data.text.trim();
                    const lower = text.toLowerCase();
                    console.log('[Hands-Free] Recognized:', text, '| InDialogue:', wasDialogueActive);

                    const isWakeHail = lower.includes('мелвин') || lower.includes('мэлвин') || lower.includes('melvin') ||
                                      lower.includes('рик') || lower.includes('rick');

                    if (isWakeHail || wasDialogueActive || isWaitingForCommand) {
                        if (lower.includes('стоп') || lower.includes('хватит') || lower.includes('отмена') || lower.includes('заткнись')) {
                            dialogueActiveUntil = 0;
                            isWaitingForCommand = false;
                            appendMsg('user', text);
                            appendMsg('bot', 'Диалог завершен. Слушаю оклик.');
                            vadIndicator.classList.remove('dialogue-active');
                            vadText.textContent = 'СЛУШАЮ: "МЕЛВИН / РИК"';
                            return;
                        }

                        dialogueActiveUntil = Date.now() + 25000;

                        if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                            window.MelvinNativeBridge.vibrate(40);
                        }
                        send(text);
                    } else {
                        console.log('[Hands-Free] Ignored speech outside dialogue (not wake-word):', text);
                        if (wasDialogueActive) {
                            vadIndicator.classList.add('dialogue-active');
                            vadText.textContent = 'ДИАЛОГ: ГОВОРИТЕ...';
                        } else {
                            vadIndicator.classList.remove('dialogue-active');
                            vadText.textContent = 'СЛУШАЮ: "МЕЛВИН / РИК"';
                        }
                    }
                } else {
                    console.log('[Hands-Free] STT result:', data.status);
                    if (wasDialogueActive) {
                        vadIndicator.classList.add('dialogue-active');
                        vadText.textContent = 'ДИАЛОГ: ГОВОРИТЕ...';
                    } else {
                        vadIndicator.classList.remove('dialogue-active');
                        vadText.textContent = 'СЛУШАЮ: "МЕЛВИН / РИК"';
                    }
                }
            } catch(e) {
                console.log('[Hands-Free] STT error:', e);
            } finally {
                isTranscribing = false;
            }
        }

        """

p3 = code.find(old_stt_block_start)
p4 = code.find(old_stt_block_end)
if p3 != -1 and p4 != -1:
    code = code[:p3] + new_stt_block + code[p4:]
    print("STT and Resampler block patched successfully!")
else:
    print(f"Error finding STT block: p3={p3}, p4={p4}")
    sys.exit(1)

# 3. Fix debug file path in transcribe_audio
code = code.replace(
    'with open("/sdcard/melvin/last_stt_debug.wav", "wb") as f_dbg:',
    'debug_wav = "/melvin/last_stt_debug.wav" if os.path.exists("/melvin") else "/sdcard/melvin/last_stt_debug.wav"\n            with open(debug_wav, "wb") as f_dbg:'
)

with open(TARGET_FILE, "w", encoding="utf-8") as f:
    f.write(code)

print("All patches applied cleanly to agent_orchestrator.py!")
