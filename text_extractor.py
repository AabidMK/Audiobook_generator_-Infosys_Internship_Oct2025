"""
Text Extractor Module
Extracts text from PDF, DOCX, TXT, and image files
"""

import os
import pdfplumber
import pytesseract
from PIL import Image
from docx import Document
from pathlib import Path


class TextExtractor:
    """Extract text from various file formats"""
    
    def __init__(self, output_folder="extracted_texts"):
        """
        Initialize the text extractor
        
        Args:
            output_folder: Folder to save extracted text files
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        
    def extract_from_pdf(self, file_path):
        """
        Extract text from PDF file using pdfplumber
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text as string
        """
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def extract_from_docx(self, file_path):
        """
        Extract text from DOCX file
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text as string
        """
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX: {str(e)}")
    
    def extract_from_txt(self, file_path):
        """
        Extract text from TXT file
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Extracted text as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from TXT: {str(e)}")
    
    def extract_from_image(self, file_path):
        """
        Extract text from image file using pytesseract OCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted text as string
        """
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from image: {str(e)}")
    
    def extract_text(self, file_path):
        """
        Extract text from file based on file extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text as string
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self.extract_from_pdf(file_path)
        elif extension == '.docx':
            return self.extract_from_docx(file_path)
        elif extension == '.txt':
            return self.extract_from_txt(file_path)
        elif extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']:
            return self.extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def save_extracted_text(self, file_path, text):
        """
        Save extracted text to a file
        
        Args:
            file_path: Original file path
            text: Extracted text to save
            
        Returns:
            Path to saved text file
        """
        original_file = Path(file_path)
        output_filename = original_file.stem + "_extracted.txt"
        output_path = self.output_folder / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return output_path
    
    def process_file(self, file_path):
        """
        Extract text from file and save it
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Tuple of (extracted_text, saved_file_path)
        """
        print(f"Extracting text from: {file_path}")
        text = self.extract_text(file_path)
        saved_path = self.save_extracted_text(file_path, text)
        print(f"Text extracted and saved to: {saved_path}")
        return text, saved_path

