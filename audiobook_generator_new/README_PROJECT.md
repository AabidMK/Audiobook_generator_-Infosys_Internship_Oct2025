## Project details (derived from uploaded spec)

Source spec: AudioBook Generator (user-provided PDF). The app follows the modules:
- Upload Module: Streamlit file_uploader
- Text Extraction Module: extractors.py (PDF/DOCX/TXT)
- LLM Enrichment Module: llm.py (OpenAI optional)
- Text-to-Speech Module: tts.py (pyttsx3)
- Audio Delivery: Streamlit displays audio and provides download
