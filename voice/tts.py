from gtts import gTTS
import os
import tempfile
import platform
import subprocess
import time


def speak(text: str, language: str = "en") -> None:
    """
    Convert text to speech and play it using gTTS.
    Works on Windows, Mac, and Linux.
    """
    print(f"[TTS] Generating speech for: {text[:50]}...")
    
    # Create temp file for audio
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    
    try:
        # Generate speech using gTTS
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(tmp.name)
        print(f"[TTS] Audio saved to: {tmp.name}")
        
        # Play the audio based on OS
        if platform.system() == "Windows":
            os.startfile(tmp.name)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["afplay", tmp.name])
        else:  # Linux
            subprocess.run(["mpv", tmp.name])
        
        print("[TTS] Playing audio...")
        time.sleep(5)  # Wait 5 seconds for audio to play
        
    except Exception as e:
        print(f"[TTS] Error: {e}")
    finally:
        # Clean up temp file
        try:
            os.remove(tmp.name)
        except:
            pass


if __name__ == "__main__":
    print("=== Testing tts.py ===\n")
    
    test_sentences = [
        "Hello, this is a test of the text to speech system.",
        "Your order has been successfully cancelled.",
        "Your refund has been approved and will arrive in 5 to 7 business days.",
    ]
    
    for sentence in test_sentences:
        print(f"\nSpeaking: {sentence}")
        speak(sentence)
        print("Done.\n")
    
    print("[tts] All tests completed.")