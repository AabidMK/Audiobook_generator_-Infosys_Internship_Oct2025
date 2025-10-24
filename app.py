import streamlit as st
import pdfplumber
from docx import Document

st.title("AI Audiobook Generator")

uploaded_files = st.file_uploader(
    "Upload your document(s)", 
    type=["pdf", "docx", "txt"], 
    accept_multiple_files=True
)

def extract_text(file):
    if file.type == "application/pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return file.read().decode("utf-8", errors="ignore")

if uploaded_files:
    for file in uploaded_files:
        text = extract_text(file)
        st.write(f"### Extracted Text from {file.name}")
        st.text_area("Content", text)
