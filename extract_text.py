import os
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract

# --- Set path to tesseract executable (adjust if installed elsewhere) ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Functions to extract text from each type of file ---
def extract_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return f"Error reading PDF {file_path}: {e}"
    return text

def extract_docx(file_path):
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        return f"Error reading DOCX {file_path}: {e}"
    return text

def extract_txt(file_path):
    text = ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return f"Error reading TXT {file_path}: {e}"
    return text

def extract_image(file_path):
    text = ""
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
    except Exception as e:
        return f"Error reading image {file_path}: {e}"
    return text

# --- Main function ---
def main():
    folder_path = os.getcwd()
    print(f"Current folder: {folder_path}\n")

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isdir(file_path):
            continue

        # PDF
        if file_name.lower().endswith(".pdf"):
            extracted = extract_pdf(file_path)
            out_file = file_name.replace(".pdf", "_output.txt")
        # DOCX
        elif file_name.lower().endswith(".docx"):
            extracted = extract_docx(file_path)
            out_file = file_name.replace(".docx", "_output.txt")
        # TXT
        elif file_name.lower().endswith(".txt"):
            extracted = extract_txt(file_path)
            out_file = file_name.replace(".txt", "_output_extracted.txt")
        # Images (png, jpg, jpeg)
        elif file_name.lower().endswith((".png", ".jpg", ".jpeg")):
            extracted = extract_image(file_path)
            out_file = file_name.rsplit(".",1)[0] + "_image_text.txt"
        else:
            continue

        with open(os.path.join(folder_path, out_file), "w", encoding="utf-8") as f:
            f.write(extracted)
        print(f"✅ Extracted text saved to: {out_file}")

if __name__ == "__main__":
    main()
