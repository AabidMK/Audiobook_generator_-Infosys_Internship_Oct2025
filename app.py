import streamlit as st
import os
from typing import List, Tuple
import io 
import chromadb
from google import genai
import pypdf
from docx import Document
import time
import asyncio
import edge_tts
import tempfile
from typing import Optional

# --- IMPORTANT NOTE ---
# This line requires the 'rag_service.py' file to be present in the same directory.
try:
    from rag_service import run_query_search
except ImportError:
    st.error("Error: Could not find 'rag_service.py'. Please ensure it is saved in the same folder.")
    st.stop()
# ----------------------

# --- CONFIGURATION (Match your existing config) ---
EMBEDDING_MODEL = "gemini-embedding-001"
COLLECTION_NAME = "gemini_document_embeddings"
PERSIST_DIRECTORY = "my_vector_db"
CHUNK_SIZE = 1000

# --- EDGE TTS CONFIGURATION (New) ---
EDGE_TTS_VOICE = "en-US-AndrewNeural" 
OUTPUT_AUDIO_FORMAT = "mp3"
# ------------------------------------------------

# --- GLOBAL CLIENT INITIALIZATION ---
@st.cache_resource
def get_gemini_client():
    """Initializes and caches the Gemini client."""
    try:
        # Client reads GEMINI_API_KEY from environment variables
        client = genai.Client()
        return client
    except Exception as e:
        st.error(f"ERROR: Failed to initialize Gemini Client. Ensure GEMINI_API_KEY is set as an environment variable (e.g., export GEMINI_API_KEY='...')")
        st.stop()

# Initialize client globally
client = get_gemini_client()

# --- BACKEND FUNCTIONS: TEXT EXTRACTION & INDEXING ---

def extract_text_from_file(uploaded_file) -> str:
    """Step: Extraction - Extracts raw text content from uploaded files."""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    text = ""
    
    with st.status(f"Step 1 (Extraction): Extracting text from {uploaded_file.name}...", expanded=True) as status:
        try:
            if file_extension == "pdf":
                pdf_file = io.BytesIO(uploaded_file.getvalue())
                reader = pypdf.PdfReader(pdf_file)
                for page in reader.pages:
                    text += page.extract_text() or ""
            elif file_extension == "docx":
                doc_file = io.BytesIO(uploaded_file.getvalue())
                document = Document(doc_file)
                for paragraph in document.paragraphs:
                    text += paragraph.text + "\n"
            elif file_extension == "txt":
                text = uploaded_file.getvalue().decode("utf-8")
            else:
                status.error(f"Unsupported file type: {file_extension}. Only PDF, DOCX, and TXT are supported.")
                return ""
            
            status.update(label="Step 1 (Extraction) complete: Text extracted successfully!", state="complete", expanded=False)
            return text
        
        except Exception as e:
            status.error(f"Error extracting text: {e}")
            return ""

def chunk_and_embed_text(text: str, client: genai.Client):
    """Steps: Chunking, Embeddings, and Vector DB (Chroma) indexing."""
    
    if not text:
        return None

    # Simple Chunking Logic
    chunks = []
    segments = text.split('\n\n')
    current_chunk = ""
    for segment in segments:
        if len(current_chunk) + len(segment) + 2 > CHUNK_SIZE:
            if current_chunk: chunks.append(current_chunk.strip())
            current_chunk = segment
        else:
            current_chunk += "\n\n" + segment
            
    if current_chunk:
        chunks.append(current_chunk.strip())
    chunks = [c for c in chunks if len(c) > 50] 

    if not chunks: return None

    # 1. Embeddings
    with st.status(f"Step 2 (Embeddings/Vector DB): Generating embeddings and indexing {len(chunks)} chunks in Chroma...", expanded=True) as status:
        all_embeddings = []
        for i in range(0, len(chunks), 2000): 
            batch = chunks[i:i+2000]
            status.write(f"Generating embeddings for batch {i//2000 + 1}...")
            try:
                response = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=batch,
                )
                all_embeddings.extend(response.embeddings)
            except Exception as e:
                status.error(f"Embedding API Error: {e}")
                return None

        # 2. Saving to Vector DB (Chroma)
        status.write("Saving index to Vector DB (Chroma)...")
        db_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        try:
            db_client.delete_collection(name=COLLECTION_NAME)
        except:
            pass 

        collection = db_client.get_or_create_collection(name=COLLECTION_NAME)
        
        ids = [f"doc_{i}" for i in range(len(chunks))]
        embeddings = [e.values for e in all_embeddings] 
        
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
        )
        
        status.update(label=f"Step 2 (Embeddings/Vector DB) complete: {len(chunks)} chunks indexed in Chroma.", state="complete", expanded=False)
        return len(chunks)

# --- TTS GENERATION FUNCTION (UPDATED to use edge-tts) ---
def generate_audio_from_text(text: str, client: genai.Client) -> Optional[bytes]:
    """Step: Audio Generation (Edge TTS System) - Generates audio bytes from text using edge_tts."""
    
    # Truncate text for TTS if too long
    if len(text) > 4500:
        text = text[:4500] + "..."

    # Use a temporary file to save the MP3 before reading its bytes
    temp_filepath = None
    try:
        # 1. Create temporary file path
        with tempfile.NamedTemporaryFile(suffix=f".{OUTPUT_AUDIO_FORMAT}", delete=False) as tmp_file:
            temp_filepath = tmp_file.name

        # 2. Use Streamlit status for feedback
        with st.status(f"Step 3 (Edge TTS): Generating audio using {EDGE_TTS_VOICE}...", expanded=True) as status:
            
            # SSML Text Preparation
            ssml_text = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="{EDGE_TTS_VOICE}">
                    <prosody rate="+5%">
                        <break time="100ms"/>
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Define the asynchronous TTS task
            async def tts_generation_task():
                communicate = edge_tts.Communicate(ssml_text, EDGE_TTS_VOICE)
                await communicate.save(temp_filepath)
            
            status.write(f"Starting asynchronous Edge TTS generation with voice: {EDGE_TTS_VOICE}...")
            
            # Run the async task synchronously (necessary in Streamlit's execution environment)
            asyncio.run(tts_generation_task())
            
            status.write(f"Audio saved to temporary file. Reading {OUTPUT_AUDIO_FORMAT} bytes...")
            
            # 3. Read the generated MP3 file into memory
            with open(temp_filepath, 'rb') as f:
                audio_bytes = f.read()
            
            status.update(label=f"Step 3 (Edge TTS) complete: Audio generated ({OUTPUT_AUDIO_FORMAT})!", state="complete", expanded=False)
            return audio_bytes

    except Exception as e:
        st.error(f"Edge TTS Audio Generation Error: Failed to create MP3. Details: {e}")
        return None

    finally:
        # 4. Clean up the temporary file
        if temp_filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)

# --- MAIN PIPELINE FUNCTION ---

def process_document_and_generate_audio(uploaded_file, client: genai.Client):
    """
    Handles the end-to-end document processing: Extraction, Indexing, and Edge TTS.
    """
    
    # 1. Extraction
    raw_text = extract_text_from_file(uploaded_file)
    if not raw_text:
        return None, None

    # 2. Chunking, Embeddings, Vector DB
    chunk_count = chunk_and_embed_text(raw_text, client)
    if chunk_count is None:
        return None, None
    
    # 3. Audio Generation (Edge TTS)
    st.markdown("---") # Separator for clear process steps
    audio_bytes = generate_audio_from_text(raw_text, client)
    
    if audio_bytes is None:
        return None, None

    return audio_bytes, f"{uploaded_file.name.split('.')[0]}_audiobook.{OUTPUT_AUDIO_FORMAT}"


def answer_question_with_rag(query: str, client: genai.Client) -> str:
    """
    Step: RAG Pipeline - Executes the Advanced RAG Query, Retrieval, and Generation.
    """
    
    # The run_query_search function handles the Advanced RAG logic (expansion, retrieval, generation)
    answer, context_list = run_query_search(query, client)
    
    # Add context information to the chat response for transparency
    context_markdown = ""
    if context_list:
        context_markdown = f"\n\n---\n**Source Context Used (Total {len(context_list)} chunks retrieved via Advanced RAG):**\n"
        # We only show the context count here, as the full context can be too long for the chat window
        context_markdown += f"*(Context used for generation: {len(context_list)} chunks)*"

    return answer + context_markdown


# --- Frontend Layout (Streamlit) ---

st.set_page_config(
    layout="wide", 
    page_title="Advanced RAG & Audiobook Generator",
    initial_sidebar_state="collapsed"
)

# Use a container for better centering and layout
with st.container():
    st.markdown("""
        <div style='text-align: center; background-color: #004a77; padding: 10px; border-radius: 10px; color: white;'>
            <h1 style='margin: 0;'>📚 Advanced RAG & Audiobook Generator</h1>
            <p style='margin: 0; font-size: 1.1em;'>Integrated Document Processing with Gemini</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")


# 1. Create the two tabs
tab1, tab2 = st.tabs(["1. DOCUMENT PROCESSING (Edge TTS) 🎧", "2. ADVANCED RAG QUERY CHAT 💬"])

# --- TAB 1: Upload and Audio Generation ---
with tab1:
    col_upload, col_status = st.columns([1, 1])
    
    with col_upload:
        st.subheader("Document Uploader")
        st.markdown("**Core Workflow:** Extraction -> Embeddings -> Vector DB (Chroma) -> Edge TTS")
        
        uploaded_file = st.file_uploader(
            "Choose a Document (PDF, DOCX, TXT)", 
            type=["pdf", "docx", "txt"], 
            accept_multiple_files=False,
            key="file_uploader"
        )

        if uploaded_file is not None:
            if st.button("🚀 Start Full Pipeline", key="process_button", use_container_width=True):
                
                # Clear previous status messages
                st.session_state['file_processed'] = None
                
                # Call the main function
                audio_data, file_name = process_document_and_generate_audio(uploaded_file, client)
                
                if audio_data is not None:
                    st.session_state['file_processed'] = True
                    st.session_state['audio_data'] = audio_data
                    st.session_state['file_name'] = file_name
                    st.rerun() # Rerun to display download section cleanly

            
    with col_status:
        st.subheader("Processing Results")
        if uploaded_file is None:
            st.info("Please upload a document to begin processing the full pipeline.")
        elif 'file_processed' in st.session_state and st.session_state['file_processed']:
            st.success(f"✅ Document indexed and audio generated (Edge TTS System) in {OUTPUT_AUDIO_FORMAT.upper()} format.")
            st.markdown("### Edge TTS Audio Preview (MP3)")
            
            # IMPORTANT: Specify format="audio/mp3" for Streamlit player
            st.audio(st.session_state['audio_data'], format="audio/mp3")
            
            st.download_button(
                label=f"⬇️ Download Audiobook ({st.session_state['file_name']})",
                data=st.session_state['audio_data'],
                file_name=st.session_state['file_name'],
                mime="audio/mp3",
                use_container_width=True
            )
            st.success("The audio file is generated by the Edge TTS System (using the edge-tts library).")
            st.caption("If the audio player does not work, try downloading the MP3 file and playing it with a local player.")

# --- TAB 2: Document Q&A Chat ---
with tab2:
    st.header("Advanced RAG Query Pipeline")
    st.markdown("""
        This chat uses the **Advanced RAG Pipeline** (Query Expansion -> Retrieval -> Generation) 
        to find the most accurate answer from the document indexed in the first tab.
    """)
    
    
    # Check if a document has been indexed
    collection_ready = False
    try:
        db_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        if COLLECTION_NAME in [c.name for c in db_client.list_collections()]:
            collection_ready = db_client.get_collection(name=COLLECTION_NAME).count() > 0
    except Exception:
        pass # Ignore db connection errors for UI purposes

    if not collection_ready:
        st.warning("⚠️ No document is currently indexed. Please upload and process a file in the first tab to build the Vector DB.")
        
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm your **Advanced RAG** assistant. Ask me anything about the document you indexed."})

    # Display previous chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle new chat input
    if prompt := st.chat_input(
        "Ask a complex question about your document...", 
        disabled=not collection_ready
    ):
        # Add user message to history and display
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get RAG response
        with st.spinner("Executing Advanced RAG Pipeline (Query Expansion, Retrieval, Synthesis)..."):
            response = answer_question_with_rag(prompt, client)
        
        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)
            
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})