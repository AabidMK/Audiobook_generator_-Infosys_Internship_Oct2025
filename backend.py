import streamlit as st
import os
from gtts import gTTS
from extractor import extract_text_generic
from llm_enrich import enrich_text
import chromadb


# -----------------------------
# CREATE DIRECTORIES
# -----------------------------
OUTPUT_TEXT_DIR = "output_text"
OUTPUT_AUDIO_DIR = "audio_output"
os.makedirs(OUTPUT_TEXT_DIR, exist_ok=True)
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)


# -----------------------------
# CHROMA DB SIMPLE MODE (NO TORCH)
# -----------------------------
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="audiobook_text")


# Streamlit UI
st.set_page_config(page_title="Audiobook + Q/A", page_icon="🎧")

st.title("📚 AI Audiobook + Q/A System")

uploaded_file = st.file_uploader("Upload File", type=["pdf", "txt", "docx", "png", "jpg", "jpeg"])

if uploaded_file:
    filename = uploaded_file.name
    file_path = os.path.join(OUTPUT_TEXT_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("📄 File Uploaded Successfully")

    extracted_text = extract_text_generic(file_path)

    if extracted_text:
        st.info("⏳ Enriching text...")
        enriched_text = enrich_text(extracted_text)

        enriched_file = os.path.join(OUTPUT_TEXT_DIR, "enriched.txt")
        with open(enriched_file, "w", encoding="utf-8") as ef:
            ef.write(enriched_text)

        st.success("✨ Text Enriched Successfully!")

        # Store in Chroma
        collection.add(
            documents=[enriched_text],
            ids=[str(len(collection.get()['ids']))]
        )

        # AUDIOBOOK GENERATION
        st.info("🎶 Converting to Audiobook...")
        audio_path = os.path.join(OUTPUT_AUDIO_DIR, "audiobook.mp3")
        tts = gTTS(text=enriched_text, lang='en')
        tts.save(audio_path)

        st.audio(audio_path, format="audio/mp3")
        st.success("🎧 Audiobook Ready to Play!")


# QUESTION ANSWERING
st.subheader("💬 Ask Questions About the Document")
question = st.text_input("Ask something here:")

if question:
    try:
        results = collection.query(
            query_texts=[question],
            n_results=1
        )
        if results["documents"]:
            st.success("Answer:")
            st.write(results["documents"][0][0])
        else:
            st.error("No relevant answer found.")
    except Exception:
        st.error("Ask questions only after uploading a file!")
