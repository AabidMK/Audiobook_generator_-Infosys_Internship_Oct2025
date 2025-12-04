import os
import pytesseract
from pdf2image import convert_from_path
from docx import Document
from PIL import Image
import tempfile
import PyPDF2

# Update with your installed tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(file_path):
    text = ""

    # Try normal text extraction first
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except:
        pass

    if text.strip():
        return text  # Found real text, no need for OCR

    # OCR fallback for scanned PDFs
    images = convert_from_path(file_path)
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"

    return text


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def extract_text_from_image(file_path):
    img = Image.open(file_path)
    return pytesseract.image_to_string(img)


def extract_text_generic(uploaded_file):
    # Save uploaded file temporarily
    suffix = uploaded_file.name.split('.')[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix='.' + suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    ext = suffix.lower()
    if ext == "pdf":
        return extract_text_from_pdf(tmp_path)
    elif ext == "docx":
        return extract_text_from_docx(tmp_path)
    elif ext in ["png", "jpg", "jpeg"]:
        return extract_text_from_image(tmp_path)
    elif ext == "txt":
        with open(tmp_path, "r", encoding="utf-8") as file:
            return file.read()

    return ""
