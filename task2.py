import fitz  
from docx import Document
import os

def extract_text_from_pdf(file_path):
    """Extract text from PDF using PyMuPDF"""
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text("text")
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

def extract_text(file_path, output_format="txt"):
    """Main extraction function that detects file type"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
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

    extract_text(file_path, output_format)
