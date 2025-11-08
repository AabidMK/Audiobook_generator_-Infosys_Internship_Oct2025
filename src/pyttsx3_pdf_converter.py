import fitz  # pymupdf
from pyttsx3_generator import PyTTSX3Generator
import os

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pymupdf"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        
        doc.close()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def main():
    pdf_path = "../input_files/audiobook.pdf"
    output_path = "../output_files/audiobook.mp3"
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Extract text from PDF using pymupdf
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("No text extracted from PDF")
        return
    
    print(f"Extracted {len(text)} characters from PDF")
    
    # Generate audio
    print("Generating audio...")
    tts_generator = PyTTSX3Generator()
    success = tts_generator.generate_audio(text, output_path)
    
    if success:
        print("Audiobook generation completed successfully!")
    else:
        print("Audiobook generation failed!")

if __name__ == "__main__":
    main()