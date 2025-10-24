# Audiobook_generator_-Infosys_Internship_Oct2025

Text Extraction and Enrichment Pipeline

This project is a Python-based pipeline that extracts text from various file types (PDFs, DOCX, images) and then uses the Google Gemini API to "enrich" or rewrite the text, improving its grammar, tone, and clarity.

File Structure
--------------

Your project folder should look like this:

.
├── .env
├── main.py
├── text_extraction.py
└── text_enrichment.py

* `main.py`: The main entry point to run the pipeline.
* `text_extraction.py`: A module to extract raw text from different file formats.
* `text_enrichment.py`: A module to send the extracted text to the Gemini API for rewriting.
* `.env`: A file to securely store your API key (you must create this).

---

Setup Instructions
------------------

Follow these steps to set up and run the project.

1. Python Environment (Recommended)
----------------------------------

It is highly recommended to use a virtual environment to manage dependencies.

# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

2. Install Python Dependencies
------------------------------

The project requires several Python libraries. You can install them all using pip.

pip install PyMuPDF python-docx pytesseract Pillow requests python-dotenv

Or, you can create a `requirements.txt` file with the following content:

requirements.txt
----------------
PyMuPDF
python-docx
pytesseract
Pillow
requests
python-dotenv
----------------

...and then install from it:

pip install -r requirements.txt

3. Install Tesseract-OCR (Crucial for Image Extraction)
------------------------------------------------------

This pipeline uses `pytesseract` for Optical Character Recognition (OCR) on image files. This requires the Tesseract-OCR engine to be installed on your system.

* **Windows:** Download and run the installer from Tesseract at UB Mannheim (https://github.com/UB-Mannheim/tesseract/wiki).
* **macOS:** Use Homebrew: `brew install tesseract`
* **Linux (Ubuntu/Debian):** Use apt: `sudo apt-get install tesseract-ocr`

IMPORTANT: After installing Tesseract, you MUST update the path in `text_extraction.py`. Open the file and find this line (around line 15):

# text_extraction.py
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows example

Change this path to match where Tesseract was installed on your system.

* **macOS (Homebrew) default:** `/usr/local/bin/tesseract` or `/opt/homebrew/bin/tesseract`
* **Linux default:** `/usr/bin/tesseract`

4. Create .env File for API Key
-------------------------------

The script in `text_enrichment.py` requires a Google Gemini API key.

1.  Create a file named `.env` in the same directory as the Python scripts.
2.  Get your API key from Google AI Studio (https://aistudio.google.com/app/apikey).
3.  Add your key to the `.env` file like this:

    GEMINI_API_KEY=YOUR_API_KEY_HERE

---

How to Run
----------

Once all dependencies are installed and configured, you can run the pipeline from your terminal.

The `main.py` script takes one argument: the path to the file you want to process.

python main.py <path/to/your/file>

Supported file types: .pdf, .docx, .txt, .png, .jpg, .jpeg, .bmp, .tiff, .webp

Example
-------

# Example with a PDF
python main.py "my_report.pdf"

# Example with an image
python main.py "scanned_notes.png"

Output
------

The script will create two new files in the same directory as your input file:

1.  **`[filename]_extracted.txt`**: Contains the raw, extracted text.
2.  **`[filename]_extracted_enriched.txt`**: Contains the enhanced, rewritten text from the Gemini API.
