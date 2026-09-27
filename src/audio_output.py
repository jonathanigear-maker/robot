"""
audio_output.py

Central audio-output utilities for the robot.

This module currently has two main jobs:

1. Play WAV files through the Raspberry Pi speaker.
2. Analyse outgoing audio and send an amplitude value to the Arduino
   so the robot's mouth LEDs can react to speech.

The important design idea is that the source of the audio should not
need to know how the mouth works.

For example:

    WAV file --------\
                      \
    OpenAI audio ------> audio_output.py ---> Arduino mouth level
                      /
    Future TTS -------/

This means the RMS calculation, scaling and Arduino communication only
need to exist in one place.
"""

import threading

import numpy as np
import soundfile as sf
import sounddevice as sd

from src import arduino_comms


# ---------------------------------------------------------------------
# AUDIO / MOUTH SETTINGS
# ---------------------------------------------------------------------

# Number of audio samples processed at a time when playing WAV files.
#
# At 24 kHz, 1024 samples represents about 43 milliseconds of audio,
# giving roughly 23 mouth updates per second.
CHUNK_SIZE = 1024


# Multiplier used to convert normalised audio RMS values into the
# 0-255 range expected by the Arduino.
#
# Typical float audio values are much smaller than 1.0, so simply
# multiplying RMS by 255 would usually produce very small mouth values.
#
# 1000 worked as a useful starting point during testing. This can be
# tuned later without changing any of the audio sources.
MOUTH_SCALE = 1000


# Maximum value understood by the Arduino mouth animation.
MOUTH_MAX = 255


# ---------------------------------------------------------------------
# MOUTH LEVEL FUNCTIONS
# ---------------------------------------------------------------------

def update_mouth(audio):
    """
    Calculate the amplitude of float32 audio and update the mouth.

    'audio' should be a NumPy array containing normalised audio samples,
    normally in approximately the range:

        -1.0 to +1.0

    This is the format used by sounddevice and by WAV files loaded as
    float32.

    The RMS (Root Mean Square) value gives us a useful measurement of
    the overall loudness of the audio chunk.

    The RMS value is then scaled into the 0-255 range used by the
    Arduino mouth animation.
    """

    # There is nothing useful to calculate if the audio block is empty.
    if len(audio) == 0:
        return

    # Calculate Root Mean Square amplitude.
    #
    # Squaring removes negative values, mean gives the average energy,
    # and square root converts it back into an amplitude measurement.
    rms = np.sqrt(np.mean(audio ** 2))

    # Convert the small floating-point RMS value into a useful mouth
    # animation value.
    mouth_level = int(rms * MOUTH_SCALE)

    # Never send more than the Arduino's maximum value.
    mouth_level = min(MOUTH_MAX, mouth_level)

    # Send the resulting level using our existing persistent Arduino
    # communications connection.
    arduino_comms.send_mouth_level(mouth_level)


def update_mouth_pcm16(audio_bytes):
    """
    Update the mouth from raw signed 16-bit PCM audio.

    This is primarily intended for streaming audio sources such as
    OpenAI Realtime.

    OpenAI gives us raw PCM16 bytes rather than the normalised float32
    NumPy arrays used by play_wav().

    This function converts those PCM16 bytes into the same float format
    used by update_mouth(), then passes them through the SAME mouth
    amplitude calculation.

    Therefore WAV playback and OpenAI speech share exactly the same
    RMS calculation and mouth scaling.
    """

    if not audio_bytes:
        return

    # Interpret the raw bytes as little-endian signed 16-bit samples.
    audio = np.frombuffer(
        audio_bytes,
        dtype="<i2",
    )

    # Convert integer PCM16:
    #
    #     -32768 ... +32767
    #
    # into normalised float audio:
    #
    #     approximately -1.0 ... +1.0
    #
    audio = audio.astype(np.float32) / 32768.0

    # Use exactly the same RMS/mouth calculation as every other
    # float32 audio source.
    update_mouth(audio)


def mouth_off():
    """
    Explicitly turn the mouth LEDs off.

    Audio sources should call this when speech finishes so the mouth
    cannot remain illuminated at the level of the final audio chunk.
    """

    arduino_comms.send_mouth_level(0)


# ---------------------------------------------------------------------
# WAV PLAYBACK
# ---------------------------------------------------------------------

def play_wav(filename):
    """
    Play a WAV file and animate the robot's mouth from its amplitude.

    The WAV is loaded as float32 audio and divided into small chunks.

    For every chunk we:

        1. Calculate/update the mouth level.
        2. Send the audio chunk to the speaker.

    Processing the audio in chunks allows the mouth level to change
    continuously throughout the spoken response rather than simply
    switching on for the entire WAV.
    """

    # Load the WAV as normalised float32 audio.
    data, sample_rate = sf.read(
        filename,
        dtype="float32",
    )

    # If the WAV is stereo (or otherwise multi-channel), combine the
    # channels into mono.
    #
    # The robot currently has one speech output channel and the mouth
    # only needs one amplitude value.
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    try:

        # Open the Raspberry Pi audio output at the WAV file's native
        # sample rate.
        with sd.OutputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        ) as stream:

            # Work through the WAV in small blocks.
            for start in range(0, len(data), CHUNK_SIZE):

                chunk = data[start:start + CHUNK_SIZE]

                # Calculate the speech amplitude and send the resulting
                # mouth level to the Arduino.
                update_mouth(chunk)

                # Play this block of audio.
                #
                # reshape(-1, 1) gives sounddevice the expected
                # frames x channels layout for our mono stream.
                stream.write(chunk.reshape(-1, 1))

    finally:

        # Always turn the mouth off when playback finishes.
        #
        # Using finally is important because this also happens if audio
        # playback stops because of an exception.
        mouth_off()


def play_wav_async(filename):
    """
    Play a WAV file in a background thread.

    play_wav() itself blocks until the sound has finished.

    This wrapper allows the rest of the robot program to continue
    running while the WAV is playing.

    The returned Thread can be waited for using:

        thread.join()

    This is currently used by voice_feedback.py.
    """

    thread = threading.Thread(
        target=play_wav,
        args=(filename,),
        daemon=True,
    )

    thread.start()

    return thread

# ---------------------------------------------------------------------
# STREAMING AUDIO OUTPUT
# ---------------------------------------------------------------------

import subprocess


# The OpenAI voice stream currently uses 16 kHz signed 16-bit mono PCM.
STREAM_SAMPLE_RATE = 16000

# Volume applied to streaming AI speech.
# Keep this at the same value currently used in openai_realtime.py.
STREAM_VOLUME = 2.5

_stream_speaker = None
_stream_output_thread = None

def start_stream():
    """
    Start the streaming audio output used for live speech.

    This creates a persistent SOX process.

    Raw PCM16 audio can then be passed to write_stream() in small
    chunks. SOX receives those chunks, applies the robot voice effect,
    and sends the result to the Raspberry Pi audio output.

    Keeping this here means audio_output.py, rather than OpenAI itself,
    owns the physical audio playback path.
    """

    global _stream_speaker, _stream_output_thread
    
    # Do nothing if the streaming speaker is already running.
    if _stream_speaker is not None:
        return

    _stream_speaker = subprocess.Popen(
        [
            "sox",

            # Input: raw PCM16 from OpenAI.
            "-t", "raw",
            "-r", str(STREAM_SAMPLE_RATE),
            "-e", "signed-integer",
            "-b", "16",
            "-c", "1",
            "-",

            # Output: processed raw PCM16 back to Python.
            "-t", "raw",
            "-r", str(STREAM_SAMPLE_RATE),
            "-e", "signed-integer",
            "-b", "16",
            "-c", "1",
            "-",

            # Robot voice processing.
            "pitch", "900",
            "vol", str(STREAM_VOLUME),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    # Start a background thread which reads the processed audio
    # coming back from SOX, drives the mouth, and plays the audio.
    _stream_output_thread = threading.Thread(
        target=_stream_output_worker,
        daemon=True,
    )

    _stream_output_thread.start()

def write_stream(audio_bytes):
    """
    Send a chunk of PCM16 audio into the live SOX processor.

    If the stream is shutting down, simply ignore any late audio
    chunks that arrive.
    """

    if _stream_speaker is None:
        return

    if _stream_speaker.stdin is None:
        return

    if _stream_speaker.stdin.closed:
        return

    try:
        _stream_speaker.stdin.write(audio_bytes)
        _stream_speaker.stdin.flush()

    except (ValueError, BrokenPipeError):
        # The stream was closed while this chunk was arriving.
        # This is normal during shutdown.
        return

def _stream_output_worker():
    """
    Read pitch-processed audio coming back from SOX.

    Each chunk is:
        1. Converted to float32.
        2. Used to calculate the robot's mouth level.
        3. Sent to the speaker.

    Because sounddevice controls the final playback, the mouth update
    should now closely match the audio actually being heard.
    """

    # 1024 PCM16 samples = 2048 bytes.
    bytes_per_chunk = CHUNK_SIZE * 2

    with sd.OutputStream(
        samplerate=STREAM_SAMPLE_RATE,
        channels=1,
        dtype="float32",
    ) as output_stream:

        while _stream_speaker is not None:

            audio_bytes = _stream_speaker.stdout.read(bytes_per_chunk)

            if not audio_bytes:
                break

            # Convert SOX's PCM16 output into normalised float32.
            audio = np.frombuffer(
                audio_bytes,
                dtype="<i2"
            ).astype(np.float32) / 32768.0

            # Move the mouth according to this exact audio chunk.
            update_mouth(audio)

            # Play this exact audio chunk.
            output_stream.write(
                audio.reshape(-1, 1)
            )

    # Make absolutely sure the mouth is off when playback stops.
    mouth_off()



def stop_stream():
    """
    Stop the live speech output cleanly.

    This closes SOX's input, waits for the output worker to finish,
    terminates SOX if necessary, and makes sure the mouth LEDs are off.
    """

    global _stream_speaker, _stream_output_thread

    if _stream_speaker is None:
        mouth_off()
        return

    # Tell SOX there will be no more audio.
    if _stream_speaker.stdin is not None:
        try:
            _stream_speaker.stdin.close()
        except Exception:
            pass

    # Allow the output worker to finish reading any audio
    # still coming from SOX.
    if _stream_output_thread is not None:
        _stream_output_thread.join(timeout=2.0)

    # Make sure SOX has stopped.
    if _stream_speaker.poll() is None:
        _stream_speaker.terminate()

        try:
            _stream_speaker.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            _stream_speaker.kill()

    _stream_speaker = None
    _stream_output_thread = None

    # Always leave the mouth off.
    mouth_off()