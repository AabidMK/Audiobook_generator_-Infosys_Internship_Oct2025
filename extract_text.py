import os
import pdfplumber
from docx import Document

# --- Functions to extract text from each type of file ---

def extract_pdf(file_path):
    """Extract text from a PDF file."""
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
    """Extract text from a Word (.docx) file."""
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        return f"Error reading DOCX {file_path}: {e}"
    return text

def extract_txt(file_path):
    """Extract text from a text (.txt) file."""
    text = ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return f"Error reading TXT {file_path}: {e}"
    return text

# --- Main function ---
def main():
    folder_path = os.getcwd()  # Current folder
    print(f"Current folder: {folder_path}\n")

    # List all files in the folder
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        # Skip directories
        if os.path.isdir(file_path):
            continue

        # PDF files
        if file_name.lower().endswith(".pdf"):
            print(f"--- Extracting from PDF: {file_name} ---")
            extracted = extract_pdf(file_path)
            output_file = os.path.join(folder_path, file_name.replace(".pdf", "_output.txt"))
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(extracted)
            print(f"Saved PDF text to: {output_file}\n")

        # DOCX files
        elif file_name.lower().endswith(".docx"):
            print(f"--- Extracting from DOCX: {file_name} ---")
            extracted = extract_docx(file_path)
            output_file = os.path.join(folder_path, file_name.replace(".docx", "_output.txt"))
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(extracted)
            print(f"Saved DOCX text to: {output_file}\n")

        # TXT files
        elif file_name.lower().endswith(".txt"):
            print(f"--- Extracting from TXT: {file_name} ---")
            extracted = extract_txt(file_path)
            output_file = os.path.join(folder_path, file_name.replace(".txt", "_output_extracted.txt"))
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(extracted)
            print(f"Saved TXT text to: {output_file}\n")

# --- Run main ---
if __name__ == "__main__":
    main()
