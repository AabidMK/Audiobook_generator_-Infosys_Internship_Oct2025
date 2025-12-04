
import os
import sys
import pdfplumber
import pytesseract
from PIL import Image
import docx

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    with pdfplumber.open(file_path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages)

def extract_text_from_image(file_path):
    """Extracts text from an image file."""
    return pytesseract.image_to_string(Image.open(file_path))

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    doc = docx.Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs)

def extract_text_from_txt(file_path):
    """Reads a plain text file."""
    with open(file_path, 'r') as f:
        return f.read()

def main():
    """Main function to handle file processing."""
    if len(sys.argv) != 2:
        print("Usage: python extractor.py <path_to_file>")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"Error: File not found at {input_path}")
        sys.exit(1)

    _, file_extension = os.path.splitext(input_path)
    filename = os.path.basename(input_path)
    output_filename = os.path.splitext(filename)[0] + ".txt"
    output_path = os.path.join("extracted_text", output_filename)

    extracted_text = ""
    if file_extension.lower() == ".pdf":
        extracted_text = extract_text_from_pdf(input_path)
    elif file_extension.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        extracted_text = extract_text_from_image(input_path)
    elif file_extension.lower() == ".docx":
        extracted_text = extract_text_from_docx(input_path)
    elif file_extension.lower() == ".txt":
        extracted_text = extract_text_from_txt(input_path)
    else:
        print(f"Error: Unsupported file type: {file_extension}")
        sys.exit(1)

    with open(output_path, "w") as f:
        f.write(extracted_text)

    print(f"Successfully extracted text to: {output_path}")

if __name__ == "__main__":
    main()
