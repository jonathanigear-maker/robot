from kokoro import KPipeline
import soundfile as sf
import time

print("Loading Kokoro...")
pipeline = KPipeline(lang_code='b')
print("Kokoro ready.")

while True:
    text = input("Say: ")

    if text.lower() in ["quit", "exit"]:
        break

    start = time.time()

    generator = pipeline(
        text,
        voice='bm_fable',
        speed=1.0
    )

    for i, (gs, ps, audio) in enumerate(generator):
        sf.write("spenser.wav", audio, 24000)

    elapsed = time.time() - start

    print(f"Generated in {elapsed:.2f} seconds")