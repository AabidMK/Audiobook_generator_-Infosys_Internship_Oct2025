from PyPDF2 import PdfReader
import docx

def extract_text_from_pdf(path):
    """Extract text from a PDF file."""
    text = []
    reader = PdfReader(path)
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text)

def extract_text_from_docx(path):
    """Extract text from a DOCX file."""
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_txt(path):
    """Extract text from a TXT file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_text(file_path):
    """Automatically detect file type and extract text."""
    lower = file_path.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif lower.endswith(".docx"):
        return extract_text_from_docx(file_path)
    elif lower.endswith(".txt"):
        return extract_text_from_txt(file_path)
    else:
        return "ERROR: Unsupported file type. Only PDF, DOCX, TXT allowed."
