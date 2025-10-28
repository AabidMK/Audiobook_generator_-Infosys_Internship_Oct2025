import os
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

input_folder = "input_files"
output_folder = "output_files"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def extract_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception:
        pass
    if not text.strip():
        print(f"Falling back to OCR for: {os.path.basename(file_path)}")
        pages = convert_from_path(file_path)
        for page_image in pages:
            text += pytesseract.image_to_string(page_image)
    return text

def extract_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_image(file_path):
    img = Image.open(file_path)
    return pytesseract.image_to_string(img)

def save_text(filename, text):
    name, _ = os.path.splitext(filename)
    output_path = os.path.join(output_folder, f"{name}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text.strip())
    print(f"Saved extracted text to: {output_path}")

def process_files():
    for filename in os.listdir(input_folder):
        path = os.path.join(input_folder, filename)
        if not os.path.isfile(path):
            continue

        ext = filename.lower().split(".")[-1]
        if ext == "pdf":
            text = extract_pdf(path)
        elif ext == "docx":
            text = extract_docx(path)
        elif ext == "txt":
            text = extract_txt(path)
        elif ext in ["jpg", "jpeg", "png"]:
            text = extract_image(path)
        else:
            print(f"Skipped unsupported file: {filename}")
            continue

        save_text(filename, text)

if __name__ == "__main__":
    process_files()
