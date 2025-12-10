"""
AI AUDIOBOOK GENERATOR (PIPELINE)
--------------------------------------
1️⃣ Extracts text from document (PDF, DOCX, TXT, IMAGE)
2️⃣ Enhances it via Gemini LLM into natural audiobook narration
3️⃣ Converts it into realistic speech using Coqui TTS

Author: Swati's Project
"""

import logging
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Force CPU mode
import re
import textwrap
import time
from pathlib import Path
from typing import Callable, Dict, Optional

import PyPDF2
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
import google.generativeai as genai
from TTS.api import TTS
from dotenv import load_dotenv

# ------------------------------------------------------------
# INITIAL SETUP
# ------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# -------------------------
# MODULE 1: DOCUMENT PARSER
# -------------------------
class DocumentParser:
    def __init__(self):
        self.SUPPORTED_FORMATS: Dict[str, Callable[[Path], str]] = {
            ".pdf": self._extract_pdf,
            ".docx": self._extract_docx,
            ".txt": self._extract_txt,
            ".png": self._extract_image,
            ".jpg": self._extract_image,
            ".jpeg": self._extract_image,
        }

    def parse(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            logging.error(f"File does not exist: {path}")
            return ""

        ext = path.suffix.lower()
        extractor = self.SUPPORTED_FORMATS.get(ext)
        if extractor is None:
            logging.error(f"Unsupported file extension: {ext}")
            return ""

        logging.info(f"📄 Extracting text from: {path.name}")
        start = time.time()
        try:
            text = extractor(path)
        except Exception as e:
            logging.error(f"❌ Extraction error: {e}")
            text = ""
        duration = time.time() - start
        logging.info(f"✅ Extraction completed in {duration:.2f}s ({len(text)} chars).")
        return text.strip()

    def _extract_pdf(self, path: Path) -> str:
        try:
            text_parts = []
            with path.open("rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts).strip()
        except Exception as e:
            logging.warning(f"PyPDF2 failed: {e}, using pdfplumber...")
            with pdfplumber.open(str(path)) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages]).strip()

    def _extract_docx(self, path: Path) -> str:
        doc = Document(str(path))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    def _extract_txt(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").strip()

    def _extract_image(self, path: Path) -> str:
        img = Image.open(path)
        return pytesseract.image_to_string(img).strip()


# -------------------------
# MODULE 2: TEXT ENRICHMENT
# -------------------------
class TextEnrichment:
    def __init__(self, model_name="gemini-flash-latest"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("❌ GOOGLE_API_KEY not found in environment.")
        genai.configure(api_key=api_key)
        self.model_name = model_name

    def clean_enriched_text(self, text: str) -> str:
        text = text.replace("’", "'").replace("“", '"').replace("”", '"').replace("—", "-")
        text = re.sub(r"[*_/\\#^~<>|]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        lines = [line.strip() for line in text.splitlines() if len(line.strip().split()) > 3]
        return " ".join(lines)

    def enrich_text(self, input_text: str) -> str:
        system_prompt = (
            "You are an audiobook narration expert. "
            "Rewrite the text to sound engaging, listener-friendly, and natural for narration. "
            "Preserve meaning but enhance tone, rhythm, and flow."
        )
        prompt = f"{system_prompt}\n\nText to enrich:\n{input_text}"

        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt, generation_config={"temperature": 0.7})
            enriched = self.clean_enriched_text(response.text.strip())
            logging.info("✅ Enrichment successful.")
            return enriched
        except Exception as e:
            logging.error(f"❌ Gemini enrichment failed: {e}")
            return ""

    def process_text(self, text: str, output_path="enriched_output.txt") -> Optional[Path]:
        if not text.strip():
            logging.warning("⚠️ No text to enrich.")
            return None

        chunks = textwrap.wrap(text, 2000)
        enriched_chunks = []
        for i, chunk in enumerate(chunks, 1):
            logging.info(f"✨ Enriching chunk {i}/{len(chunks)}...")
            enriched_chunk = self.enrich_text(chunk)
            if enriched_chunk:
                enriched_chunks.append(enriched_chunk)

        if not enriched_chunks:
            logging.error("No enriched text generated.")
            return None

        enriched_text = "\n\n".join(enriched_chunks)
        output = Path(output_path)
        output.write_text(enriched_text, encoding="utf-8")
        logging.info(f"✅ Enriched text saved at: {output}")
        return output


# -------------------------
# MODULE 3: TEXT TO SPEECH
# -------------------------
class TextToSpeech:
    def __init__(self, model_name="tts_models/en/ljspeech/tacotron2-DDC"):
        logging.info(f"🔊 Loading TTS model: {model_name}")
        self.tts = TTS(model_name)

    def convert_text_to_audio(self, text: str, output_path="audiobook_output.wav"):
        if not text.strip():
            logging.error("❌ Empty text for TTS.")
            return None
        try:
            logging.info(f"🎙️ Generating speech ({len(text)} chars)...")
            self.tts.tts_to_file(text=text, file_path=output_path)
            logging.info(f"✅ Audio saved at: {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"❌ TTS failed: {e}")
            return None


# -------------------------
# MAIN PIPELINE
# -------------------------
if __name__ == "__main__":
    logging.info("🚀 Starting Audiobook Generation Pipeline...")

    file_path = input("Enter the path of your document (PDF/DOCX/TXT/IMAGE): ").strip().strip('"')

    parser = DocumentParser()
    extracted_text = parser.parse(file_path)
    if not extracted_text:
        logging.error("❌ No text extracted. Exiting.")
        exit()

    extracted_path = Path("extracted_output.txt")
    extracted_path.write_text(extracted_text, encoding="utf-8")

    enricher = TextEnrichment()
    enriched_path = enricher.process_text(extracted_text, "enriched_output.txt")
    if not enriched_path:
        logging.error("❌ Enrichment failed. Exiting.")
        exit()

    tts = TextToSpeech()
    enriched_text = Path(enriched_path).read_text(encoding="utf-8")
    tts.convert_text_to_audio(enriched_text, "audiobook_output.wav")

    logging.info("🎉 FULL PIPELINE COMPLETE! Audiobook generated successfully.")