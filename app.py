"""
Streamlit Frontend for Audiobook Generator
Clean UI with document upload and chat interface
"""

import streamlit as st
import os
from pathlib import Path
import time
from text_extractor import TextExtractor
from text_enricher import TextEnricher
from tts_converter import TTSConverter
from embedding_generator import EmbeddingGenerator
from vector_db_store import store_embeddings_in_vector_db
from rag_responder import RAGResponder

# Page configuration
st.set_page_config(
    page_title="Audiobook Generator & Q&A",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean, high-contrast design
st.markdown("""
    <style>
    /* Global layout: pure white background, dark text */
    body {
        background-color: #ffffff;
        color: #111827;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .main {
        padding: 2rem;
        background-color: #ffffff;
    }
    header[data-testid="stHeader"] {
        background-color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background-color: #f9fafb;
        border-right: 1px solid #e5e7eb;
        color: #111827;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        background-color: #2563eb;
        color: #ffffff !important;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
    }

    /* File uploader: force white background and dark text */
    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        color: #111827 !important;
    }
    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #d1d5db !important;
    }
    [data-testid="stFileUploader"] * {
        color: #111827 !important;
    }
    /* Browse files button inside uploader */
    [data-testid="stFileUploader"] button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 500 !important;
    }

    /* Info / status panels (st.info, st.success, etc.) */
    div[role="alert"] {
        background-color: #eff6ff !important;  /* light blue */
        color: #111827 !important;             /* dark text */
        border: 1px solid #bfdbfe !important;
    }

    /* Chat bubbles */
    .chat-message {
        padding: 0.9rem 1rem;
        border-radius: 8px;
        margin: 0.4rem 0;
        border: 1px solid #d1d5db;
        font-size: 0.95rem;
        color: #111827;
        background-color: #ffffff;
    }
    .user-message {
        background-color: #dbeafe;
        margin-left: 15%;
    }
    .assistant-message {
        background-color: #e5e7eb;
        margin-right: 15%;
    }

    h1, h2, h3 {
        color: #111827;
        font-weight: 600;
    }
    .stProgress > div > div > div {
        background-color: #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'vector_db_ready' not in st.session_state:
    st.session_state.vector_db_ready = False
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = []


def process_document(uploaded_file, api_key):
    """Process uploaded document: extract, enrich, generate audio, and create embeddings"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Save uploaded file temporarily
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        file_path = temp_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        status_text.text("📄 Step 1/5: Extracting text from document...")
        progress_bar.progress(10)
        
        # Step 1: Extract text
        extractor = TextExtractor(output_folder="extracted_texts")
        extracted_text, extracted_file_path = extractor.process_file(str(file_path))
        
        status_text.text("✨ Step 2/5: Enriching text with AI...")
        progress_bar.progress(30)
        
        # Step 2: Enrich text
        enricher = TextEnricher(api_key=api_key, output_folder="enriched_texts")
        enriched_text, enriched_file_path = enricher.process_file(extracted_file_path)
        
        status_text.text("🎙️ Step 3/5: Generating audio...")
        progress_bar.progress(50)
        
        # Step 3: Generate audio
        converter = TTSConverter(output_folder="audio_output")
        audio_file = converter.convert_file(enriched_file_path)
        
        status_text.text("🔢 Step 4/5: Generating embeddings...")
        progress_bar.progress(70)
        
        # Step 4: Generate embeddings
        embedding_gen = EmbeddingGenerator(output_folder="embeddings")
        embedding_csv = embedding_gen.process_file(str(extracted_file_path))
        
        status_text.text("💾 Step 5/5: Storing embeddings in vector database...")
        progress_bar.progress(90)
        
        # Step 5: Store in vector DB
        store_embeddings_in_vector_db(
            str(embedding_csv),
            persist_directory="vector_store",
            collection_name="audiobook_embeddings",
            metadata={"source": uploaded_file.name, "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        
        # Clean up temp file
        if file_path.exists():
            file_path.unlink()
        
        return {
            "success": True,
            "audio_file": audio_file,
            "extracted_file": extracted_file_path,
            "enriched_file": enriched_file_path,
            "embedding_file": embedding_csv
        }
        
    except Exception as e:
        progress_bar.progress(0)
        status_text.text(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}


def main():
    """Main Streamlit app"""

    # Sidebar
    st.sidebar.title("Audiobook Generator")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Settings")

    # API Key input
    api_key = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv('GEMINI_API_KEY', ''),
        help="Enter your Google Gemini API key"
    )

    if not api_key:
        st.sidebar.warning("API key required for text enrichment and Q&A")

    # Main layout with two tabs
    st.title("Audiobook Generator & Document Q&A")
    st.caption("Upload a document once to generate audio and enable question answering.")

    upload_tab, chat_tab = st.tabs(["Upload & Audio", "Chat with Document"])

    # --- Upload & Audio tab ---
    with upload_tab:
        st.subheader("Upload a document")
        st.markdown("Upload a document to generate an audiobook and prepare it for Q&A.")

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif'],
            help="Supported formats: PDF, DOCX, TXT, images (JPG, PNG, etc.)"
        )

        if uploaded_file is not None:
            st.info(f"File: **{uploaded_file.name}** ({uploaded_file.size / 1024:.2f} KB)")

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("Process document", type="primary", use_container_width=True):
                    if not api_key:
                        st.error("Please enter your Gemini API key in the sidebar.")
                    else:
                        result = process_document(uploaded_file, api_key)

                        if result["success"]:
                            st.success("Document processed successfully.")

                            # Display results
                            st.markdown("#### Processing summary")
                            col_a, col_b, col_c = st.columns(3)

                            with col_a:
                                st.metric("Extracted text", "Complete")
                            with col_b:
                                st.metric("Enriched text", "Complete")
                            with col_c:
                                st.metric("Audio", "Generated")

                            # Audio playback & download
                            st.markdown("#### Generated audio")
                            audio_path = result["audio_file"]
                            if audio_path.exists():
                                with open(audio_path, "rb") as audio_file:
                                    audio_bytes = audio_file.read()
                                    st.audio(audio_bytes, format='audio/mp3')

                                    st.download_button(
                                        label="Download audio",
                                        data=audio_bytes,
                                        file_name=audio_path.name,
                                        mime="audio/mp3"
                                    )

                            # Update session state
                            st.session_state.vector_db_ready = True
                            st.session_state.processed_documents.append(uploaded_file.name)

                            st.info("You can now switch to the 'Chat with Document' tab to ask questions.")

            with col2:
                if st.button("Reset", use_container_width=True):
                    st.session_state.vector_db_ready = False
                    st.session_state.chat_history = []
                    st.rerun()

        else:
            st.info("Upload a PDF, DOCX, TXT, or image file to get started.")

    # --- Chat tab ---
    with chat_tab:
        st.subheader("Ask questions about your document")

        # Check if vector DB is ready
        if not st.session_state.vector_db_ready:
            st.warning("No documents processed yet. Please upload and process a document in the 'Upload & Audio' tab.")
            return

        if not api_key:
            st.error("Please enter your Gemini API key in the sidebar.")
            return

        st.markdown("#### Chat history")

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.chat_history):
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>Assistant:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)

        # Query input
        st.markdown("#### Ask a question")
        user_query = st.text_input(
            "Enter your question:",
            placeholder="For example: What is the main idea of this document?",
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([1, 5])
        with col1:
            ask_button = st.button("Ask", type="primary", use_container_width=True)
        with col2:
            clear_button = st.button("Clear chat", use_container_width=True)

        if clear_button:
            st.session_state.chat_history = []
            st.rerun()

        if ask_button and user_query:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_query
            })

            # Generate response
            with st.spinner("Generating answer based on your document..."):
                try:
                    responder = RAGResponder(
                        api_key=api_key,
                        persist_dir="vector_store",
                        collection_name="audiobook_embeddings"
                    )

                    result = responder.generate_response(user_query, top_k=5)
                    response = result['response']

                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })

                    st.rerun()

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    st.error(error_msg)
                    st.rerun()


if __name__ == "__main__":
    main()

