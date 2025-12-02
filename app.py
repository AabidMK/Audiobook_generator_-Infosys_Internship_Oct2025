import os
import streamlit as st
from dotenv import load_dotenv
import numpy as np
import pickle
import faiss 
import pyttsx3 

try:
    
    import faiss
except ImportError:
    
    try:
        import faiss_cpu as faiss
    except ImportError:
        st.error("FAISS is not installed. Please install 'faiss-cpu' or 'faiss-gpu'.")
        st.stop()
    

load_dotenv()

from sentence_transformers import SentenceTransformer

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

from openai import APIError, AuthenticationError 


EMBED_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "gpt-4o-mini"

FAISS_INDEX = "faiss_index.bin"
FAISS_META = "faiss_metadata.pkl"

AUDIO_FILE = "generated_audio.mp3"



@st.cache_resource
def get_embedder():
    """Loads the Sentence Transformer model only once."""
    try:
        embedder = SentenceTransformer(EMBED_MODEL)
        return embedder
    except Exception as e:
        st.error(f"Error loading Sentence Transformer: {e}. Ensure sentence-transformers is installed.")
        st.stop()


@st.cache_resource
def load_faiss_knowledge_base():
    """Loads FAISS index and metadata from disk only once."""
    if not (os.path.exists(FAISS_INDEX) and os.path.exists(FAISS_META)):
        return None, None
    
    try:
        index = faiss.read_index(FAISS_INDEX)
        with open(FAISS_META, "rb") as f:
            metadata = pickle.load(f)
        return index, metadata
    except Exception as e:
        st.error(f"Failed to load FAISS files. Please re-upload the PDF. Error: {e}")
        return None, None

def check_openai_api_key():
    """Checks for the presence of the OpenAI API key (required for RAG/LLM only)."""
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Error: OPENAI_API_KEY is missing. Cannot run LLM queries.")
        return False
    return True




st.set_page_config(layout="wide") 
st.title(" PDF → Audio + RAG Chat Assistant")

tab1, tab2 = st.tabs([" Upload Document", " Chat with PDF"])




with tab1:

    st.header("Upload Document & Generate Audio")
    st.markdown("Upload a PDF file to build the knowledge base for the Q&A tab and generate a preliminary audiobook file. The audio generation now uses the free, local `pyttsx3` library.")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_uploader")

    if uploaded_file is not None:
        
        
        load_faiss_knowledge_base.clear()
        
        if os.path.exists(FAISS_INDEX) and os.path.exists(FAISS_META):
            st.warning("Index files exist. Uploading a new PDF will overwrite the existing knowledge base.")
        
        with st.spinner("Processing document... This may take a moment."):
            
            st.success("PDF uploaded successfully! Starting text processing.")

            pdf_path = "uploaded.pdf"
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

            
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()

            st.info("Extracting & splitting text...")

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            chunks = splitter.split_documents(docs) 
            text_chunks = [c.page_content for c in chunks]

            
            st.info(f"Creating embeddings and index using {EMBED_MODEL}...")

            
            embedder = get_embedder()
            
            embeddings = embedder.encode(text_chunks)
            embeddings = np.array(embeddings).astype("float32")

            if embeddings.shape[0] == 0:
                st.error("Could not extract any meaningful text from the PDF. Check the document format.")
                st.stop()
                
            
            index = faiss.IndexFlatL2(embeddings.shape[1])
            index.add(embeddings)

            faiss.write_index(index, FAISS_INDEX)

            
            with open(FAISS_META, "wb") as f:
                pickle.dump({"chunks": text_chunks}, f)

            st.success(f" FAISS vector DB built and saved to {FAISS_INDEX} / {FAISS_META}!")
            
            
            load_faiss_knowledge_base.clear()
            load_faiss_knowledge_base()

            
            st.info("Generating audio locally using pyttsx3 (limited to first 10 chunks for speed)...")
                    
            try:
                
                full_text = "\n".join(text_chunks[:10])
                
                if not full_text:
                    st.warning("Extracted text is empty. Skipping audio generation.")
                else:
                    engine = pyttsx3.init()
                    
                    
                    engine.save_to_file(full_text, AUDIO_FILE)
                    
                    
                    engine.runAndWait()

                    if os.path.exists(AUDIO_FILE) and os.path.getsize(AUDIO_FILE) > 0:
                        st.success("🎉 Audio generated successfully using pyttsx3!")

                        st.audio(AUDIO_FILE, format="audio/mpeg")
                        
                        st.download_button(
                            label="⬇ Download Audio",
                            data=open(AUDIO_FILE, "rb"),
                            file_name="document_audio.mp3",
                            mime="audio/mpeg"
                        )
                    else:
                        st.error("pyttsx3 failed to generate a valid audio file. Ensure the library and a system TTS engine are configured correctly.")
                        
            except Exception as e:
                
                st.error(f"TTS Audio Generation Failed. Please ensure pyttsx3 is installed (`pip install pyttsx3`) and your system has a working TTS engine (e.g., SAPI on Windows, eSpeak on Linux). Full Error: {e}")
                
            st.markdown("---")
            st.markdown("You can now switch to the *' Chat with PDF'* tab.")




with tab2:

    st.header("Ask Questions from the PDF ")
    st.markdown("Use this chat to ask questions that will be answered only using the content of the document uploaded in the first tab. **NOTE: This tab still requires a valid OPENAI_API_KEY.**")
    
    
    index, metadata = load_faiss_knowledge_base()

    if index is None or metadata is None:
        st.warning("Please upload a PDF in the 'Upload Document' tab first to build the knowledge base.")
        query = st.text_input("Enter your question", disabled=True)
    elif not check_openai_api_key():
        st.warning("The OpenAI API key is missing. This tab requires it for the RAG LLM.")
        query = st.text_input("Enter your question", disabled=True)
    else:
        query = st.text_input("Enter your question")

        if query:
            with st.spinner("Searching and generating answer..."):
                try:
                    
                    embedder = get_embedder()
                    
                    
                    q_vec = embedder.encode([query]).astype("float32")

                    
                    D, I = index.search(q_vec, 5)

                    retrieved_chunks = [metadata["chunks"][i] for i in I[0]]

                    
                    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)

                    STRICT_PROMPT = """
You MUST answer the question using ONLY the PDF context provided below.

CONTEXT:
{context}

QUESTION:
{question}

RULES:
1. Answer only using the context.
2. If the answer is NOT present, reply exactly: "ANSWER NOT FOUND IN PDF".
3. Do NOT guess or use external knowledge.
"""

                    prompt = PromptTemplate(
                        input_variables=["context", "question"],
                        template=STRICT_PROMPT
                    )

                    final = prompt.format(
                        context="\n\n".join(retrieved_chunks),
                        question=query
                    )

                    response = llm.invoke(final)

                    st.write("Answer:")
                    st.success(response.content)

                    with st.expander("View Retrieved Chunks (For Debugging RAG)"):
                        
                        for i, chunk in enumerate(retrieved_chunks):
                            st.markdown(f"**Chunk {i+1}**:\n```\n{chunk}\n```")

                except AuthenticationError as e:
                    st.error("RAG Query Failed: The OpenAI API Key provided is likely invalid or revoked. Please check your key.")
                except APIError as e:
                    
                    st.error(f"RAG Query Failed: API Error. This often means you have exceeded your current quota or hitting a rate limit. Full Error: {e.status_code} - {e.response.text}")
                except Exception as e:
                   
                    st.error(f"An unexpected error occurred during the RAG process. Full Error: {e}")