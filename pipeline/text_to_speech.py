"""
MODULE 4 - Text-to-Speech (Audiobook Narration)
-----------------------------------------------
Converts enriched text into natural-sounding speech using Coqui TTS.

Input  : enriched_output.txt
Output : audiobook_output.wav
"""

import logging
import re
from pathlib import Path
from TTS.api import TTS  # pip install TTS

# -------------------------
# Logging Setup
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# -------------------------
# Text Cleaning Helper
# -------------------------
def clean_text(text: str) -> str:
    """
    Cleans text to avoid unsupported characters for TTS models.
    - Removes symbols (*, /, —, etc.)
    - Replaces fancy quotes with normal ones
    - Collapses multiple spaces
    """
    # Normalize quotes and dashes
    text = text.replace("’", "'").replace("“", '"').replace("”", '"').replace("—", "-")
    # Remove unsupported symbols (anything not alphanumeric, punctuation, or space)
    text = re.sub(r"[^a-zA-Z0-9.,!?;:'\"()\-\s]", " ", text)
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

class TextToSpeech:
    def __init__(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
        """
        Initialize the TTS model.
        Default: English female voice (LJSpeech)
        Other voices: use `TTS.list_models()` to see available models.
        """
        logging.info(f"Loading TTS model: {model_name}")
        self.tts = TTS(model_name)

    def convert_text_to_audio(self, text: str, output_path: str = "audiobook_output.wav"):
        """
        Convert the input text to speech and save it to output_path.
        """
        if not text.strip():
            logging.error("❌ Empty text provided for TTS conversion.")
            return False

        try:
            logging.info(f"🎙️ Generating speech for {len(text)} characters...")
            self.tts.tts_to_file(text=text, file_path=output_path)
            logging.info(f"✅ Audio saved successfully at: {output_path}")
            return True
        except Exception as e:
            logging.error(f"❌ TTS generation failed: {e}")
            return False

    def process_file(self, input_path: str, output_path: str = "audiobook_output.wav"):
        """
        Reads enriched text file and generates an audio narration.
        """
        path = Path(input_path)
        if not path.exists():
            logging.error(f"Input text file not found: {path}")
            return

        logging.info(f"🎧 Reading enriched text from {path.name}...")
        text = path.read_text(encoding="utf-8").strip()
        return self.convert_text_to_audio(text, output_path)


# -------------------------
# Automatic Run
# -------------------------
if __name__ == "__main__":
    input_file = r"C:\Users\SWATI\OneDrive\Desktop\AIaudioBook\enriched_output.txt"
    output_audio = r"C:\Users\SWATI\OneDrive\Desktop\AIaudioBook\audiobook_output.wav"

    tts_module = TextToSpeech()
    tts_module.process_file(input_file, output_audio)
    logging.info("🎉 TTS conversion complete!")
