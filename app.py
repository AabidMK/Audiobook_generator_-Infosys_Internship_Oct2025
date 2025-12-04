# app.py
import streamlit as st
import tempfile
import os
import asyncio
import edge_tts
from io import BytesIO

# Text extraction libs
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import PyPDF2
from docx import Document

# -------- Optional Enrichment Import --------
try:
    from llm_enrich import enrich_text
    ENRICH_AVAILABLE = True
except:
    ENRICH_AVAILABLE = False

# -------- Streamlit Config --------
st.set_page_config(page_title="Audiobook + Q&A Generator", layout="wide")
st.title("📚 AI Audiobook + Q&A From Document")

st.markdown("Upload a PDF / DOCX / TXT / Image and convert it into Audio + Ask Questions from it.")


# OCR / Poppler Overrides
with st.expander("⚙️ OCR / Poppler settings (optional)"):
    tesseract_path = st.text_input("Tesseract executable path", value="")
    poppler_path = st.text_input("Poppler bin path", value="")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


# Text Extraction Helpers
def extract_text_from_pdf(path):
    text = ""
    try:
        reader = PyPDF2.PdfReader(open(path, "rb"))
        for p in reader.pages:
            if p.extract_text():
                text += p.extract_text() + "\n"
    except:
        pass

    if text.strip():
        return text

    imgs = convert_from_path(path, poppler_path=poppler_path if poppler_path else None)
    for img in imgs:
        text += pytesseract.image_to_string(img) + "\n"
    return text


def extract_text_from_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_text_from_image(path):
    img = Image.open(path)
    return pytesseract.image_to_string(img)


def extract_text_generic(temp_path):
    if temp_path.endswith(".pdf"):
        return extract_text_from_pdf(temp_path)
    if temp_path.endswith(".docx"):
        return extract_text_from_docx(temp_path)
    if temp_path.endswith(".txt"):
        with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return extract_text_from_image(temp_path)


# Simple Enrich
def simple_enrich(text):
    import re
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) and t[-1] not in ".!?":
        t += "."
    return t


# TTS - Edge
async def _edge_save(text, voice, out):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out)


def edge_generate_audio(text, voice, out_mp3):
    try:
        asyncio.run(_edge_save(text, voice, out_mp3))
        return True
    except Exception as e:
        return False


# --------- MAIN UI TABS ---------
tab1, tab2 = st.tabs(["🎧 Audiobook Generator", "💬 Q&A From Document"])

uploaded_file = st.sidebar.file_uploader("📄 Upload File", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"])
voice = st.sidebar.selectbox("🎙️ Select Voice", ["en-US-JennyNeural", "en-US-GuyNeural"])

# --------------------------------------------------------------------
# TAB 1 — AUDIOBOOK
# --------------------------------------------------------------------
with tab1:
    st.subheader("🎧 Generate Audiobook")

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        if st.button("📌 Extract Text"):
            with st.spinner("Extracting text..."):
                text = extract_text_generic(tmp_path)

            if not text.strip():
                st.error("No text detected!")
            else:
                st.session_state["text"] = text
                st.text_area("Extracted Text", text, height=250)
                st.success("Text extracted successfully!")

        if st.button("✨ Enrich Text"):
            if "text" not in st.session_state:
                st.error("Extract text first!")
            else:
                with st.spinner("Enhancing text..."):
                    if ENRICH_AVAILABLE:
                        enriched = enrich_text(st.session_state["text"])
                    else:
                        enriched = simple_enrich(st.session_state["text"])
                st.session_state["enriched_text"] = enriched
                st.text_area("Enriched Text", enriched, height=300)
                st.success("Enrichment Done!")

        if st.button("🎵 Generate MP3"):
            if "enriched_text" not in st.session_state:
                st.error("Enrich text first!")
            else:
                out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                with st.spinner("Generating audio... wait..."):
                    ok = edge_generate_audio(st.session_state["enriched_text"], voice, out)

                if ok:
                    audio = open(out, "rb").read()
                    st.audio(audio, format="audio/mp3")
                    st.download_button("⬇ Download Audiobook", audio, "audiobook.mp3")
                    st.success("Audiobook Ready!")
                else:
                    st.error("Failed converting text to audio!")


# --------------------------------------------------------------------
# TAB 2 — QUESTION ANSWER
# --------------------------------------------------------------------
with tab2:
    st.subheader("💬 Ask Questions From Extracted Text")

    if "text" not in st.session_state:
        st.info("Upload and extract text first (from Audiobook tab).")
    else:
        prompt = st.text_input("Ask something about the document:")

        if st.button("🔍 Search Answer"):
            text = st.session_state["text"]
            sentences = text.split(".")
            words = prompt.lower().split()

            matches = [s for s in sentences if any(w in s.lower() for w in words)]

            if matches:
                ans = ". ".join(matches[:2]).strip() + "."
                st.success("Answer Found:")
                st.write(ans)
            else:
                st.warning("No exact match found in document!")
                

# Footer
st.markdown("---")
st.markdown("⚡ Fast Q&A (keyword-based) — No Embeddings Required")
