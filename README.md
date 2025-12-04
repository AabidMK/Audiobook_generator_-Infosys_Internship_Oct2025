# Audiobook Generator

An audiobook generator system that extracts text from various file formats and enriches it using Google Gemini API.

## Features

- **Text Extraction**: Extract text from PDF, DOCX, TXT, and image files (JPG, PNG, BMP, TIFF, GIF)
- **Text Enrichment**: Enhance extracted text using Google Gemini API for better audiobook quality
- **Text-to-Speech**: Convert enriched text to natural-sounding speech using Edge-TTS (Microsoft's neural voices)
- **Embeddings Generation**: Create semantic embeddings for extracted or enriched text and save them to CSV
- **Vector DB Storage**: Load embeddings into a local Chroma vector database for semantic search
- **Web Interface**: Clean Streamlit frontend with document upload and chat interface
- **Organized Output**: Automatically saves extracted text, enriched text, audio files, embeddings, and vector DB files in separate folders

## Installation

1. **Create and activate virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

**Note**: If you see "could not be resolved" import errors in your IDE, see [SETUP.md](SETUP.md) for instructions on configuring your IDE to use the virtual environment.

3. Install Tesseract OCR (required for image text extraction):
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. Install FFmpeg (required for audio file combination):
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)

5. Set up Google Gemini API key:
   - **Quick setup**: Run `./setup_api.sh` (if you have the API key ready)
   - **Manual setup**: Set it as an environment variable:
     ```bash
     export GEMINI_API_KEY="your_api_key_here"
     ```
   - **Or pass it directly**: Use `--api-key` flag when running (see Usage below)
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Usage

**Important**: Always activate the virtual environment before running:
```bash
source venv/bin/activate  # On macOS/Linux
# OR use the convenience script:
./run.sh <file_path>
```

### Basic Usage

```bash
python main.py <file_path>
```

Example:
```bash
python main.py document.pdf
python main.py document.docx
python main.py document.txt
python main.py image.png
```

### With API Key

```bash
python main.py <file_path> --api-key YOUR_GEMINI_API_KEY
```

### With TTS (Full Pipeline)

To extract, enrich, AND convert to speech in one go:

```bash
python main.py <file_path> --api-key YOUR_API_KEY --tts
```

### Standalone TTS Conversion

To convert an existing enriched text file to speech:

```bash
python convert_to_speech.py enriched_texts/document_enriched.txt
```

Example:
```bash
python main.py document.pdf --api-key AIzaSyXXXXXXXXXXXXXXXXXXXXXXXX --tts
python convert_to_speech.py enriched_texts/document_enriched.txt
```

### Generate Embeddings

Produce semantic embeddings for any extracted or enriched text file and save them as a CSV:

```bash
python generate_embeddings.py extracted_texts/document_extracted.txt
```

You can customise the embedding model, output filename, output directory, and maximum words per chunk:

```bash
python generate_embeddings.py extracted_texts/document_extracted.txt \
    --model sentence-transformers/all-MiniLM-L6-v2 \
    --output document_embeddings.csv \
    --output-folder embeddings \
    --max-words 200
```

### Store Embeddings in Vector Database

Store generated embeddings in a Chroma vector database for fast similarity search:

```bash
python store_embeddings.py embeddings/document_embeddings.csv
```

### Query Documents (RAG System)

Query your documents using Retrieval-Augmented Generation (RAG):

```bash
python query_document.py "What is Amazon RDS?" --api-key YOUR_GEMINI_API_KEY
```

The system will:
1. Generate embeddings for your query
2. Search for top K most relevant chunks in the vector database
3. Send query + context to Gemini LLM
4. Return an answer based on the document content

Options:
```bash
python query_document.py "Your question here" \
    --api-key YOUR_API_KEY \
    --top-k 5 \
    --collection audiobook_embeddings \
    --persist-dir vector_store
```

### Web Interface (Streamlit)

Launch the clean web interface with document upload and chat:

```bash
streamlit run app.py
```

Or use the convenience script:
```bash
./run_streamlit.sh
```

**Features:**
- **Upload Document Tab**: Upload PDF/DOCX/TXT/Images, automatically process (extract → enrich → audio → embeddings → vector DB), and download generated audio
- **Chat Tab**: Ask questions about your uploaded documents using RAG (Retrieval-Augmented Generation)

The web interface provides a clean, user-friendly way to:
1. Upload documents and generate audiobooks
2. Automatically create embeddings and store in vector DB
3. Chat with your documents using natural language queries

> **Note:** The first run will download the selected sentence-transformers model from Hugging Face (internet connection required).

### Store Embeddings in Vector DB

Load any embedding CSV (from the previous step) into a local Chroma database for semantic search:

```bash
python store_embeddings.py embeddings/document_embeddings.csv
```

Customise the persistence directory, collection, and metadata:

```bash
python store_embeddings.py embeddings/document_embeddings.csv \
    --persist-dir vector_store \
    --collection audiobook_embeddings \
    --source "AI AudioBook Generator" \
    --tags aws database audiobook
```

The Chroma DB files are stored in the `vector_store/` directory. You can reopen the same database in any script by pointing `chromadb.PersistentClient` to that path.

## Project Structure

```
audio gen/
├── main.py              # Main orchestrator script
├── text_extractor.py    # Text extraction module
├── text_enricher.py     # Text enrichment module
├── tts_converter.py     # Text-to-speech conversion module
├── pipeline.py          # Reusable pipeline for extraction + enrichment + TTS
├── embedding_generator.py # Embedding generation module
├── vector_db_store.py      # Vector database storage module
├── query_processor.py      # Query processing and similarity search
├── rag_responder.py        # RAG (Retrieval-Augmented Generation) responder
├── convert_to_speech.py    # Standalone TTS conversion script
├── generate_embeddings.py  # Standalone embedding generation script
├── store_embeddings.py     # Store embeddings in vector DB script
├── query_document.py       # Query documents using RAG script
├── app.py                  # Streamlit web interface
└── run_streamlit.sh        # Convenience script to run Streamlit app
├── vector_db_store.py   # Vector DB helper for Chroma
├── store_embeddings.py  # CLI to store embeddings in Chroma
├── requirements.txt     # Python dependencies
├── run.sh               # Convenience script (auto-activates venv)
├── SETUP.md             # Setup guide for fixing import errors
├── venv/                # Virtual environment (created after setup)
├── extracted_texts/     # Folder for extracted text files
├── enriched_texts/      # Folder for enriched text files
├── audio_output/        # Folder for generated audio files
├── embeddings/          # Folder for generated embedding CSVs
└── vector_store/        # Persistent directory for the Chroma vector database
```

## Supported File Formats

- **PDF**: Uses `pdfplumber` library
- **DOCX**: Uses `python-docx` library
- **TXT**: Plain text files
- **Images**: JPG, JPEG, PNG, BMP, TIFF, GIF (uses `pytesseract` OCR)

## How It Works

1. **Text Extraction**: The system identifies the file type and extracts text using appropriate methods:
   - PDF → pdfplumber
   - DOCX → python-docx
   - TXT → direct file reading
   - Images → pytesseract OCR

2. **Text Saving**: Extracted text is saved to `extracted_texts/` folder with `_extracted.txt` suffix

3. **Text Enrichment**: The extracted text is sent to Google Gemini API for enhancement:
   - Makes text engaging and conversational
   - Removes Markdown formatting while preserving information
   - Expands abbreviations (e.g., "e.g." → "for example")
   - Converts lists to spoken style ("First... then... finally...")
   - Adds natural pauses and breaks for rhythm
   - Optimizes sentence structure for spoken flow
   - Maintains all original information and depth

4. **Enriched Text Saving**: Enriched text is saved to `enriched_texts/` folder with `_enriched.txt` suffix

5. **Text-to-Speech Conversion** (Optional): The enriched text can be converted to speech using Edge-TTS:
   - Uses Microsoft's neural voices for natural-sounding speech
   - Automatically handles long texts by splitting into chunks and combining into a single MP3 file
   - Saves one complete audio file in `audio_output/` folder (no multiple parts)
6. **Embeddings Generation** (Optional): Generate semantic embeddings for each text chunk:
   - Uses the free `sentence-transformers/all-MiniLM-L6-v2` model
   - Splits text into manageable chunks for high-quality embeddings
   - Saves embeddings as CSV files (`embeddings/` folder) with `text` and `embedding` columns

7. **Vector Database Storage** (Optional): Store embeddings in Chroma vector database:
   - Enables fast similarity search for document retrieval
   - Persistent storage in `vector_store/` directory
   - Supports metadata tagging for better organization

8. **Document Querying (RAG)** (Optional): Query documents using Retrieval-Augmented Generation:
   - Generates embeddings for user queries
   - Performs similarity search to find top K relevant chunks
   - Uses Gemini LLM to generate answers based on retrieved context
   - Returns accurate, context-aware responses
7. **Vector DB Storage** (Optional): Persist embeddings into a Chroma vector database:
   - Runs locally—no external service required
   - Stores embeddings plus metadata for later semantic search
   - Output directory: `vector_store/`

## Customization

You can customize the enrichment prompt by modifying the `enrich_text` method in `text_enricher.py` or by passing a custom prompt when calling the enrichment function.

### Programmatic Usage (Pipeline)

You can use the pipeline directly from Python:

```python
from pipeline import AudiobookPipeline

pipeline = AudiobookPipeline()
results = pipeline.process(
    "Source_Files/your_file.pdf",
    api_key="YOUR_GEMINI_API_KEY",
    convert_to_audio=True,
)

print(results["extracted_text_path"])
print(results["enriched_text_path"])
print(results["audio_path"])
```

The pipeline automatically skips steps if you pass in files that have already been extracted or enriched (for example, passing a file from `extracted_texts/` skips extraction).

## Error Handling

The system includes error handling for:
- Unsupported file formats
- Missing files
- API errors
- OCR failures

## License

MIT License

