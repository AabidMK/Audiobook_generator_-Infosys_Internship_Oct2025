# OCR → Enrich → TTS (Streamlit)

A simple Streamlit app to:
- Extract text from files (txt, pdf, docx, images)
- Optionally clean/enrich with OpenAI
- Generate speech via pyttsx3 (offline) or gTTS (online)

## Features
- PDF text via pdfplumber, OCR fallback via pdf2image + Tesseract
- Image OCR via Tesseract
- DOCX via python-docx
- Safe fallback if `OPENAI_API_KEY` is not configured (returns original text)
- Saves extracted text and audio to `outputs/`

## Requirements
- Python 3.10+
- Windows prerequisites for OCR on PDFs:
  - Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
  - Poppler for Windows: https://github.com/oschwartz10612/poppler-windows/releases/
  - Add both to PATH. For Tesseract, the installer usually adds it. If not, set in code:
    ```python
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    ```

## Setup
1. Create and activate a virtual environment
2. Install dependencies
3. (Optional) Set `OPENAI_API_KEY` if you want AI enrichment
4. Run Streamlit

### Commands (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Optional for OpenAI
$env:OPENAI_API_KEY = "your_key_here"
$env:OPENAI_MODEL = "gpt-4o-mini"

streamlit run app.py
```

## Usage
- Upload a file in the UI. If it is a scanned PDF, ensure Tesseract and Poppler are installed.
- Toggle AI enrichment in the sidebar if you set the OpenAI key.
- Choose TTS engine and generate audio.
- Files are saved under `outputs/text` and `outputs/audio`.

## Troubleshooting
- Tesseract not found: install Tesseract and ensure `tesseract.exe` is discoverable in PATH; or hardcode the path in `extractor.py`.
- Poppler not found: install Poppler and add `bin` directory to PATH so `pdf2image` can convert pages.
- OpenAI errors: enrich step falls back to original text.
- pyttsx3 voices: available voices depend on your system (SAPI5 on Windows). You may set `voice_id` in code.

## Notes
- This is a minimal demo. For large documents, consider chunking and streaming audio in segments.

## To Run This on Cmd Line
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"; .\.venv\Scripts\python.exe watch_uploads.py
