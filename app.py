import streamlit as st
from pathlib import Path

from utils import ensure_dirs, OUTPUT_TEXT_DIR, OUTPUT_AUDIO_DIR, file_stem
from extractor import extract_text, extract_and_save, OCRDependencyMissing
from llm_enrich import enrich_text
from tts import tts_synthesize

st.set_page_config(page_title="OCR → Enrich → TTS", page_icon="🗣️", layout="wide")

ensure_dirs()

st.title("OCR → LLM Enrichment → TTS")
st.write("Upload a document or image, optionally enhance the text with AI, and generate speech.")

with st.sidebar:
    st.header("Options")
    do_enrich = st.toggle("Use AI enrichment (OpenAI)", value=False, help="Requires OPENAI_API_KEY")
    model = st.text_input("OpenAI model", value="gpt-4o-mini")
    engine = st.selectbox("TTS engine", options=["pyttsx3", "gtts"], index=0)
    rate = st.number_input("pyttsx3 rate (wpm)", min_value=80, max_value=300, value=180)
    lang = st.text_input("gTTS language", value="en")

uploaded = st.file_uploader("Upload a file (.txt, .pdf, .docx, image)", type=["txt", "pdf", "docx", "png", "jpg", "jpeg", "bmp", "tiff", "tif"]) 

if uploaded:
    tmp_path = Path("uploads") / uploaded.name
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())
    st.success(f"Saved upload to {tmp_path}")

    with st.spinner("Extracting text..."):
        try:
            text = extract_text(tmp_path)
            out_txt = extract_and_save(tmp_path)
        except OCRDependencyMissing as e:
            st.error("Tesseract OCR is not installed or not found.\n\n" 
                     "Fix steps on Windows:\n"
                     "1) Install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki\n"
                     "2) Reopen PowerShell so PATH refreshes\n"
                     "3) Optionally set env TESSERACT_CMD to tesseract.exe full path\n"
                     "4) For PDF OCR, also install Poppler and set POPPLER_PATH to its bin folder",
                     icon="🚨")
            st.stop()
    st.write(f"Text saved to: {out_txt}")

    if not text.strip():
        st.warning("No text extracted. If PDF is scanned, ensure Tesseract and Poppler are installed for OCR.")
    
    st.subheader("Extracted text")
    st.text_area("Text", value=text, height=250, key="extracted_text")

    final_text = text
    if do_enrich:
        with st.spinner("Enriching with OpenAI..."):
            final_text = enrich_text(text, model=model)
        st.subheader("Enriched text")
        st.text_area("Text (enriched)", value=final_text, height=250, key="enriched_text")

    if final_text.strip():
        st.subheader("Text-to-Speech")
        basename = file_stem(uploaded.name)
        if st.button("Generate speech"):
            with st.spinner("Synthesizing audio..."):
                audio_path = tts_synthesize(
                    final_text,
                    engine=engine,
                    rate=rate if engine == "pyttsx3" else None,
                    language=lang if engine == "gtts" else "en",
                    basename=basename,
                )
            st.success(f"Saved audio to: {audio_path}")
            if audio_path.suffix.lower() == ".mp3":
                st.audio(str(audio_path), format="audio/mp3")
            else:
                st.audio(str(audio_path))

st.divider()
st.caption("Outputs are saved under 'outputs/text' and 'outputs/audio'. On Windows, install Tesseract OCR and Poppler for best PDF OCR.")
