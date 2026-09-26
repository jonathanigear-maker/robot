from kokoro_onnx import Kokoro
import kokoro_onnx
import onnxruntime as rt
import soundfile as sf
import time

THREADS = 1

print(f"Loading Kokoro ONNX with {THREADS} threads...")

options = rt.SessionOptions()
options.intra_op_num_threads = THREADS
options.inter_op_num_threads = 1

session = rt.InferenceSession(
    "/home/sodigece/robot/models/kokoro/kokoro-v1.0.int8.onnx",
    sess_options=options,
    providers=["CPUExecutionProvider"]
)

kokoro = Kokoro.__new__(Kokoro)

kokoro._setup(
    session=session,
    model_path="/home/sodigece/robot/models/kokoro/kokoro-v1.0.int8.onnx",
    voices_path="/home/sodigece/robot/models/kokoro/voices-v1.0.bin",
    espeak_config=None,
    vocab_config=None
)

print("Kokoro ONNX ready.")

while True:
    text = input("Say: ")

    if text.lower() in ["quit", "exit"]:
        break

    start = time.time()

    samples, sample_rate = kokoro.create(
        text,
        voice="bm_fable",
        speed=1.0,
        lang="en-gb"
    )

    elapsed = time.time() - start

    sf.write("spenser_onnx.wav", samples, sample_rate)

    print(f"Generated in {elapsed:.2f} seconds")