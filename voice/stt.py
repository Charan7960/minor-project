import os
import sys
import tempfile
import wave
import pyaudio
import whisper

# Load Whisper model once (small model — fast and accurate enough)
print("[STT] Loading Whisper model...")
model = whisper.load_model("base")
print("[STT] Whisper model ready.")


def record_audio(duration: int = 5, sample_rate: int = 16000) -> str:
    """
    Record audio from microphone for given duration.
    Returns path to the saved .wav file.
    """
    chunk = 1024
    fmt   = pyaudio.paInt16
    channels = 1

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=fmt,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk
    )

    print(f"[STT] Recording for {duration} seconds... Speak now.")
    frames = []
    for _ in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print("[STT] Recording done.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save to temp wav file
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wf = wave.open(tmp.name, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(audio.get_sample_size(fmt))
    wf.setframerate(sample_rate)
    wf.writeframes(b"".join(frames))
    wf.close()

    return tmp.name


def transcribe(audio_path: str) -> str:
    """
    Transcribe audio file to text using Whisper.
    Returns the transcribed text string.
    """
    print("[STT] Transcribing audio...")
    result = model.transcribe(audio_path, language="en")
    text = result["text"].strip()
    print(f"[STT] Transcribed: {text}")

    # Clean up temp file
    try:
        os.remove(audio_path)
    except Exception:
        pass

    return text


def listen(duration: int = 5) -> str:
    """
    Full pipeline — record mic then transcribe.
    Returns transcribed text.
    """
    audio_path = record_audio(duration=duration)
    return transcribe(audio_path)


if __name__ == "__main__":
    print("=== Testing stt.py ===")
    print("Speak a sentence after the prompt.\n")
    text = listen(duration=5)
    print(f"\nYou said: {text}")
