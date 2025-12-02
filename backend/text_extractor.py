import os
import io
import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import pytesseract
import re

def extract_text_from_pdf(file_bytes: bytes, use_ocr: bool = True, lang: str = "eng") -> str:
    """
    Extract text from a PDF file (supports OCR fallback for scanned PDFs).
    """
    text = []
    try:
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num, page in enumerate(pdf, start=1):
            page_text = page.get_text("text").strip()

            # Use OCR fallback if no selectable text
            if use_ocr and not page_text:
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # better DPI
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img, lang=lang, config="--oem 1 --psm 6")
                    page_text = ocr_text.strip()
                    print(f"[OCR] Page {page_num}: Recovered text via Tesseract.")
                except Exception as e:
                    print(f"[OCR] Failed on page {page_num}: {e}")

            text.append(page_text)
        pdf.close()
    except Exception as e:
        print(f"[Error] Failed to extract text from PDF: {e}")
        return ""

    # Normalize spacing between pages
    return "\n\n".join([t for t in text if t]).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from a DOCX file using python-docx.
    """
    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs).strip()
    except Exception as e:
        print(f"[Error] Failed to extract text from DOCX: {e}")
        return ""


def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Extract plain text from a TXT file (UTF-8 assumed).
    """
    try:
        return file_bytes.decode("utf-8", errors="ignore").strip()
    except Exception as e:
        print(f"[Error] Failed to decode TXT: {e}")
        return ""


def extract_text_from_file(filename: str, file_bytes: bytes, **kwargs) -> str:
    """
    Automatically detect file type and extract text accordingly.
    Supports .pdf, .docx, .txt
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes, **kwargs)
    elif ext == ".docx":
        return extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        return extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def split_text(text: str, chunk_size: int = 2000) -> list[str]:
    """
    Split text into approximate chunks, avoiding mid-sentence cuts.
    """
    if not text:
        return []

    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        # Prefer breaking at sentence end
        match = re.search(r"[.!?]\s", text[start:end][::-1])
        if match:
            end = start + end - match.start()
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    return chunks
