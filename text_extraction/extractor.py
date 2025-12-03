"""
Core Text Extraction Module

This module handles text extraction from various file formats with fallback logic.
It uses the same exact libraries and logic as the original app.py.
"""

import tempfile
import os
import re
import logging
from typing import Tuple, Dict, Any
from PIL import Image, ImageEnhance, ImageFilter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OCR setup - Same as original app.py
try:
    import pytesseract
    # Try to set tesseract path for Windows
    try:
        pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    except:
        pass
    tesseract_available = True
    logger.info("Tesseract OCR is available")
except ImportError:
    tesseract_available = False
    logger.warning("Tesseract OCR not available. Image text extraction will be limited.")

def extract_text_from_file(uploaded_file) -> str:
    """
    Extract text from various file types - NO TRUNCATION
    
    This is the MAIN extraction function that handles all file formats.
    
    Args:
        uploaded_file: File-like object with read() method and name attribute
        
    Returns:
        Extracted text as string, or error message if extraction fails
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        file_ext = uploaded_file.name.lower().split('.')[-1]
        text = ""
        
        logger.info(f"Extracting text from {uploaded_file.name} (type: {file_ext})")
        
        # Dispatch based on file extension
        if file_ext == 'txt':
            text = _extract_txt(tmp_path)
                
        elif file_ext == 'pdf':
            text = _extract_pdf(tmp_path)
                
        elif file_ext == 'docx':
            text = _extract_docx(tmp_path)
                
        elif file_ext in ['jpg', 'jpeg', 'png', 'bmp']:
            text = _extract_image(tmp_path)
        else:
            text = f"🚫 Unsupported file type: {file_ext}"
        
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        logger.info(f"Extraction complete. Got {len(text)} characters.")
        
        # Return extracted text or error message
        return text.strip() if text.strip() else "📭 No text extracted from file."
        
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return f"🚫 Extraction error: {str(e)}"

def _extract_txt(filepath: str) -> str:
    """Extract text from TXT files"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encodings if utf-8 fails
        encodings = ['latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                    return f.read()
            except:
                continue
        return "🚫 TXT reading error: Could not decode file"
    except Exception as e:
        return f"🚫 TXT reading error: {str(e)}"

def _extract_pdf(filepath: str) -> str:
    """Extract text from PDF files with fallback"""
    text = ""
    
    # Try pdfplumber first (most accurate)
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Page {page.page_number} ---\n{page_text}\n\n"
        logger.info(f"PDF extraction with pdfplumber: {len(text)} chars")
        if text:
            return text
    except ImportError:
        logger.warning("pdfplumber not available, trying PyPDF2...")
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}, trying fallback...")
    
    # Fallback to PyPDF2
    try:
        import PyPDF2
        with open(filepath, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
        logger.info(f"PDF extraction with PyPDF2: {len(text)} chars")
        if text:
            return text
    except ImportError:
        logger.warning("PyPDF2 not available")
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {e}")
    
    # If all methods fail
    logger.error("No PDF extraction library available")
    return "📄 Install pdfplumber: pip install pdfplumber\nOr install PyPDF2: pip install PyPDF2"

def _extract_docx(filepath: str) -> str:
    """Extract text from DOCX files with fallback"""
    # Try python-docx first
    try:
        from docx import Document
        doc = Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        logger.info(f"DOCX extraction with python-docx: {len(text)} chars")
        if text:
            return text
    except ImportError:
        logger.warning("python-docx not available, trying docx2txt...")
    except Exception as e:
        logger.warning(f"python-docx failed: {e}, trying fallback...")
    
    # Fallback to docx2txt
    try:
        import docx2txt
        text = docx2txt.process(filepath)
        logger.info(f"DOCX extraction with docx2txt: {len(text)} chars")
        if text:
            return text
    except ImportError:
        logger.warning("docx2txt not available")
    except Exception as e:
        logger.warning(f"docx2txt failed: {e}")
    
    # If all methods fail
    logger.error("No DOCX extraction library available")
    return "📋 Install python-docx: pip install python-docx\nOr install docx2txt: pip install docx2txt"

def _extract_image(filepath: str) -> str:
    """Extract text from images using OCR with multiple fallback strategies"""
    if not tesseract_available:
        logger.warning("OCR not available for image extraction")
        return "🔍 Tesseract OCR not available. Install: pip install pytesseract and install tesseract-ocr"
    
    try:
        original_image = Image.open(filepath)
        logger.info(f"Processing image: {original_image.size}, mode: {original_image.mode}")
        
        # Strategy 1: Try with original image first
        text = pytesseract.image_to_string(original_image, config='--psm 6')
        if text.strip():
            logger.info(f"OCR successful with original image: {len(text)} chars")
            return text
        
        # Strategy 2: Try with enhanced image
        enhanced_image = enhance_image_for_ocr(original_image)
        text = pytesseract.image_to_string(enhanced_image, config='--psm 6')
        if text.strip():
            logger.info(f"OCR successful with enhanced image: {len(text)} chars")
            return text
        
        # Strategy 3: Try different PSM modes
        psm_modes = [
            ('1', 'Automatic page segmentation with OSD'),
            ('3', 'Fully automatic page segmentation'),
            ('4', 'Assume a single column of text'),
            ('6', 'Assume a single uniform block of text'),
            ('11', 'Sparse text'),
            ('12', 'Sparse text with OSD')
        ]
        
        for psm, description in psm_modes:
            text = pytesseract.image_to_string(original_image, config=f'--psm {psm}')
            if text.strip():
                logger.info(f"OCR successful with PSM mode {psm}: {description}, {len(text)} chars")
                return text
        
        logger.warning("No text detected in image after trying multiple OCR strategies")
        return "🔍 No text detected in image after trying multiple OCR strategies"
        
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        return f"🚫 OCR Error: {str(e)}"

def enhance_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Enhance image for better OCR results
    
    Args:
        image: PIL Image object
        
    Returns:
        Enhanced PIL Image
    """
    try:
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
        
        # Apply contrast enhancement
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Apply sharpness enhancement
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Apply noise reduction
        image = image.filter(ImageFilter.MedianFilter(3))
        
        logger.info("Image enhanced for OCR")
        return image
        
    except Exception as e:
        logger.warning(f"Image enhancement failed: {e}, returning original")
        return image

def validate_extracted_text(text: str, min_words: int = 5) -> Tuple[bool, str]:
    """
    Validate if extracted text is meaningful
    
    Args:
        text: Extracted text to validate
        min_words: Minimum number of words to consider valid
        
    Returns:
        Tuple of (is_valid, reason_message)
    """
    if not text or not text.strip():
        return False, "No text extracted"
    
    # Check for error messages
    error_patterns = [
        r'🚫.*error',
        r'📄.*install',
        r'📋.*install', 
        r'🔍.*not available',
        r'📭.*no text',
        r'Install.*pip',
        r'not available',
        r'extraction error',
        r'no text',
        r'unsupported file',
        r'OCR Error',
        r'TXT reading error',
        r'PDF extraction error'
    ]
    
    for pattern in error_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Contains error message"
    
    # Clean and check word count
    clean_text = re.sub(r'[^\w\s]', '', text)
    words = clean_text.split()
    
    if len(words) < min_words:
        return False, f"Too short: only {len(words)} words (minimum {min_words})"
    
    # Check if it's mostly special characters
    alpha_chars = sum(c.isalpha() for c in text)
    if alpha_chars < 10:
        return False, "Not enough alphabetic characters"
    
    logger.info(f"Text validation passed: {len(words)} words, {len(text)} chars")
    return True, f"Valid text with {len(words)} words"

def get_file_info(uploaded_file) -> Dict[str, Any]:
    """
    Get information about the uploaded file
    
    Args:
        uploaded_file: File-like object with name and size attributes
        
    Returns:
        Dictionary with file information
    """
    file_ext = uploaded_file.name.lower().split('.')[-1]
    
    file_types = {
        'txt': {'type': '📝 Text File', 'icon': '📝'},
        'pdf': {'type': '📄 PDF Document', 'icon': '📄'},
        'docx': {'type': '📋 Word Document', 'icon': '📋'},
        'doc': {'type': '📋 Word Document', 'icon': '📋'},
        'jpg': {'type': '🖼️ Image', 'icon': '🖼️'},
        'jpeg': {'type': '🖼️ Image', 'icon': '🖼️'},
        'png': {'type': '🖼️ Image', 'icon': '🖼️'},
        'bmp': {'type': '🖼️ Image', 'icon': '🖼️'},
    }
    
    info = file_types.get(file_ext, {'type': '📁 File', 'icon': '📁'})
    
    return {
        'filename': uploaded_file.name,
        'extension': file_ext,
        'type': info['type'],
        'icon': info['icon'],
        'size': uploaded_file.size,
        'size_kb': uploaded_file.size / 1024,
        'size_mb': uploaded_file.size / (1024 * 1024),
        'ocr_available': tesseract_available if file_ext in ['jpg', 'jpeg', 'png', 'bmp'] else None
    }
