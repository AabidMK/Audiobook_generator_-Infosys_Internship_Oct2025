import os
import fitz  
from docx2python import docx2python 
from PIL import Image              
import pytesseract                 


class TextExtractor:
    """
    A unified module for extracting text from PDF, DOCX, TXT, and JPG/image files.
    """
    def __init__(self):
        
        pass

    def _extract_pdf(self, file_path):
        """Extracts text from a digital PDF using PyMuPDF."""
        text = ""
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    
                    text += page.get_text("text") + "\n\n"
            return text.strip()
        except Exception as e:
            
            return f"Error extracting digital PDF {file_path}: {e}"

    def _extract_docx(self, file_path):
        """Extracts text from a DOCX file using docx2python."""
        try:
        
            with docx2python(file_path, html=False) as docx_content:
      
                return docx_content.text.strip()
        except Exception as e:
            return f"Error extracting DOCX {file_path}: {e}"

    def _extract_txt(self, file_path):
        """Extracts text from a TXT/MD file using native Python."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            return f"Error extracting TXT/MD {file_path}: {e}"

    def _extract_image_ocr(self, file_path):
        """Extracts text from an image (JPG/PNG) using Tesseract OCR."""
        try:
  
            text = pytesseract.image_to_string(Image.open(file_path))
            return text.strip()
        except Exception as e:
            return f"Error performing OCR on image {file_path}. Is Tesseract installed and configured? Error: {e}"

    def extract_text(self, file_path):
        """
        Main function to determine file type and extract text.
        """
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
            
        extension = os.path.splitext(file_path)[1].lower()

        if extension == '.pdf':
            return self._extract_pdf(file_path)
        elif extension == '.docx':
            return self._extract_docx(file_path)
        elif extension in ['.txt', '.md']:
            return self._extract_txt(file_path)
        elif extension in ['.jpg', '.jpeg', '.png']:
            return self._extract_image_ocr(file_path)
        else:
            return f"Unsupported file type: {extension}"
            
    def save_text(self, text_content, base_file_name, output_format='txt'):
        """
        Saves the extracted text to a .txt or .md file.
        """
        if output_format not in ['txt', 'md']:
            raise ValueError("Output format must be 'txt' ")

        output_path = f"{base_file_name}_extracted_text.{output_format}"
        
        try:
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            return f" Successfully saved extracted text to: {output_path}"
        except Exception as e:
            return f" Error saving file: {e}"

if __name__ == '__main__':
    
    input_files = [
        "Sample 1.docx",
        "Sample 2.pdf",
        "sample 3.txt",
        "sample 4.jpg"
        
    ]

    OUTPUT_FORMAT = 'txt' 

    extractor = TextExtractor()

    print("--- Starting Text Extraction Module ---")
    print(f"Output Format: .{OUTPUT_FORMAT}\n")

    for file_name in input_files:
        print(f"Processing: {file_name}...")

        extracted_text = extractor.extract_text(file_name)
        base_name = os.path.splitext(file_name)[0]
        
        if extracted_text and not extracted_text.startswith(('Error', 'File not found')):
           
            save_result = extractor.save_text(extracted_text, base_name, OUTPUT_FORMAT)
            print(save_result)
        else:
            print(f"Extraction Failed/Skipped for {file_name}: {extracted_text}")
            
    print("\n--- Extraction Complete ---")

