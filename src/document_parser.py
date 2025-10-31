# MODULE 2 - * Extracts raw text from PDFs, DOCX, and TXT files
#            * Extracts text, OCR (Optical Character Recognition) for image files (like .png, .jpg, .jpeg)
#             Libraries used: pytesseract — Python wrapper for Google’s Tesseract OCR engine
#                             Pillow (PIL) — to open and preprocess image files    
"""-----------------------------------------------------------------------------------------------------------"""        

import logging
import time
from pathlib import Path
from typing import Callable, Dict, Optional

import PyPDF2
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract

# Configure Tesseract path (Windows only)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class DocumentParser:
    def __init__(self):
        # map extensions to extractor callables
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

        logging.info(f"Extracting from: {path.name}")
        start = time.time()
        try:
            text = extractor(path)
        except Exception as e:
            logging.error(f"Extractor threw an error: {e}")
            text = ""
        duration = time.time() - start
        if text:
            logging.info(f"Extraction successful ({len(text)} chars) in {duration:.2f}s")
        else:
            logging.warning("No text extracted.")
        return text

    def save(self, text: str, output_path: str, fmt: str = "txt") -> Optional[Path]:
        fmt = fmt.lower()
        if fmt not in ("txt", "md"):
            fmt = "txt"

        out = Path(f"{output_path}.{fmt}")
        try:
            out.write_text(text, encoding="utf-8")
            logging.info(f"Saved extracted text to {out}")
            return out
        except Exception as e:
            logging.error(f"Failed to save file: {e}")
            return None

    # PDF
    def _extract_pdf(self, path: Path) -> str:
        text_parts = []
        try:
            with path.open("rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            extracted = "\n".join(text_parts).strip()
            if extracted:
                return extracted
        except Exception as e:
            logging.warning(f"PyPDF2 failed: {e}, using pdfplumber.")

        try:
            text_parts = []
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts).strip()
        except Exception as e:
            logging.error(f"pdfplumber failed: {e}")
            return ""

    # DOCX
    def _extract_docx(self, path: Path) -> str:
        try:
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs).strip()
        except Exception as e:
            logging.error(f"DOCX extraction failed: {e}")
            return ""

    # TXT
    def _extract_txt(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8").strip()
        except Exception as e:
            logging.error(f"TXT read failed: {e}")
            return ""

    # OCR Image extraction
    def _extract_image(self, path: Path) -> str:
        """
        Extract text from image using pytesseract.
        Supports: .png, .jpg, .jpeg
        """
        try:
            img = Image.open(path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            logging.error(f"OCR extraction failed: {e}")
            return ""


if __name__ == "__main__":
    file_path = input("Enter the path of your document (PDF/DOCX/TXT/IMAGE): ").strip().strip('"')
    parser = DocumentParser()
    extracted_text = parser.parse(file_path)

    if extracted_text:
        parser.save(extracted_text, "extracted_output", fmt="txt")
    else:
        logging.info("No output generated from parse().")
