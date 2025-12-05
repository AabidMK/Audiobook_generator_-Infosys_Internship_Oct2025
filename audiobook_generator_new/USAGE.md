## Quick start (local)

1. Create a Python virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Linux / macOS
   venv\Scripts\activate    # Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Set OpenAI API key if you want LLM rewriting (recommended for better narration):
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```
4. Run Streamlit app:
   ```bash
   streamlit run app.py
   ```
5. In the app, upload PDF/DOCX/TXT files, choose options and press **Generate Audiobook**.

Notes:
- By default the project uses an internal fallback 'audiobook-style' rewriter when OpenAI key is not present.
- TTS uses `pyttsx3` to synthesize audio. On some systems pyttsx3 may require platform-specific drivers.
