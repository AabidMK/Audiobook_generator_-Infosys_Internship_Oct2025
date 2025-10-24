# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Tesseract path configuration
if os.name == 'nt':  # Windows
    TESSERACT_PATH = os.getenv('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
else:  # Linux/Mac
    TESSERACT_PATH = os.getenv('TESSERACT_PATH', '/usr/bin/tesseract')

# App configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
SUPPORTED_FORMATS = ['.txt', '.pdf', '.docx', '.jpg', '.jpeg', '.png', '.bmp']