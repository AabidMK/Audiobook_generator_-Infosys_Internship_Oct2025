# app.py
import os
import uuid
import streamlit as st
from pathlib import Path
from PIL import Image
import pdfplumber
from docx import Document
import pytesseract
from gtts import gTTS
import chromadb
from sentence_transformers import SentenceTransformer

# Try to import Gemini SDK; if absent, code will fallback to non-Gemini paths
try:
    import google.generativeai as genai
    GEMINI_SDK = True
except Exception:
    genai = None
    GEMINI_SDK = False

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Audiobook Generator", layout="wide")

BASE = Path(__file__).parent
UPLOAD_DIR = BASE / "uploads"
AUDIO_DIR = BASE / "audio"
DB_DIR = BASE / "chroma_db"
COLLECTION_NAME = "audiobook_docs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- GEMINI CONFIG ----------------
# Set your Gemini API key as an environment variable GEMINI_API_KEY or paste here (temporary)
GEMINI_API_KEY = os.getenv("AIzaSyCYfjCBPKUItU3VSdc9x2uydhpZS-j--IQ", "")  # or set: "YOUR_KEY"
if GEMINI_SDK and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-pro")
    except Exception:
        gemini_model = None
else:
    gemini_model = None

# ---------------- Chroma & Embeddings ----------------
client = chromadb.PersistentClient(path=str(DB_DIR))
collection = client.get_or_create_collection(name=COLLECTION_NAME)
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# ---------------- Helpers: extraction ----------------
def extract_text_pdf(path: str) -> str:
    try:
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                p = page.extract_text()
                if p:
                    text += p + "\n"
        return text.strip()
    except Exception:
        return ""

def extract_text_docx(path: str) -> str:
    try:
        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        return "\n".join(paragraphs).strip()
    except Exception:
        return ""

def extract_text_txt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def extract_text_image(path: str) -> str:
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img)
    except Exception:
        return ""

# ---------------- Helpers: chunking & safe delete ----------------
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150):
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(start + chunk_size, L)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def safe_clear_file_chunks(filename: str):
    """
    Remove all items that were added for filename by checking metadata 'source'.
    Deletes by ids to avoid using collection.delete() without filter.
    """
    try:
        data = collection.get()
        ids_all = data.get("ids", [])
        metas = data.get("metadatas", [])
        to_delete = []
        for _id, meta in zip(ids_all, metas):
            if isinstance(meta, dict) and meta.get("source") == filename:
                to_delete.append(_id)
        if to_delete:
            collection.delete(ids=to_delete)
    except Exception:
        # ignore errors to keep process robust
        pass

def save_chunks_to_chroma(chunks, filename: str):
    if not chunks:
        return
    safe_clear_file_chunks(filename)
    ids = [f"{filename}__{i}" for i in range(len(chunks))]
    embeddings = embed_model.encode(chunks).tolist()
    metas = [{"source": filename} for _ in chunks]
    collection.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metas)

# ---------------- Gemini backend enrichment (server-side only) ----------------
def gemini_enrich_text_for_audiobook(text: str) -> str:
    """
    Backend-only text enrichment. Uses Gemini if available, otherwise returns a trimmed version.
    The enriched text is NOT displayed to the user in the UI; it's used for audio + RAG indexing only.
    """
    if not text:
        return ""
    snippet = text[:3500]  # keep prompt size reasonable
    prompt = f"""
You are an audiobook writer. Convert the text below into an engaging, listener-friendly audiobook narration.
Keep it clear, add flow/transition cues, and make it concise.

Text:
{snippet}
"""
    if gemini_model:
        try:
            resp = gemini_model.generate_content(prompt)
            # sdk may provide .text or nested candidates
            txt = getattr(resp, "text", None)
            if txt:
                return txt.strip()
            try:
                return resp["candidates"][0]["content"][0]["text"].strip()
            except Exception:
                return snippet
        except Exception:
            return snippet
    else:
        # fallback: simple light formatting (no LLM)
        return snippet

# ---------------- Gemini answer-from-context (server-side) ----------------
def gemini_answer_from_context(question: str, context: str) -> str:
    """
    Ask Gemini to answer the question using ONLY the provided context.
    If Gemini not available, fallback to a conservative heuristic: pick best-matching sentences.
    """
    if not context:
        return "Not found in document."

    prompt = f"""
Answer the question using ONLY the context below. If the answer is not present, reply exactly: "Not found in document."

Context:
{context}

Question:
{question}

Give a short, precise answer (1-2 sentences). Do not repeat the entire context.
"""
    if gemini_model:
        try:
            resp = gemini_model.generate_content(prompt)
            txt = getattr(resp, "text", None)
            if txt:
                return txt.strip()
            try:
                return resp["candidates"][0]["content"][0]["text"].strip()
            except Exception:
                return "Not found in document."
        except Exception:
            pass

    # Fallback heuristic:
    q_words = [w.lower() for w in question.split() if len(w) > 2]
    sentences = []
    for chunk in context.split("\n"):
        for s in chunk.replace("\n", " ").split(". "):
            s_clean = s.strip()
            if not s_clean:
                continue
            score = sum(1 for q in q_words if q in s_clean.lower())
            if score > 0:
                sentences.append((score, s_clean))
    if sentences:
        sentences.sort(key=lambda x: -x[0])
        top = sentences[0][1]
        if not top.endswith("."):
            top += "."
        # Optionally include second highest if different
        if len(sentences) > 1 and sentences[1][1] != top:
            second = sentences[1][1]
            if not second.endswith("."):
                second += "."
            return (top + " " + second)[:800]
        return top
    # ultimate fallback: return first one or two sentences of context
    ctx_sents = [s.strip() for s in context.replace("\n", " ").split(". ") if s.strip()]
    if ctx_sents:
        short = ". ".join(ctx_sents[:2])
        if not short.endswith("."):
            short += "."
        return short[:800]
    return "Not found in document."

# ----------------- TTS -----------------
def generate_audio_and_bytes(text: str):
    # gTTS gets long text failure-prone; limit length
    safe_text = text if len(text) <= 15000 else text[:15000]
    fname = f"{uuid.uuid4().hex}.mp3"
    fpath = AUDIO_DIR / fname
    tts = gTTS(safe_text)
    tts.save(str(fpath))
    with open(fpath, "rb") as f:
        data = f.read()
    return str(fpath), data

# ----------------- RAG retrieval -----------------
def retrieve_top_chunks(question: str, n_results: int = 3):
    try:
        q_emb = embed_model.encode([question]).tolist()[0]
        res = collection.query(query_embeddings=[q_emb], n_results=n_results)
        docs = res.get("documents", [[]])[0]
        return docs
    except Exception:
        try:
            res = collection.query(query_texts=[question], n_results=n_results)
            docs = res.get("documents", [[]])[0]
            return docs
        except Exception:
            return []

# ----------------- UI -----------------
st.title("AI Audiobook Generator")

# Instructions: upload, press Generate, then ask in Chat panel
st.markdown("Upload a single document (PDF/DOCX/TXT/Image). Text enrichment runs in the backend; the frontend shows only audio and RAG answers.")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Upload document (pdf, docx, txt, png, jpg)", type=["pdf","docx","txt","png","jpg","jpeg"], accept_multiple_files=False)
    initial_question = st.text_input("Initial question for RAG (optional)", placeholder="e.g. What is the objective of audiobook generator?")
with col2:
    generate_btn = st.button("Generate Audiobook & Index Document")

# When user clicks generate: extract -> backend enrich -> save chunks -> generate audio
if generate_btn:
    if not uploaded_file:
        st.warning("Please upload a document first.")
    else:
        fname = uploaded_file.name
        save_path = UPLOAD_DIR / fname
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        ext = fname.split(".")[-1].lower()
        if ext == "pdf":
            raw_text = extract_text_pdf(str(save_path))
        elif ext == "docx":
            raw_text = extract_text_docx(str(save_path))
        elif ext == "txt":
            raw_text = extract_text_txt(str(save_path))
        elif ext in ["png","jpg","jpeg"]:
            raw_text = extract_text_image(str(save_path))
        else:
            raw_text = ""

        if not raw_text.strip():
            st.error("No text extracted from document.")
        else:
            # --- Backend enrichment (Gemini) ONLY ---
            with st.spinner("Enriching text (backend)..."):
                enriched = gemini_enrich_text_for_audiobook(raw_text)

            # --- Save enriched chunks to Chroma ---
            chunks = chunk_text(enriched)
            if chunks:
                save_chunks_to_chroma(chunks, fname)

            # --- Generate audio from enriched text ---
            with st.spinner("Generating audio..."):
                audio_path, audio_bytes = generate_audio_and_bytes(enriched)
                # store in session for audio tab / download
                st.session_state["audio_path"] = audio_path
                st.session_state["audio_bytes"] = audio_bytes
                st.session_state["uploaded_filename"] = fname
                st.session_state["enriched_text_hidden"] = True  # for clarity; we don't show it

            st.success("Generated audiobook and indexed document for RAG (enrichment done in backend).")

# Left display: audio player & download
st.markdown("### Audiobook")
if st.session_state.get("audio_path"):
    st.audio(st.session_state["audio_path"], format="audio/mp3")
    st.download_button("Download Audio", data=st.session_state["audio_bytes"],
                       file_name=f"{st.session_state.get('uploaded_filename','audiobook')}.mp3",
                       mime="audio/mp3")
else:
    st.info("No audio yet. Upload and generate to create audio.")

# Right / Chat area
st.markdown("---")
st.header("Chat (RAG)")
question = st.text_input("Ask a question about the uploaded document", value=initial_question or "")
if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        # ensure DB has items
        try:
            total = collection.count()
        except Exception:
            total = 0
        if total == 0:
            st.error("No indexed document found. Upload & generate first.")
        else:
            with st.spinner("Retrieving relevant context..."):
                top_chunks = retrieve_top_chunks(question, n_results=4)
                context = "\n\n".join(top_chunks) if top_chunks else ""
            with st.spinner("Forming concise answer from context..."):
                answer = gemini_answer_from_context(question, context)
            st.markdown("**Answer (from document context):**")
            st.write(answer)
            # Optionally show which chunks were used (for debugging)
            with st.expander("Show retrieved context (for debugging)"):
                st.write(context)

# End
# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>AudioBook Generator Made By Shruti Oberoi | Powered by gTTS, chromadb, and Gemini</p>
</div>
""", unsafe_allow_html=True)