import subprocess
import os
import time

BIN = "/opt/sherpa/sherpa-onnx-v1.10.30-linux-aarch64-static/bin/sherpa-onnx-offline-tts"
MODEL = "/opt/sherpa/vits-piper-ru_RU-dmitri-medium/ru_RU-dmitri-medium.onnx"
TOKENS = "/opt/sherpa/vits-piper-ru_RU-dmitri-medium/tokens.txt"
DATA = "/opt/sherpa/vits-piper-ru_RU-dmitri-medium/espeak-ng-data"
OUT = "/sdcard/melvin/rick_voice_test.wav"
PITCHED = "/sdcard/melvin/rick_voice_pitched.wav"

cmd = [
    BIN,
    f"--vits-model={MODEL}",
    f"--vits-tokens={TOKENS}",
    f"--vits-data-dir={DATA}",
    f"--output-filename={OUT}",
    "--num-threads=1",
    "--provider=cpu",
    "Привет Морти"
]

print("Executing Sherpa-ONNX test...")
t0 = time.time()
env = os.environ.copy()
env["OMP_NUM_THREADS"] = "1"
p = subprocess.run(cmd, capture_output=True, text=True, env=env)
t1 = time.time()

print("Exit code:", p.returncode)
print("Stdout:", p.stdout)
print("Stderr:", p.stderr)
print(f"Elapsed: {round(t1 - t0, 3)}s")

if os.path.exists(OUT):
    print("WAV created successfully, size:", os.path.getsize(OUT))
    # Run SoX DSP
    sox_cmd = ["sox", OUT, PITCHED, "pitch", "-480", "bass", "+5", "120", "tempo", "1.04"]
    subprocess.run(sox_cmd, check=True)
    print("Pitched WAV created, size:", os.path.getsize(PITCHED))
