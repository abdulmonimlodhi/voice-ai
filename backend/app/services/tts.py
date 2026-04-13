# backend/app/services/tts.py
from gtts import gTTS
import tempfile

def text_to_speech(text: str) -> bytes:
    try:
        if not text or not text.strip():
            return b""

        tts = gTTS(text=text, lang="en")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        tts.save(tmp_path)

        with open(tmp_path, "rb") as f:
            audio = f.read()

        return audio

    except Exception as e:
        print("TTS Error:", e)
        return b""