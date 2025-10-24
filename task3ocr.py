import fitz  # PyMuPDF
from docx import Document
import pdfplumber
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image
import io
import os


def extract_text_from_pdf(file_path, use_plumber=False, use_ocr=False):
    """Extract text from PDF using PyMuPDF, pdfplumber, or OCR"""
    text = ""

    if use_plumber:
        # 🧾 pdfplumber for text-based PDFs (especially with tables)
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                elif use_ocr:  # fallback if no text found
                    img = page.to_image(resolution=300).original
                    ocr_text = pytesseract.image_to_string(img)
                    text += ocr_text
    else:
        # ⚙️ PyMuPDF for regular PDFs
        with fitz.open(file_path) as doc:
            for page in doc:
                page_text = page.get_text("text")
                if page_text.strip():
                    text += page_text
                elif use_ocr: 
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img)
                    text += ocr_text

    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX using python-docx"""
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_txt(file_path):
    """Extract text directly from TXT"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def save_text(output_text, input_file, output_format="txt"):
    """Save extracted text as .txt or .md"""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_name}_extracted.{output_format}"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_text)
    print(f"✅ Text saved as: {output_file}")

def extract_text(file_path, output_format="txt", for_tables=False, use_ocr=False):
    """Main extraction function that detects file type"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path, use_plumber=for_tables, use_ocr=use_ocr)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    elif ext == ".txt":
        text = extract_text_from_txt(file_path)
    else:
        raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")

    save_text(text, file_path, output_format)
    return text

if __name__ == "__main__":
    file_path = input("Enter file path (PDF/DOCX/TXT): ").strip()
    output_format = input("Output format (txt/md): ").strip().lower() or "txt"
    for_tables = input("Does the PDF contain tables? (y/n): ").lower().startswith("y")
    use_ocr = input("Enable OCR for scanned/image PDFs? (y/n): ").lower().startswith("y")

    extract_text(file_path, output_format, for_tables, use_ocr)
