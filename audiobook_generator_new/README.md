# [file name]: README.md
# [file content begin]
# AudioBook Generator

This project was generated for the user based on the uploaded PDF specification. It includes:

- Streamlit frontend (app.py) with two tabs: Audiobook Generation and Document Q&A
- Text extraction (PDF, DOCX, TXT) using PyPDF2 and python-docx
- LLM enrichment wrapper (OpenAI integration optional via OPENAI_API_KEY). If no API key is provided, a safe fallback rewriting function is used
- TTS conversion using pyttsx3 (offline). Alternatively, user can integrate Coqui/Tortoise by modifying `tts.py`
- Vector database for document embeddings and semantic search
- Question answering system that chats with uploaded documents

## New Features Added:
1. **Two-tab interface**: 
   - Tab 1: Upload documents and generate audiobooks
   - Tab 2: Chat with your uploaded documents using Q&A

2. **Vector Database**: Automatically stores document embeddings when processing files for audiobook generation

3. **Semantic Search**: Finds relevant document chunks based on user questions

4. **Intelligent Q&A**: Uses OpenAI or fallback methods to answer questions about document content

See `requirements.txt` for dependencies and `USAGE.md` for quick run instructions.

Specification source: the user-provided PDF (AudioBook Generator). fileciteturn0file0
# [file content end]