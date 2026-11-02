import rick_voice
import time

t0 = time.time()
bio = rick_voice.voice_engine.synthesize_to_memory("Слушай сюда, Морти, я проверил генерацию звука!")
t1 = time.time()
data = bio.getvalue()
print(f"Generated WAV in {round(t1 - t0, 3)}s, length: {len(data)} bytes")
with open("/sdcard/melvin/test_final_rick.wav", "wb") as f:
    f.write(data)
print("Saved to /sdcard/melvin/test_final_rick.wav")
