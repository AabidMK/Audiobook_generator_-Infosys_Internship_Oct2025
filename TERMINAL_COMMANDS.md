# Terminal Commands Guide

## Prerequisites

First, activate the virtual environment:
```bash
cd "/Users/adityakachhot/audio gen"
source venv/bin/activate
```

Set your API key (optional, if not set as environment variable):
```bash
export GEMINI_API_KEY="AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak"
```

---

## Step 1: Source File → Extracted Text

### Extract text from any source file (PDF, DOCX, TXT, or Image):

```bash
python -c "
from text_extractor import TextExtractor
extractor = TextExtractor(output_folder='extracted_texts')
text, path = extractor.process_file('Source_Files/your_file.pdf')
print(f'Extracted text saved to: {path}')
"
```

### Or use the main.py script (extraction only):
```bash
python main.py "Source_Files/your_file.pdf"
```

**Examples:**
```bash
# Extract from PDF
python main.py "Source_Files/AI AudioBook Generator.pdf"

# Extract from DOCX
python main.py "Source_Files/document.docx"

# Extract from image
python main.py "Source_Files/image.png"
```

**Output:** Text saved to `extracted_texts/your_file_extracted.txt`

---

## Step 2: Extracted Text → Enriched Text

### Enrich extracted text using Google Gemini API:

```bash
python -c "
from text_enricher import TextEnricher
import os
api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak')
enricher = TextEnricher(api_key=api_key, output_folder='enriched_texts')
text, path = enricher.process_file('extracted_texts/your_file_extracted.txt')
print(f'Enriched text saved to: {path}')
"
```

### Or use the main.py script with API key:
```bash
python main.py "extracted_texts/your_file_extracted.txt" --api-key AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak
```

**Example:**
```bash
python main.py "extracted_texts/AI AudioBook Generator_extracted.txt" --api-key AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak
```

**Output:** Enriched text saved to `enriched_texts/your_file_enriched.txt`

---

## Step 3: Enriched Text → Audiobook

### Convert enriched text to speech (single audio file):

```bash
python convert_to_speech.py "enriched_texts/your_file_enriched.txt"
```

**Example:**
```bash
python convert_to_speech.py "enriched_texts/AI AudioBook Generator_enriched.txt"
```

**Output:** Audio file saved to `audio_output/your_file_audio.mp3`

---

## Step 4: Text → Embeddings (CSV)

### Generate embeddings for extracted or enriched text:

```bash
python generate_embeddings.py "extracted_texts/your_file_extracted.txt"
```

**Examples:**
```bash
# Using default settings
python generate_embeddings.py "extracted_texts/AI AudioBook Generator_extracted.txt"

# Custom model, output filename, and chunk size
python generate_embeddings.py "extracted_texts/AI AudioBook Generator_extracted.txt" \
    --model sentence-transformers/all-MiniLM-L6-v2 \
    --output "AI AudioBook Generator_embeddings.csv" \
    --output-folder embeddings \
    --max-words 200
```

**Output:** CSV saved to `embeddings/your_file_embeddings.csv` with columns `text` and `embedding`.

> The first run downloads the selected sentence-transformers model from Hugging Face (internet connection required).

---

## Step 5: Embeddings → Vector DB (Chroma)

### Store embedding CSV into a persistent vector database:

```bash
python store_embeddings.py "embeddings/your_file_embeddings.csv"
```

**Examples:**
```bash
# Default storage (vector_store/, collection: audiobook_embeddings)
python store_embeddings.py "embeddings/AI AudioBook Generator_embeddings.csv"

# Custom directory, collection, and metadata
python store_embeddings.py "embeddings/AI AudioBook Generator_embeddings.csv" \
    --persist-dir vector_store \
    --collection audiobook_embeddings \
    --source "AI AudioBook Generator" \
    --tags aws database audiobook
```

**Output:** Chroma DB persisted in `vector_store/`. Re-open it with `chromadb.PersistentClient(path="vector_store")` to run similarity queries.

---

## Complete Pipeline (All Steps at Once)

### Extract → Enrich → Convert to Audiobook in one command:

```bash
python main.py "Source_Files/your_file.pdf" --api-key AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak --tts
```

**Example:**
```bash
python main.py "Source_Files/AI AudioBook Generator.pdf" --api-key AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak --tts
```

This single command will:
1. Extract text from PDF
2. Enrich it using Gemini API
3. Convert to audiobook (MP3)

---

## Quick Reference Commands

### For the new PDF file "AI AudioBook Generator.pdf":

**Step 1 - Extract:**
```bash
python main.py "Source_Files/AI AudioBook Generator.pdf"
```

**Step 2 - Enrich:**
```bash
python main.py "extracted_texts/AI AudioBook Generator_extracted.txt" --api-key AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak
```

**Step 3 - Convert to Audio:**
```bash
python convert_to_speech.py "enriched_texts/AI AudioBook Generator_enriched.txt"
```

**Step 4 - Generate Embeddings:**
```bash
python generate_embeddings.py "extracted_texts/AI AudioBook Generator_extracted.txt"
```

**Step 5 - Store in Vector DB:**
```bash
python store_embeddings.py "embeddings/AI AudioBook Generator_embeddings.csv"
```

**Or all at once:**
```bash
python main.py "Source_Files/AI AudioBook Generator.pdf" --api-key AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak --tts
```

---

## File Path Examples

Replace `your_file` with your actual filename:

- **Source files:** `Source_Files/your_file.pdf`
- **Extracted:** `extracted_texts/your_file_extracted.txt`
- **Enriched:** `enriched_texts/your_file_enriched.txt`
- **Audio:** `audio_output/your_file_audio.mp3`
- **Embeddings:** `embeddings/your_file_embeddings.csv`
- **Vector DB:** `vector_store/` (Chroma persistent storage)
- **Embeddings:** `embeddings/your_file_embeddings.csv`

---

---

## Step 4: Generate Embeddings

### Create embeddings from extracted or enriched text:

```bash
python generate_embeddings.py "extracted_texts/your_file_extracted.txt"
```

**Output:** Embeddings saved to `embeddings/your_file_embeddings.csv`

---

## Step 5: Store Embeddings in Vector Database

### Store embeddings for fast similarity search:

```bash
python store_embeddings.py "embeddings/your_file_embeddings.csv"
```

**Output:** Vector database created in `vector_store/` directory

---

## Step 6: Query Documents (RAG System)

### Ask questions about your documents:

```bash
python query_document.py "What is Amazon RDS?" --api-key AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak
```

**Example queries:**
```bash
# Basic query
python query_document.py "Explain database services" --api-key YOUR_API_KEY

# With custom top-k results
python query_document.py "What are the key features?" --api-key YOUR_API_KEY --top-k 3

# With custom collection
python query_document.py "Tell me about RDS" --api-key YOUR_API_KEY --collection document_embeddings
```

**How it works:**
1. Generates embedding for your query
2. Searches vector DB for top K most relevant chunks
3. Sends query + context to Gemini LLM
4. Returns answer based on document content

---

## Complete RAG Pipeline

### Full workflow: Extract → Embed → Store → Query

```bash
# 1. Extract text
python main.py "Source_Files/document.pdf"

# 2. Generate embeddings
python generate_embeddings.py "extracted_texts/document_extracted.txt"

# 3. Store in vector DB
python store_embeddings.py "embeddings/document_embeddings.csv"

# 4. Query the document
python query_document.py "Your question here" --api-key YOUR_API_KEY
```

---

## Notes

1. **Always activate venv first:** `source venv/bin/activate`
2. **API key:** You can either:
   - Set environment variable: `export GEMINI_API_KEY="your_key"`
   - Pass as argument: `--api-key your_key`
3. **File paths:** Use quotes if filename contains spaces
4. **Supported formats:** PDF, DOCX, TXT, JPG, PNG, BMP, TIFF, GIF
5. **Vector DB:** Make sure to store embeddings before querying documents
5. **Embeddings:** Uses the free `sentence-transformers/all-MiniLM-L6-v2` model; first run downloads from Hugging Face
6. **Vector DB:** Chroma stores files locally under `vector_store/`; safe to delete/rebuild if needed

