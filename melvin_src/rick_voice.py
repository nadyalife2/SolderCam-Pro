import os
import io
import time
import random
import subprocess
import wave
from pathlib import Path

BASE_DIR = Path("/melvin")
if not BASE_DIR.exists():
    BASE_DIR = Path("/sdcard/melvin")
if not BASE_DIR.exists():
    BASE_DIR = Path(".")

BURP_FALLBACK = BASE_DIR / "burp.mp3"
TMP_DIR = Path("/tmp")

class RickVoiceEngine:
    def __init__(self):
        self.burp_pcm = None
        self._load_burps()

    def _load_burps(self):
        """Конвертируем burp.mp3 в чистый raw PCM 22050 Hz 16-bit mono."""
        if BURP_FALLBACK.exists():
            try:
                p = subprocess.Popen(
                    ["sox", str(BURP_FALLBACK), "-t", "raw", "-r", "22050", "-c", "1", "-b", "16", "-e", "signed-integer", "-"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )
                raw_data, _ = p.communicate()
                if raw_data and len(raw_data) > 100:
                    self.burp_pcm = raw_data
                    print(f"[RickVoice] Burp raw PCM cached in RAM ({len(raw_data)} bytes)")
            except Exception as e:
                print(f"[RickVoice] Burp load notice: {e}")

    def synthesize_to_memory(self, text: str, persona: str = "rick") -> io.BytesIO:
        """
        Четкий синтез речи через espeak-ng + чистый SoX DSP.
        Без каши, без обрезания фраз, без сломанных заголовков WAV.
        """
        clean_text = text.replace("*рыгает*", "").replace("*отрыжка*", "").strip()
        if not clean_text:
            clean_text = "Что?"

        ts = int(time.time() * 1000)
        raw_wav = str(TMP_DIR / f"raw_{ts}.wav")
        pitched_raw = str(TMP_DIR / f"pitched_{ts}.raw")

        try:
            # 1. espeak-ng с четким голосом ru+m3
            speed = "146" if persona == "rick" else "152"
            pitch_native = "38" if persona == "rick" else "45"
            
            cmd_tts = [
                "espeak-ng",
                "-v", "ru+m3",
                "-s", speed,
                "-a", "100",
                "-p", pitch_native,
                "-w", raw_wav,
                clean_text
            ]
            subprocess.run(cmd_tts, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 2. SoX DSP: умеренный сдвиг тона (pitch -140), подъем баса +3dB, экспорт в чистый RAW PCM
            pitch_shift = "-140" if persona == "rick" else "-70"
            cmd_sox = [
                "sox",
                "-v", "0.95",
                raw_wav,
                "-t", "raw",
                "-r", "22050",
                "-c", "1",
                "-b", "16",
                "-e", "signed-integer",
                pitched_raw,
                "pitch", pitch_shift,
                "bass", "+3", "120"
            ]
            subprocess.run(cmd_sox, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            with open(pitched_raw, "rb") as f:
                speech_pcm = f.read()

            # 3. Сборка единого валидного WAV с правильным RIFF-заголовком
            out_pcm = speech_pcm
            if persona == "rick" and self.burp_pcm and random.random() < 0.35:
                silence = b"\x00" * 6615  # ~0.15s тишины
                out_pcm = self.burp_pcm + silence + speech_pcm

            bio = io.BytesIO()
            with wave.open(bio, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                wf.writeframes(out_pcm)

            bio.seek(0)
            return bio

        except Exception as e:
            print(f"[RickVoice] DSP error: {e}")
            bio = io.BytesIO()
            with wave.open(bio, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                wf.writeframes(b"\x00" * 2205)
            bio.seek(0)
            return bio

        finally:
            for tmp_file in [raw_wav, pitched_raw]:
                if os.path.exists(tmp_file):
                    try:
                        os.remove(tmp_file)
                    except OSError:
                        pass

# Глобальный экземпляр
voice_engine = RickVoiceEngine()
