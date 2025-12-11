import streamlit as st
import os
import sys
import subprocess
import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv

# Import your existing modules
# We wrap these in try-except to prevent the app from crashing if dependencies are missing
try:
    from text_extraction import extract_and_save
    from text_enrichment import enrich_text
    from piper_tts import generate_and_save_audio
except ImportError as e:
    st.error(f"Error importing local modules: {e}")
    st.stop()

# Load Environment Variables
load_dotenv()

# Page Config
st.set_page_config(page_title="DocuVoice & Chat", layout="wide", page_icon="🎙️")

# --- HELPER: GET AVAILABLE GEMINI MODEL ---
def get_best_available_model():
    """
    Dynamically fetches the best available model for the API key 
    to avoid 404 errors with hardcoded names.
    """
    try:
        # List all models available to the API key
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            return "models/gemini-1.5-flash" # Fallback if list is empty

        # Priority 1: Prefer Flash (Fast & Cheap)
        for model in available_models:
            if "flash" in model.lower():
                return model
        
        # Priority 2: Prefer Pro (Standard)
        for model in available_models:
            if "pro" in model.lower():
                return model
                
        # Priority 3: First available valid model
        return available_models[0]

    except Exception as e:
        # Fallback if list_models fails (e.g. strict permission scopes)
        return "models/gemini-1.5-flash"

# --- HELPER: RAG QUERY FUNCTION ---
def get_rag_response(user_question):
    """
    Returns (response_text, retrieved_chunks_list)
    """
    try:
        # 1. Setup API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "❌ Error: GEMINI_API_KEY not found.", []
        genai.configure(api_key=api_key)

        # 2. Connect to DB
        client = chromadb.PersistentClient(path="my_vectordb")
        collection = client.get_collection(name="document_chunks")

        # 3. Embed Query (same model as ingestion)
        embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = embed_model.encode([user_question]).tolist()

        # 4. Search (Similarity Search)
        results = collection.query(query_embeddings=query_embedding, n_results=5)
        retrieved_chunks = results['documents'][0]

        if not retrieved_chunks:
            return "I couldn't find any relevant information in the uploaded documents.", []

        # 5. Generate Answer (Augment & Generate)
        context_block = "\n\n".join(retrieved_chunks)
        rag_prompt = f"""
        You are a helpful assistant. Use the provided Context to answer the User's Question.
        If the answer is not in the context, strictly state "I cannot answer this based on the provided documents."
        
        Context:
        {context_block}
        
        User Question:
        {user_question}
        """
        
        # Dynamic Model Selection to prevent 404s
        model_name = get_best_available_model()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(rag_prompt)
        return response.text, retrieved_chunks

    except Exception as e:
        return f"Error during RAG query: {str(e)}", []

# --- HELPER: CHECK IF DATA EXISTS IN CHROMA ---
def check_if_stored_in_db(source_identifier):
    try:
        client = chromadb.PersistentClient(path="my_vectordb")
        # Use get_or_create to avoid errors if it doesn't exist yet
        collection = client.get_or_create_collection(name="document_chunks")
        
        # Query for any document where metadata 'source' matches our file
        # Note: store_in_db.py saves the full 'csv_path' as the source.
        result = collection.get(where={"source": source_identifier}, limit=1)
        
        # If we found at least one ID, it's already stored
        return len(result['ids']) > 0
    except Exception as e:
        print(f"Error checking DB: {e}")
        return False

# --- MAIN UI ---
st.title("🎙️ DocuVoice: Audio & Chat")

# Create Tabs
tab1, tab2 = st.tabs(["📂 Upload & Process", "💬 Chat with Document"])

# ==========================================
# TAB 1: UPLOAD, AUDIO, AND EMBEDDING
# ==========================================
with tab1:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a file (PDF, DOCX, Image)", type=['pdf', 'docx', 'txt', 'png', 'jpg'])

    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_filename = f"temp_{uploaded_file.name}"
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File '{uploaded_file.name}' uploaded successfully.")

        if st.button("🚀 Process Document (Generate Audio & Embed)"):
            status_container = st.container()
            
            with status_container:
                
                # --- STEP 1: TEXT EXTRACTION ---
                with st.spinner("Step 1/4: Checking Extraction..."):
                    base_name = os.path.splitext(temp_filename)[0]
                    expected_extracted_path = f"{base_name}_extracted.txt"
                    
                    if os.path.exists(expected_extracted_path):
                        st.info(f"📂 Found existing extracted file: '{expected_extracted_path}'. Skipping extraction.")
                        extracted_txt_path = expected_extracted_path
                    else:
                        extracted_txt_path = extract_and_save(temp_filename)
                        if not extracted_txt_path or not os.path.exists(extracted_txt_path):
                            st.error("Extraction failed.")
                            st.stop()
                        st.toast("✅ Text Extracted")

                # --- STEP 2: AUDIO GENERATION PIPELINE ---
                with st.spinner("Step 2/4: Checking Audio Pipeline..."):
                    # 2a. Check Enrichment
                    expected_enriched_path = os.path.splitext(extracted_txt_path)[0] + "_audiobook.txt"
                    
                    if os.path.exists(expected_enriched_path):
                        st.info(f"📂 Found existing enriched text: '{expected_enriched_path}'. Skipping enrichment.")
                        enriched_path = expected_enriched_path
                    else:
                        enriched_path = enrich_text(extracted_txt_path)
                    
                    if not enriched_path:
                        st.error("Text Enrichment Failed")
                        st.stop()

                    # 2b. Check TTS
                    audio_filename = f"audio_{uploaded_file.name}.wav"
                    
                    if os.path.exists(audio_filename):
                        st.info(f"📂 Found existing audio: '{audio_filename}'. Skipping generation.")
                        success = True
                    else:
                        with open(enriched_path, "r", encoding="utf-8") as f:
                            text_to_speak = f.read()
                        success = generate_and_save_audio(text_to_speak, audio_filename)
                    
                    if success:
                        st.audio(audio_filename, format='audio/wav')
                        st.toast("✅ Audio Ready")
                        with open(audio_filename, "rb") as f:
                            st.download_button("⬇️ Download Audio", f, file_name=audio_filename)
                    else:
                        st.error("Audio Generation Failed")

                # --- STEP 3: EMBEDDING PIPELINE ---
                with st.spinner("Step 3/4: Checking Embeddings..."):
                    # Predict the CSV name based on embed.py logic
                    # embed.py logic: base_name, _ = os.path.splitext(input_path) -> f"{base_name}_chunked_embeddings.csv"
                    base_name_extracted = os.path.splitext(extracted_txt_path)[0]
                    expected_csv_path = f"{base_name_extracted}_chunked_embeddings.csv"
                    
                    if os.path.exists(expected_csv_path):
                        st.info(f"📂 Found existing embeddings CSV: '{expected_csv_path}'. Skipping embedding.")
                    else:
                        try:
                            subprocess.run([sys.executable, "embed.py", extracted_txt_path], check=True)
                            st.toast("✅ Embeddings Created")
                        except subprocess.CalledProcessError as e:
                            st.error(f"Error running embed.py: {e}")
                            st.stop()

                # --- STEP 4: STORING IN DB ---
                with st.spinner("Step 4/4: Checking Vector DB..."):
                    if os.path.exists(expected_csv_path):
                        # Check if this specific CSV source is already in the DB
                        if check_if_stored_in_db(expected_csv_path):
                            st.info("📂 Data already exists in Vector DB. Skipping storage.")
                            st.success("🎉 Process Complete (Cached Results Used)")
                        else:
                            try:
                                subprocess.run([sys.executable, "store_in_db.py", expected_csv_path], check=True)
                                st.toast("✅ Stored in Vector DB")
                                st.success("🎉 All processing complete! You can now go to the Chat tab.")
                            except subprocess.CalledProcessError as e:
                                st.error(f"Error running store_in_db.py: {e}")
                    else:
                        st.error(f"Could not find embedding CSV to store: {expected_csv_path}")

# ==========================================
# TAB 2: CHAT INTERFACE
# ==========================================
with tab2:
    st.header("💬 Chat with your Data")
    
    # --- CSS Fix to enforce sticky bottom input ---
    st.markdown("""
        <style>
            /* Force the chat input widget to be fixed at the bottom */
            [data-testid="stChatInput"] {
                position: fixed !important;
                bottom: 0 !important;
                left: 0 !important;
                right: 0 !important;
                z-index: 9999 !important;
                background-color: var(--background-color); /* Uses the theme's background color */
                padding-bottom: 20px;
                padding-top: 10px;
            }
            
            /* Add bottom padding to the main content area so the last message isn't hidden behind the text box */
            .main .block-container {
                padding-bottom: 120px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask a question about your document..."):
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_text, sources = get_rag_response(prompt)
                
                # Show the main answer
                st.markdown(response_text)
                
                # Show the sources in an expander
                if sources:
                    with st.expander("🔍 View Top 5 Source Chunks"):
                        for i, chunk in enumerate(sources):
                            st.markdown(f"**Chunk {i+1}**")
                            st.caption(chunk)
                            st.divider()
        
        # Save to history (we only save the text answer to keep history clean)
        st.session_state.messages.append({"role": "assistant", "content": response_text})