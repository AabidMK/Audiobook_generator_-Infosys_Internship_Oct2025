import streamlit as st
import os
import tempfile
from datetime import datetime
from pathlib import Path

from extractor import extract_text
from llm_enrich import enrich_text
from tts import tts_synthesize
from embeddings import generate_embeddings, save_embeddings_csv
from vectordb_save import save_to_vectordb
from rag_langchain import get_vectorstore, query_with_sources

from dotenv import load_dotenv
load_dotenv()


st.set_page_config(page_title="AI Audiobook Generator", page_icon="🎧")

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- UI ----------
st.title("🎧 AI AudioBook Generator")
st.write("Upload a document, convert to audio, and ask questions from it (RAG).")

tab1, tab2 = st.tabs(["Upload & Generate", "Q&A Chat"])


# ============= TAB 1 : Upload & Generate ======================
with tab1:
    uploaded_file = st.file_uploader("Upload File", type=["pdf", "docx", "txt"])

    col1, col2 = st.columns(2)
    enhance = col1.checkbox("Use AI Text Enhancement (Gemini)", value=True)
    save_for_rag = col2.checkbox("Save for Q&A (RAG)", value=True)

    if uploaded_file:

        st.success(f"File uploaded: {uploaded_file.name}")

        if st.button("Generate Audiobook"):
            with st.spinner("Processing your file..."):

                # Save temp file
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, uploaded_file.name)

                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # STEP 1: Extract text
                extracted_text = extract_text(file_path)

                if not extracted_text or len(extracted_text) < 50:
                    st.error("Text extraction failed or too short")
                    st.stop()

                st.text_area("📄 Extracted Text (Preview)", extracted_text[:2000], height=200)

                # STEP 2: Gemini enrichment
                if enhance:
                    with st.spinner("Enhancing text with Gemini..."):
                        final_text = enrich_text(extracted_text)
                        st.success("Text Enhanced ✅")
                else:
                    final_text = extracted_text
                    st.info("Skipped AI Enhancement")

                # STEP 3: TTS
                with st.spinner("Generating Audio..."):
                    audio_path = tts_synthesize(final_text)

                if audio_path and os.path.exists(audio_path):
                    st.success("Audiobook Generated ✅")

                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()

                    st.audio(audio_bytes)
                    st.download_button(
                        "Download Audiobook",
                        audio_bytes,
                        file_name=f"{Path(uploaded_file.name).stem}.wav",
                        mime="audio/wav"
                    )

                # STEP 4: Save embeddings for RAG
                if save_for_rag:
                    with st.spinner("Saving embeddings..."):
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

                        chunks, vectors = generate_embeddings(
                            text=final_text,
                            model_name="all-MiniLM-L6-v2",
                            split_method="chunks",
                            chunk_size=400,
                            overlap=50
                        )

                        csv_path = f"./outputs/embeddings/{uploaded_file.name}_{timestamp}.csv"
                        os.makedirs("./outputs/embeddings", exist_ok=True)

                        save_embeddings_csv(chunks, vectors, Path(csv_path))

                        save_to_vectordb(
                            csv_path=csv_path,
                            collection_name="audiobook_embeddings",
                            persist_directory="./vectordb"
                        )

                        st.session_state.vectorstore = get_vectorstore(
                            collection_name="audiobook_embeddings",
                            persist_directory="./vectordb"
                        )

                        st.success("Saved to Vector DB for Q&A ✅")


# ============= TAB 2 : Q&A ======================================
with tab2:
    st.subheader("💬 Ask questions from your document")

    if st.session_state.vectorstore is None:
        st.warning("Upload and save a document first to enable Q&A.")
    else:
        user_question = st.text_input("Ask something:")

        if st.button("Ask"):
            if user_question:
                with st.spinner("Thinking..."):
                    answer, sources = query_with_sources(
                        st.session_state.vectorstore,
                        user_question
                    )

                st.markdown("### ✅ Answer")
                st.write(answer)

                if sources:
                    st.markdown("### 📌 Sources")
                    for s in sources:
                        st.write(f"- {s}")
