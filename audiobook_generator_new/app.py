# [file name]: app.py
# [file content begin]
import streamlit as st
from extractors import extract_text_from_file
from llm import enrich_text_for_audiobook
from tts import text_to_speech
from vector_db import SimpleVectorDB
from embeddings import get_embedding, split_text_into_chunks
from qa_chain import answer_question
import tempfile, os

# Initialize vector database
@st.cache_resource
def get_vector_db():
    return SimpleVectorDB()

vector_db = get_vector_db()

st.set_page_config(page_title='AudioBook Generator', layout='wide')
st.title('AudioBook Generator')

# Create tabs
tab1, tab2 = st.tabs(["📚 Generate Audiobook", "💬 Chat with Document"])

with tab1:
    st.markdown('Upload PDF, DOCX or TXT files. The app will extract text, optionally rewrite it using an LLM for audiobook-style narration, then convert to audio.')

    uploaded_files = st.file_uploader('Upload one or more documents', accept_multiple_files=True, type=['pdf','docx','txt'], key="uploader_1")

    model_option = st.selectbox('LLM Option', ['Fallback (local rewrite)', 'OpenAI (use API key from env)'])
    voice_rate = st.slider('Speech rate (pyttsx3)', min_value=100, max_value=300, value=150)
    audio_format = st.selectbox('Audio format', ['mp3','wav'])

    if uploaded_files:
        st.info(f'{len(uploaded_files)} file(s) ready for processing.')
        if st.button('Generate Audiobook'):
            all_text = []
            with st.spinner('Extracting text...'):
                for f in uploaded_files:
                    txt = extract_text_from_file(f)
                    all_text.append(txt)
            combined_text = '\n\n'.join(all_text)
            st.success('Extraction complete.')

            # Store embeddings in vector database
            with st.spinner('Storing document embeddings for Q&A...'):
                try:
                    # Clear previous documents
                    vector_db.clear_db()
                    
                    # Split text into chunks and create embeddings
                    chunks = split_text_into_chunks(combined_text)
                    for i, chunk in enumerate(chunks):
                        if chunk.strip():  # Only process non-empty chunks
                            embedding = get_embedding(chunk)
                            vector_db.add_document(chunk, embedding)
                    
                    st.success(f'Stored {len(chunks)} document chunks in database.')
                except Exception as e:
                    st.error(f'Error storing embeddings: {e}')

            with st.spinner('Enriching text for audiobook narration...'):
                enriched = enrich_text_for_audiobook(combined_text, use_openai=(model_option.startswith('OpenAI')))
            st.success('Enrichment complete.')

            st.text_area('Preview of enriched text (first 1000 chars)', enriched[:1000], height=200)

            with st.spinner('Generating audio...'):
                out_path = text_to_speech(enriched, rate=voice_rate, out_format=audio_format)
            st.success('Audio generation complete.')

            st.audio(out_path)
            with open(out_path, 'rb') as fh:
                st.download_button('Download Audio', fh, file_name=os.path.basename(out_path))
    else:
        st.info('Upload files to begin.')

with tab2:
    st.markdown('Chat with your uploaded documents. Ask questions about the content.')
    
    # Check if documents are loaded
    if not vector_db.documents:
        st.warning("Please upload and process documents in the 'Generate Audiobook' tab first.")
    else:
        st.success(f"Document database loaded with {len(vector_db.documents)} chunks.")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # React to user input
        if prompt := st.chat_input("Ask a question about your document..."):
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get answer
            with st.spinner("Searching documents..."):
                # Get query embedding
                query_embedding = get_embedding(prompt)
                # Search for relevant chunks
                relevant_chunks = vector_db.similarity_search(query_embedding, top_k=3)
                
                # Generate answer
                answer = answer_question(prompt, relevant_chunks)
            
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(answer)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Add clear chat button
        if st.button("Clear Chat History", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()
# [file content end]