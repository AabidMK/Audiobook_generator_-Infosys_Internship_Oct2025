# Packages and Modules Used in Audiobook Generator

## Core Python Packages (requirements.txt)

### 1. **pdfplumber** (>=0.10.0)
- **Purpose**: Extract text from PDF files
- **Usage**: Used in `text_extractor.py` to read PDF content
- **Website**: https://github.com/jsvine/pdfplumber

### 2. **pytesseract** (>=0.3.10)
- **Purpose**: OCR (Optical Character Recognition) for extracting text from images
- **Usage**: Used in `text_extractor.py` to read text from image files (JPG, PNG, etc.)
- **Dependencies**: Requires Tesseract OCR installed on system
- **Website**: https://github.com/madmaze/pytesseract

### 3. **Pillow** (>=10.3.0)
- **Purpose**: Image processing library (PIL - Python Imaging Library)
- **Usage**: Used by `pytesseract` to open and process image files
- **Website**: https://pillow.readthedocs.io/

### 4. **python-docx** (>=1.1.0)
- **Purpose**: Read and write Microsoft Word (.docx) files
- **Usage**: Used in `text_extractor.py` to extract text from DOCX files
- **Website**: https://python-docx.readthedocs.io/

### 5. **google-generativeai** (>=0.3.2)
- **Purpose**: Google Gemini AI API client library
- **Usage**: Used in `text_enricher.py` to enrich text using Google's Gemini models
- **Website**: https://ai.google.dev/gemini-api/docs

### 6. **edge-tts** (>=6.1.0)
- **Purpose**: Text-to-Speech using Microsoft Edge's neural voices
- **Usage**: Used in `tts_converter.py` to convert text to natural-sounding speech
- **Features**: Free, high-quality neural voices, supports multiple languages
- **Website**: https://github.com/rany2/edge-tts

### 7. **pydub** (>=0.25.1)
- **Purpose**: Audio manipulation library for combining audio files
- **Usage**: Used in `tts_converter.py` to merge multiple audio chunks into a single file
- **Dependencies**: Requires FFmpeg for MP3 support
- **Website**: https://github.com/jiaaro/pydub

### 8. **audioop-lts** (>=0.2.2)
- **Purpose**: Backport of audioop module for Python 3.13+
- **Usage**: Required by pydub on Python 3.13 (audioop was removed in Python 3.13)
- **Note**: This is a compatibility package

### 9. **sentence-transformers** (>=2.7.0)
- **Purpose**: Generates semantic embeddings using transformer-based models from Hugging Face
- **Usage**: Used in `embedding_generator.py` / `generate_embeddings.py` to create text embeddings and save them to CSV
- **Features**: Provides free, pre-trained models such as `all-MiniLM-L6-v2`
- **Website**: https://www.sbert.net/

### 10. **chromadb** (>=0.5.5)
- **Purpose**: Local vector database for storing and querying embeddings
- **Usage**: Used in `vector_db_store.py` / `store_embeddings.py` to upsert embedding CSVs into a persistent Chroma collection
- **Features**: Runs fully offline, simple Python API, supports metadata and similarity search
- **Website**: https://www.trychroma.com/

## Standard Library Modules

### Python Built-in Modules Used:
- **os**: Environment variables and file operations
- **sys**: System-specific parameters and functions
- **pathlib**: Object-oriented filesystem paths
- **asyncio**: Asynchronous I/O operations (for edge-tts)
- **tempfile**: Temporary file and directory creation

## External Dependencies

### System-Level Requirements:

1. **Tesseract OCR**
   - Required for: Image text extraction
   - Installation:
     - macOS: `brew install tesseract`
     - Linux: `sudo apt-get install tesseract-ocr`
     - Windows: Download from GitHub

2. **FFmpeg**
   - Required for: Audio file combination (pydub)
   - Installation:
     - macOS: `brew install ffmpeg`
     - Linux: `sudo apt-get install ffmpeg`
     - Windows: Download from ffmpeg.org

## Project Structure Modules

### Custom Modules (in this project):
1. **text_extractor.py** - Text extraction from various file formats
2. **text_enricher.py** - Text enrichment using Google Gemini API
3. **tts_converter.py** - Text-to-speech conversion using Edge-TTS
4. **embedding_generator.py** - Generates semantic embeddings and saves them to CSV
5. **vector_db_store.py** - Persists embedding CSVs into Chroma
6. **pipeline.py** - High-level pipeline orchestrating extraction, enrichment, and TTS
7. **main.py** - Command-line orchestrator using the pipeline
8. **convert_to_speech.py** - Standalone TTS conversion script
9. **generate_embeddings.py** - Standalone embedding generation script
10. **store_embeddings.py** - CLI for vector DB upserts

## Dependency Chain

```
main.py
└── pipeline.py
    ├── text_extractor.py
    │   ├── pdfplumber (PDF extraction)
    │   ├── python-docx (DOCX extraction)
    │   ├── pytesseract (Image OCR)
    │   └── Pillow (Image processing)
    │
    ├── text_enricher.py
    │   └── google-generativeai (Gemini API)
    │
    └── tts_converter.py
        ├── edge-tts (Text-to-Speech)
        └── pydub (Audio merging)
            └── audioop-lts (Python 3.13 compatibility)
            └── FFmpeg (system dependency)

generate_embeddings.py
└── embedding_generator.py
    └── sentence-transformers (semantic embeddings)

store_embeddings.py
└── vector_db_store.py
    └── chromadb (vector database)
```

## Installation

All packages can be installed via:
```bash
pip install -r requirements.txt
```

System dependencies must be installed separately:
```bash
# macOS
brew install tesseract ffmpeg

# Linux
sudo apt-get install tesseract-ocr ffmpeg
```

## Total Package Count

- **10 Python packages** from PyPI
- **2 system dependencies** (Tesseract, FFmpeg)
- **5 standard library modules** used directly
- **10 custom modules** in this project

