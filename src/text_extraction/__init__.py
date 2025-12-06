"""
Text Extraction Module for AI Audiobook Generator

This module provides text extraction from various file formats:
- TXT files
- PDF documents  
- DOCX files
- Images (via OCR)

Author: [Your Name]
Version: 1.0.0
"""

from .extractor import (
    extract_text_from_file,
    validate_extracted_text,
    get_file_info,
    enhance_image_for_ocr,
    tesseract_available
)

__version__ = "1.0.0"
__author__ = "[Your Name]"
__email__ = "[Your Email]"

__all__ = [
    'extract_text_from_file',
    'validate_extracted_text',
    'get_file_info',
    'enhance_image_for_ocr',
    'tesseract_available'
]