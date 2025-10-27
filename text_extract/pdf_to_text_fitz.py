import os
import fitz
from docx import Document

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF."""
    text = ""
    with fitz.open(pdf_path) as pdf_doc:
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc.load_page(page_num)
            text += page.get_text("text") + "\n"
    return text.strip()

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()

def extract_text_from_txt(txt_path):
    with open(txt_path, "r", encoding="utf-8") as file:
        return file.read().strip()

def save_text_to_file(text, output_path, format="txt"):
    if format not in ["txt", "md"]:
        raise ValueError("Output format must be 'txt' or 'md'")
    with open(f"{output_path}.{format}", "w", encoding="utf-8") as file:
        file.write(text)
    print(f"Extracted text saved to {output_path}.{format}")

def extract_and_save(input_path, output_format="txt"):
    ext = os.path.splitext(input_path)[1].lower()
    
    if ext == ".pdf":
        text = extract_text_from_pdf(input_path)
    elif ext == ".docx":
        text = extract_text_from_docx(input_path)
    elif ext == ".txt":
        text = extract_text_from_txt(input_path)
    else:
        raise ValueError("Unsupported file format. Supported: PDF, DOCX, TXT")

    output_path = os.path.splitext(input_path)[0]
    save_text_to_file(text, output_path, output_format)


if __name__ == "__main__":
    input_file = "maulik1.pdf"
    extract_and_save(input_file, output_format="txt")
