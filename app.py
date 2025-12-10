"""
AI Audiobook Generator - Single Page Streamlit App

Flow:
1) Upload document (PDF / DOCX / TXT / IMAGE)
2) Extract text  -> work/extracted_output.txt
3) Enrich text   -> work/enriched_output.txt
4) Generate TTS  -> work/audiobook_output.wav
5) Generate embeddings CSV + store in Chroma
6) Chat (RAG) over stored document
"""

import streamlit as st
import tempfile
import os
import subprocess
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------
# 🔧 Basic page config
# ---------------------------------------------------------------------
st.set_page_config(page_title="AI Audiobook Generator", layout="wide")

# ---------------------------------------------------------------------
# 🌗 Theme toggle
# ---------------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

dark_mode = st.toggle(
    "🌗 Dark / Light Mode",
    value=(st.session_state.theme == "dark"),
    key="theme_toggle",
    help="Switch between dark and light UI",
)
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

if theme == "dark":
    BG = "#050608"
    CARD = "#111827"
    TEXT = "#f9fafb"
    ACCENT = "#3b82f6"
    CHAT_BG = "#020617"
else:
    BG = "#f3f4f6"
    CARD = "#ffffff"
    TEXT = "#020617"
    ACCENT = "#2563eb"
    CHAT_BG = "#e5e7eb"

# ---------------------------------------------------------------------
# 🎨 Global CSS
# ---------------------------------------------------------------------
st.markdown(
    f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-color: {BG};
    color: {TEXT};
}}

.app-title {{
    text-align: center;
    font-size: 42px;
    font-weight: 700;
    color: {TEXT};
    margin-top: 0.2rem;
    margin-bottom: 1rem;
}}

.upload-section {{
    background-color: {CARD};
    padding: 1.5rem;
    border-radius: 0.9rem;
    box-shadow: 0 0 18px rgba(0,0,0,0.35);
    margin-bottom: 1.2rem;
}}

.primary-btn > button {{
    background-color: {ACCENT} !important;
    color: #ffffff !important;
    width: 100%;
    padding: 0.7rem 1rem !important;
    border-radius: 0.6rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}}

.card {{
    background-color: {CARD};
    padding: 1.3rem;
    border-radius: 0.9rem;
    color: {TEXT};
    box-shadow: 0 0 16px rgba(0,0,0,0.25);
    min-height: 430px;
}}

.card h3 {{
    margin-top: 0;
}}

.chat-box {{
    height: 260px;
    overflow-y: auto;
    padding: 0.7rem;
    background-color: {CHAT_BG};
    border-radius: 0.7rem;
    margin-bottom: 0.6rem;
    font-size: 0.95rem;
}}

.chat-msg-user {{
    color: {TEXT};
    margin-bottom: 0.4rem;
}}

.chat-msg-ai {{
    color: {TEXT};
    margin-bottom: 0.8rem;
}}

.suggestion-pill > button {{
    width: 100%;
    border-radius: 999px !important;
    padding: 0.25rem 0.6rem !important;
    font-size: 0.85rem !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# 📦 Imports from your pipeline (with fallbacks)
# ---------------------------------------------------------------------
try:
    from pipeline.document_parser import DocumentParser
except Exception:
    DocumentParser = None

try:
    from pipeline.text_enrichment import TextEnrichment
except Exception:
    TextEnrichment = None

try:
    from pipeline.text_to_speech import TextToSpeech
except Exception:
    TextToSpeech = None

try:
    import pipeline.generate_embeddings as generate_embeddings_module
except Exception:
    generate_embeddings_module = None

try:
    import pipeline.store_embeddings_chroma as store_chroma_module
except Exception:
    store_chroma_module = None

try:
    import pipeline.rag_query as rag_query_module
except Exception:
    rag_query_module = None

# ---------------------------------------------------------------------
# 📂 Paths / working directory
# ---------------------------------------------------------------------
BASE_DIR = Path.cwd()
WORK_DIR = BASE_DIR / "work"
WORK_DIR.mkdir(exist_ok=True)

EXTRACTED_PATH = WORK_DIR / "extracted_output.txt"
ENRICHED_PATH = WORK_DIR / "enriched_output.txt"
AUDIO_PATH = WORK_DIR / "audiobook_output.wav"
EMBEDDINGS_CSV = WORK_DIR / "text_embeddings.csv"

# ---------------------------------------------------------------------
# 🔧 Helper functions wrapping your existing modules / scripts
# ---------------------------------------------------------------------
def run_document_parser_local(file_path: str) -> Optional[str]:
    """Use DocumentParser if available, else run your standalone script."""
    if DocumentParser:
        parser = DocumentParser()
        text = parser.parse(file_path)
        if text:
            parser.save(text, str(EXTRACTED_PATH.with_suffix("")), fmt="txt")
            return str(EXTRACTED_PATH)
        return None

    candidates = [
        BASE_DIR / "pipeline" / "audiobook.py",
        BASE_DIR / "src" / "document_parser.py",
        BASE_DIR / "document_parser.py",
    ]
    for c in candidates:
        if c.exists():
            try:
                subprocess.run(
                    [os.environ.get("PYTHON", "python"), str(c), file_path],
                    check=True,
                )
            except subprocess.CalledProcessError:
                subprocess.run(
                    [os.environ.get("PYTHON", "python"), str(c)], check=False
                )
            if EXTRACTED_PATH.exists():
                return str(EXTRACTED_PATH)
    return None


def run_text_enrichment_local(input_path: str, output_path: str) -> bool:
    if TextEnrichment:
        enr = TextEnrichment()
        return bool(enr.process_file(input_path, output_path))

    script_paths = [
        BASE_DIR / "src" / "text_enrichment.py",
        BASE_DIR / "text_enrichment.py",
        BASE_DIR / "pipeline" / "audiobook.py",
    ]
    for s in script_paths:
        if s.exists():
            try:
                subprocess.run(
                    [os.environ.get("PYTHON", "python"), str(s)],
                    check=True,
                )
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(
                        [
                            os.environ.get("PYTHON", "python"),
                            str(s),
                            input_path,
                            output_path,
                        ],
                        check=True,
                    )
                except Exception:
                    pass
            if Path(output_path).exists():
                return True
    return False


def run_tts_local(input_path: str, output_path: str) -> bool:
    if TextToSpeech:
        tts = TextToSpeech()
        return bool(tts.process_file(input_path, output_path))

    script_paths = [
        BASE_DIR / "src" / "text_to_speech.py",
        BASE_DIR / "text_to_speech.py",
        BASE_DIR / "pipeline" / "audiobook.py",
    ]
    for s in script_paths:
        if s.exists():
            try:
                subprocess.run(
                    [os.environ.get("PYTHON", "python"), str(s)],
                    check=True,
                )
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(
                        [
                            os.environ.get("PYTHON", "python"),
                            str(s),
                            input_path,
                            output_path,
                        ],
                        check=True,
                    )
                except Exception:
                    pass
            if Path(output_path).exists():
                return True
    return False


def run_generate_embeddings_local(input_path: str, csv_out: str) -> bool:
    """Generate embeddings CSV from extracted text."""
    if generate_embeddings_module and hasattr(
        generate_embeddings_module, "generate_embeddings"
    ):
        try:
            generate_embeddings_module.generate_embeddings(
                str(input_path), str(csv_out)
            )
            return Path(csv_out).exists()
        except Exception as e:
            st.warning(f"generate_embeddings failed: {e}")

    candidates = [
        BASE_DIR / "pipeline" / "generate_embeddings.py",
        BASE_DIR / "generate_embeddings.py",
    ]
    for c in candidates:
        if c.exists():
            try:
                subprocess.run(
                    [os.environ.get("PYTHON", "python"), str(c), str(input_path), str(csv_out)],
                    check=True,
                )
            except Exception:
                subprocess.run(
                    [os.environ.get("PYTHON", "python"), str(c)],
                    check=False,
                )
            if Path(csv_out).exists():
                return True
    return False


def store_embeddings_to_chroma(csv_path: str) -> bool:
    """Store CSV embeddings into ChromaDB."""
    if store_chroma_module and hasattr(store_chroma_module, "store_csv_to_chroma"):
        try:
            store_chroma_module.store_csv_to_chroma(csv_path)
            return True
        except Exception as e:
            st.warning(f"store_embeddings_chroma failed: {e}")

    c = BASE_DIR / "pipeline" / "store_embeddings_chroma.py"
    if c.exists():
        try:
            subprocess.run(
                [os.environ.get("PYTHON", "python"), str(c), str(csv_path)],
                check=True,
            )
            return True
        except Exception:
            pass
    return False


def rag_answer(query: str, top_k: int = 5) -> str:
    """Ask a RAG question over Chroma + Gemini."""
    if rag_query_module and hasattr(rag_query_module, "answer_query"):
        try:
            return rag_query_module.answer_query(query, top_k=top_k)
        except Exception as e:
            return f"RAG error: {e}"

    c = BASE_DIR / "pipeline" / "rag_query.py"
    if c.exists():
        try:
            out = subprocess.check_output(
                [os.environ.get("PYTHON", "python"), str(c), query, str(top_k)],
                stderr=subprocess.STDOUT,
                text=True,
            )
            return out
        except subprocess.CalledProcessError as e:
            return f"RAG script error:\n{e.output}"
    return "RAG backend not found. Please implement pipeline.rag_query.answer_query()."


# ---------------------------------------------------------------------
# 🧠 Chat history state
# ---------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------------------------
# 🧾 TITLE
# ---------------------------------------------------------------------
st.markdown('<div class="app-title">📚 AI Audiobook Generator</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 📤 Upload section (top card)
# ---------------------------------------------------------------------
with st.container():
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload document (.pdf, .docx, .txt, .png, .jpg, .jpeg)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
    )

    initial_question = st.text_input(
        "Initial question for RAG (optional)",
        placeholder="e.g. What is the main idea of this document?",
    )

    opt_col1, opt_col2, opt_col3 = st.columns([1.2, 1, 1])
    with opt_col1:
        generate_audio = st.checkbox("🎧 Generate audiobook", value=True)
    with opt_col2:
        save_embeddings = st.checkbox("🧠 Store embeddings (Chroma)", value=True)
    with opt_col3:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        run_btn = st.button(
            "Generate Audiobook & Answer",
            key="main_generate",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 🚀 Run pipeline when button clicked
# ---------------------------------------------------------------------
if run_btn:
    if not uploaded_file:
        st.warning("Please upload a document first.")
    else:
        # Save upload to a temp file
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}")
        tfile.write(uploaded_file.read())
        tfile.flush()
        tfile.close()
        uploaded_path = tfile.name
        st.info(f"📂 File saved to: `{uploaded_path}`")

        # 1. Extract
        with st.spinner("📄 Extracting text from document..."):
            extracted = run_document_parser_local(uploaded_path)
        if not extracted:
            st.error("Text extraction failed. Check logs / terminal.")
        else:
            st.success(f"✅ Extracted text saved to `{EXTRACTED_PATH}`")

        # 2. Enrich
        if extracted:
            with st.spinner("✨ Enriching text using Gemini..."):
                ok = run_text_enrichment_local(str(EXTRACTED_PATH), str(ENRICHED_PATH))
            if ok and ENRICHED_PATH.exists():
                st.success(f"✅ Enriched text saved to `{ENRICHED_PATH}`")
            else:
                st.error("Text enrichment failed.")

        # 3. TTS
        if generate_audio and ENRICHED_PATH.exists():
            with st.spinner("🔊 Generating audiobook (TTS)..."):
                ok = run_tts_local(str(ENRICHED_PATH), str(AUDIO_PATH))
            if ok and AUDIO_PATH.exists():
                st.success("✅ Audiobook audio generated.")
            else:
                st.error("TTS generation failed. See logs.")

        # 4. Embeddings + Chroma
        if save_embeddings and EXTRACTED_PATH.exists():
            with st.spinner("🧠 Generating embeddings CSV..."):
                csv_ok = run_generate_embeddings_local(str(EXTRACTED_PATH), str(EMBEDDINGS_CSV))
            if csv_ok and EMBEDDINGS_CSV.exists():
                st.success(f"✅ Embeddings CSV created at `{EMBEDDINGS_CSV}`")
                with st.spinner("📦 Storing embeddings into Chroma DB..."):
                    stored = store_embeddings_to_chroma(str(EMBEDDINGS_CSV))
                if stored:
                    st.success("✅ Embeddings stored in ChromaDB.")
                else:
                    st.warning("Could not store embeddings automatically. Check vector DB script.")
            else:
                st.error("Embedding generation failed.")

        # 5. Optional initial RAG question
        if initial_question.strip():
            with st.spinner("💬 Running initial RAG query..."):
                ans = rag_answer(initial_question)
            st.session_state.chat_history.append(f"**You:** {initial_question}")
            st.session_state.chat_history.append(f"**AI:** {ans}")
            st.success("✅ Initial answer added to chat below.")

# ---------------------------------------------------------------------
# 🎛️ Main two-column layout: Audiobook + Chat
# ---------------------------------------------------------------------
col_audio, col_chat = st.columns(2)

# ----- Left: Audiobook card -----
with col_audio:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🎧 Audiobook")

    if AUDIO_PATH.exists():
        st.audio(str(AUDIO_PATH))
        st.download_button(
            "Download Audiobook",
            data=open(AUDIO_PATH, "rb").read(),
            file_name="audiobook_output.wav",
            mime="audio/wav",
        )
        if ENRICHED_PATH.exists():
            with st.expander("Preview enriched text"):
                st.write(ENRICHED_PATH.read_text(encoding="utf-8")[:1500] + "...")
    else:
        st.write("No audio yet. Upload a document and click **Generate Audiobook & Answer**.")

    st.markdown("</div>", unsafe_allow_html=True)

# ----- Right: Chat / RAG card -----
with col_chat:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 💬 Chat (RAG)")

    # Suggested question pills
    st.markdown("**💡 Suggested questions:**")
    suggs = [
        "What is the main idea of the document?",
        "Summarize this in 3 sentences.",
        "Explain any complex terms in this text.",
    ]
    sugg_cols = st.columns(len(suggs))
    for i, q in enumerate(suggs):
        with sugg_cols[i]:
            if st.button(q, key=f"sugg_{i}", help="Ask this question", type="secondary"):
                st.session_state.chat_history.append(f"**You:** {q}")
                ans = rag_answer(q)
                st.session_state.chat_history.append(f"**AI:** {ans}")
                st.experimental_rerun()

    # Chat history
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            st.markdown(msg, unsafe_allow_html=True)
    else:
        st.write("Start a conversation about your document here.")
    st.markdown("</div>", unsafe_allow_html=True)

    # User input
    user_input = st.text_input("Ask a follow-up question…", key="chat_input")

    ask_col1, ask_col2 = st.columns([4, 1])
    with ask_col2:
        if st.button("Ask", key="ask_btn"):
            if user_input.strip():
                st.session_state.chat_history.append(f"**You:** {user_input}")
                ans = rag_answer(user_input)
                st.session_state.chat_history.append(f"**AI:** {ans}")
                st.experimental_rerun()
            else:
                st.warning("Type a question before pressing **Ask**.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 📌 Sidebar: pipeline status
# ---------------------------------------------------------------------
st.sidebar.header("📌 Pipeline Status")
st.sidebar.write(f"**Working dir:** `{WORK_DIR}`")

st.sidebar.write("**1️⃣ Uploaded file:**")
st.sidebar.success("Yes" if uploaded_file else "No")

st.sidebar.write("**2️⃣ Extracted text file:**")
st.sidebar.success("Ready" if EXTRACTED_PATH.exists() else "Not yet")

st.sidebar.write("**3️⃣ Enriched text file:**")
st.sidebar.success("Ready" if ENRICHED_PATH.exists() else "Not yet")

st.sidebar.write("**4️⃣ Audiobook audio:**")
st.sidebar.success("Ready" if AUDIO_PATH.exists() else "Not yet")

st.sidebar.write("**5️⃣ Embeddings CSV:**")
st.sidebar.success("Ready" if EMBEDDINGS_CSV.exists() else "Not yet")
