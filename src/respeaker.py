import queue
import threading

import sounddevice as sd


DEVICE = 0
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024


_stream = None
_running = False
_worker_thread = None

_audio_queue = queue.Queue()
_consumers = []


def add_consumer(callback):
    """
    Register something that wants microphone audio.

    callback will receive:
        callback(audio, sample_rate)
    """
    _consumers.append(callback)


def remove_consumer(callback):
    if callback in _consumers:
        _consumers.remove(callback)


def _audio_callback(indata, frames, time_info, status):
    """
    Called by sounddevice whenever a new block of audio arrives.

    Keep this FAST. Just copy the audio and put it on the queue.
    """

    if status:
        print(f"RESPEAKER: {status}")

    audio = indata[:, 0].copy()

    _audio_queue.put(audio)


def _audio_worker():
    """
    Runs in a background thread.

    Takes audio from the queue and sends it to anything
    registered as a consumer.
    """

    while _running:

        try:
            audio = _audio_queue.get(timeout=0.1)

        except queue.Empty:
            continue

        for consumer in list(_consumers):

            try:
                consumer(audio, SAMPLE_RATE)

            except Exception as e:
                print(f"RESPEAKER CONSUMER ERROR: {e}")


def start():
    """Open the ReSpeaker and start capturing audio."""

    global _stream, _running, _worker_thread

    if _running:
        return

    print("RESPEAKER: Opening microphone...")

    _running = True

    _worker_thread = threading.Thread(
        target=_audio_worker,
        daemon=True,
    )

    _worker_thread.start()

    _stream = sd.InputStream(
        device=DEVICE,
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=BLOCK_SIZE,
        callback=_audio_callback,
    )

    _stream.start()

    print("RESPEAKER: Listening.")


def stop():
    """Stop capturing audio and release the ReSpeaker."""

    global _stream, _running

    _running = False

    if _stream is not None:
        _stream.stop()
        _stream.close()
        _stream = None

    print("RESPEAKER: Closed.")