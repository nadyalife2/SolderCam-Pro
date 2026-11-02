import subprocess
import os
import time

TEXT = "Слушай сюда, Морти, я говорю с тобой прямо из процессора."
RAW = "/tmp/test_espeak_raw.wav"
FINAL = "/tmp/test_rick_final.wav"

t0 = time.time()
# 1. espeak-ng synthesis
cmd_espeak = ["espeak-ng", "-v", "ru", "-s", "140", "-w", RAW, TEXT]
subprocess.run(cmd_espeak, check=True)
t1 = time.time()

# 2. sox pitch shift & bass
cmd_sox = ["sox", RAW, FINAL, "pitch", "-520", "bass", "+6", "120", "tempo", "1.02"]
subprocess.run(cmd_sox, check=True)
t2 = time.time()

print(f"espeak-ng: {round(t1 - t0, 3)}s, sox: {round(t2 - t1, 3)}s, total: {round(t2 - t0, 3)}s")
print(f"Final file size: {os.path.getsize(FINAL)} bytes")
