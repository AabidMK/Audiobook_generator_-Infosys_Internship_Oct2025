from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Optional

from PIL import Image
import pytesseract
import platform
import os

# Optional deps
try:
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover - optional
    pdfplumber = None

try:
    from pdf2image import convert_from_path  # type: ignore
except Exception:  # pragma: no cover - optional
    convert_from_path = None

try:
    import docx  # python-docx
except Exception:  # pragma: no cover - optional
    docx = None

from utils import ensure_dirs, write_text_file, file_stem


class OCRDependencyMissing(RuntimeError):
    """Raised when system OCR dependencies like Tesseract are missing."""
    pass


def _maybe_configure_tesseract() -> None:
    """On Windows, try to auto-configure Tesseract path if not found.

    Respects env var TESSERACT_CMD if set. Otherwise, tries common install paths.
    """
    # If user set an explicit path, honor it
    tcmd_env = os.getenv("TESSERACT_CMD") or os.getenv("TESSERACT_PATH")
    if tcmd_env and os.path.exists(tcmd_env):
        pytesseract.pytesseract.tesseract_cmd = tcmd_env  # type: ignore[attr-defined]
        return

    if platform.system().lower().startswith("win"):
        candidates = [
            r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        ]
        for c in candidates:
            if os.path.exists(c):
                pytesseract.pytesseract.tesseract_cmd = c  # type: ignore[attr-defined]
                break


_maybe_configure_tesseract()


# Windows note: set Tesseract path if needed
# Example (uncomment if pytesseract can't find tesseract.exe):
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"


def extract_text(path: str | Path, ocr_if_needed: bool = True) -> str:
    """Extract text from files: .txt, .pdf, .docx, images.

    For PDFs: tries pdfplumber text first; if none and ocr_if_needed, OCR pages via pdf2image+pytesseract.
    For images: OCR via PIL+pytesseract.
    """
    ensure_dirs()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    ext = p.suffix.lower()

    if ext in {".txt"}:
        return p.read_text(encoding="utf-8", errors="ignore")

    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}:
        img = Image.open(p)
        try:
            return pytesseract.image_to_string(img)
        except Exception as e:
            msg = str(e)
            if "TesseractNotFoundError" in msg or "tesseract is not installed" in msg.lower():
                raise OCRDependencyMissing(
                    "Tesseract OCR not found. Install Tesseract and ensure it's on PATH, "
                    "or set TESSERACT_CMD to the full path of tesseract.exe."
                ) from e
            raise

    if ext == ".pdf":
        text = ""
        if pdfplumber is not None:
            try:
                with pdfplumber.open(p) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        if page_text.strip():
                            text += page_text + "\n"
            except Exception:
                # ignore and try OCR if allowed
                pass
        if text.strip():
            return text
        if ocr_if_needed and convert_from_path is not None:
            try:
                # Allow specifying Poppler path via env var if needed
                poppler_path = os.getenv("POPPLER_PATH")
                if poppler_path and os.path.isdir(poppler_path):
                    images = convert_from_path(str(p), poppler_path=poppler_path)
                else:
                    images = convert_from_path(str(p))
            except Exception:
                images = []
            ocr_text_parts = []
            for img in images:
                try:
                    ocr_text_parts.append(pytesseract.image_to_string(img))
                except Exception as e:
                    msg = str(e)
                    if "TesseractNotFoundError" in msg or "tesseract is not installed" in msg.lower():
                        raise OCRDependencyMissing(
                            "Tesseract OCR not found for PDF OCR. Install Tesseract and set PATH or TESSERACT_CMD."
                        ) from e
                    # Skip page on other errors
            return "\n".join(ocr_text_parts)
        # If we reach here, we couldn't extract
        return text

    if ext in {".docx"} and docx is not None:
        try:
            document = docx.Document(str(p))
            return "\n".join(para.text for para in document.paragraphs)
        except Exception:
            return ""

    # Unknown type
    return ""


def extract_and_save(path: str | Path, output_dir: Optional[Path] = None) -> Path:
    text = extract_text(path)
    base = file_stem(path)
    out = write_text_file(text, basename=base, folder=output_dir)
    return out


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extractor.py <file_path>")
        raise SystemExit(2)
    in_path = sys.argv[1]
    out_path = extract_and_save(in_path)
    print(f"Saved: {out_path}")
