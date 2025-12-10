# Run in the terminal to run the pipeline:
pip install PyPDF2 pdfplumber python-docx pytesseract Pillow google-generativeai TTS python-dotenv

# Run in the terminal for vectordb: 
pip install chromadb
python -c "from TTS.api import TTS; print('TTS OK')"
python -c "import chromadb; print('Chroma OK')"

# Run store_embeddings_chroma.py then the result must be: 
📥 Loading CSV embeddings...
📦 Storing 1 embeddings in ChromaDB...
✅ Embeddings successfully stored in ChromaDB!
🧪 Testing vector search...

🔎 Enter a search query: artificial intelligence

📌 Top Matches:
→ Score: 0.09
  A Brief Introduction to Artificial Intelligence...
