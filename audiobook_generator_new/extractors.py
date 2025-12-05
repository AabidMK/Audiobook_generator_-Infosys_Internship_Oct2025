import PyPDF2, io
from docx import Document

def extract_text_from_pdf_fileobj(fileobj):
    # fileobj: file-like (BytesIO or UploadedFile)
    reader = PyPDF2.PdfReader(fileobj)
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or '')
    return '\n'.join(texts)

def extract_text_from_docx_fileobj(fileobj):
    # fileobj might be a SpooledTemporaryFile or BytesIO; python-docx expects a path or file-like binary
    fileobj.seek(0)
    doc = Document(fileobj)
    texts = [p.text for p in doc.paragraphs]
    return '\n'.join(texts)

def extract_text_from_txt_fileobj(fileobj):
    fileobj.seek(0)
    raw = fileobj.read()
    if isinstance(raw, bytes):
        return raw.decode('utf-8', errors='ignore')
    return raw

def extract_text_from_file(uploaded_file):
    # uploaded_file is Streamlit uploaded file with .type and .name and read()
    uploaded_file.seek(0)
    name = uploaded_file.name.lower()
    if name.endswith('.pdf'):
        return extract_text_from_pdf_fileobj(uploaded_file)
    elif name.endswith('.docx'):
        return extract_text_from_docx_fileobj(uploaded_file)
    elif name.endswith('.txt'):
        return extract_text_from_txt_fileobj(uploaded_file)
    else:
        return ''
