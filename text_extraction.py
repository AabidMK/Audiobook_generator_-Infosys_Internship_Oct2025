import fitz  # PyMuPDF
import docx
import os
import sys
import pytesseract
from PIL import Image

# Function to extract text from image (with Tesseract path specification)
def extract_text_from_image(image_path):
    try:
        # Specify Tesseract path if not in PATH (update this to your actual path)
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows example
        # For macOS/Linux, use something like: '/usr/local/bin/tesseract' or '/usr/bin/tesseract'
        
        # Open the image using PIL
        img = Image.open(image_path)
        # Use pytesseract to extract text
        text = pytesseract.pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

# Function to extract text from PDF, DOCX, TXT, or image files (enhanced version)
def extract_text(file_path: str) -> str:
    """
    Extract text from PDF, DOCX, TXT, or image files.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: The file '{file_path}' was not found.")

    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()
    text = ""

    try:
        # PDF extraction
        if file_extension == '.pdf':
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text("text")

        # DOCX extraction
        elif file_extension == '.docx':
            document = docx.Document(file_path)
            text = "\n".join(para.text for para in document.paragraphs)

        # TXT extraction (if needed, though not in original)
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

        # Image extraction using OCR
        elif file_extension in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']:
            text = extract_text_from_image(file_path)
            if text is None:
                raise EnvironmentError("Failed to extract text from image.")

        else:
            raise ValueError(
                f"Unsupported file type '{file_extension}'.\n"
                "Supported types: .pdf, .docx, .txt, .png, .jpg, .jpeg, .bmp, .tiff, .webp"
            )

    except Exception as e:
        print(f"❌ Error while processing '{file_path}': {e}")
        return ""

    return text.strip()

# Function to save text to a TXT file
def save_text_to_file(text: str, output_path: str):
    """
    Save extracted text to a .txt file.
    """
    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ Extracted text saved to '{output_path}'")
    except IOError as e:
        print(f"❌ Error saving text file: {e}")

# Function to extract and save
def extract_and_save(input_file: str):
    """
    Extract text from input_file (PDF, DOCX, TXT, or image) and save it to a .txt file.
    """
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_extracted.txt"

    print(f"🔍 Extracting text from: {input_file}")
    text = extract_text(input_file)

    if text:
        save_text_to_file(text, output_file)
    else:
        print("⚠️ No text extracted (file may be empty or unreadable).")

    return output_file

# Main function for command-line usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>")
        print("Supported formats: PDF, DOCX, TXT, PNG, JPG, JPEG, BMP, TIFF, WEBP")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.isfile(file_path):
        print("File not found.")
        sys.exit(1)
    
    # Extract and save
    extract_and_save(file_path)
