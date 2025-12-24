import streamlit as st
import pandas as pd
import io
import base64
import hashlib
from datetime import datetime
import tempfile
import os
import time
from PIL import Image, ImageEnhance, ImageFilter
import re
import random
import asyncio
import numpy as np
import json
import uuid
import logging

# Setup professional logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import pytesseract
    try:
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    except:
        pass
    tesseract_available = True
except:
    tesseract_available = False

# Configure Gemini AI
try:
    import google.generativeai as genai
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_available = True
except:
    gemini_available = False

try:
    from sentence_transformers import SentenceTransformer

    @st.cache_resource
    def load_embedding_model():
        try:
            models_to_try = [
                "all-MiniLM-L6-v2",
                "paraphrase-MiniLM-L6-v2",  
                "all-mpnet-base-v2", 
            ]
            
            for model_name in models_to_try:
                try:
                    model = SentenceTransformer(model_name)
                    st.success(f"✅ Loaded: {model_name}")
                    return model
                except Exception as e:
                    continue
            
            return None
        except Exception as e:
            st.error(f"❌ Failed to load embedding model: {e}")
            return None
    
    embedding_model = load_embedding_model()
    sentence_transformers_available = embedding_model is not None
except Exception as e:
    sentence_transformers_available = False
    embedding_model = None

# Configure Edge-TTS
try:
    import edge_tts
    edge_tts_available = True
except ImportError:
    edge_tts_available = False

# Fallback to gTTS
try:
    from gtts import gTTS
    gtts_available = True
except ImportError:
    gtts_available = False

def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    output_dir = "output_files"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

# =============================================================================
# QDRANT VECTOR DATABASE - PERSISTENT STORAGE
# =============================================================================

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    
    @st.cache_resource
    def setup_qdrant():
        """Initialize Qdrant client with PERSISTENT storage"""
        try:
            client = QdrantClient(path="./qdrant_storage")
            return client
        except Exception as e:
            st.error(f"❌ Qdrant setup failed: {e}")
            return None
    
    qdrant_client = setup_qdrant()
    qdrant_available = qdrant_client is not None

except ImportError:
    qdrant_available = False
    qdrant_client = None

def check_existing_embeddings():
    """Check if vector database already has data"""
    if not qdrant_available:
        return False
    
    try:
        stats = get_qdrant_stats()
        return stats["count"] > 0
    except:
        return False

# Qdrant Database Functions
def init_qdrant_collection(collection_name="documents", vector_size=384):
    """Initialize or get Qdrant collection"""
    if not qdrant_available:
        return False
    
    try:
        try:
            qdrant_client.get_collection(collection_name)
        except Exception:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
        return True
    except Exception as e:
        st.error(f"❌ Qdrant collection error: {e}")
        return False

def store_enhanced_in_qdrant(embeddings_data, filename, metadata=None):
    """Store enhanced embeddings in Qdrant vector database"""
    if not qdrant_available or not init_qdrant_collection():
        return False
    
    try:
        if metadata is None:
            metadata = {}
        
        points = []
        for i, item in enumerate(embeddings_data):
            point_id = i + int(datetime.now().timestamp())
            
            point_metadata = metadata.copy()
            point_metadata.update({
                'chunk_id': item['chunk_id'],
                'text_length': item['text_length'],
                'original_filename': filename,
                'embedding_model': item.get('embedding_model', 'sentence-transformers-enhanced'),
                'timestamp': datetime.now().isoformat(),
                'text_preview': item['enhanced_text'][:100] + "..." if len(item['enhanced_text']) > 100 else item['enhanced_text'],
                'full_text': item['enhanced_text'],
                'original_text': item.get('original_text', ''),
                'word_count': item.get('word_count', len(item['enhanced_text'].split())),
                'sentence_count': item.get('sentence_count', 1)
            })
            
            point = PointStruct(
                id=point_id,
                vector=item['embedding'],
                payload=point_metadata
            )
            points.append(point)
        
        operation_info = qdrant_client.upsert(
            collection_name="documents",
            points=points
        )
        
        return True
        
    except Exception as e:
        st.error(f"❌ Enhanced Qdrant storage failed: {e}")
        return False

def search_qdrant(query_text, n_results=5):
    """Search similar documents in Qdrant with improved query handling"""
    if not qdrant_available:
        return []
    
    try:
        processed_query = query_text.lower().strip()
        
        if sentence_transformers_available and embedding_model is not None:
            query_embedding = embedding_model.encode(processed_query).tolist()
        else:
            query_embedding = generate_simple_embedding(processed_query)
        
        search_result = qdrant_client.search(
            collection_name="documents",
            query_vector=query_embedding,
            limit=n_results * 2
        )
        
        similar_docs = []
        for result in search_result:
            similar_docs.append({
                'id': result.id,
                'score': result.score,
                'payload': result.payload,
                'text_preview': result.payload.get('text_preview', 'No preview'),
                'full_text': result.payload.get('full_text', '')
            })
        
        return similar_docs
        
    except Exception as e:
        st.error(f"❌ Qdrant search failed: {e}")
        return []

def get_qdrant_stats():
    """Get Qdrant collection statistics"""
    if not qdrant_available:
        return {"count": 0, "status": "not_available"}
    
    try:
        collection_info = qdrant_client.get_collection("documents")
        return {
            "count": collection_info.points_count,
            "status": "active",
            "vectors_count": collection_info.vectors_count,
        }
    except Exception as e:
        return {"count": 0, "status": "error", "error": str(e)}

# =============================================================================
# RAG (RETRIEVAL AUGMENTED GENERATION) FUNCTIONS - IMPROVED
# =============================================================================

def generate_rag_answer(query, context_chunks, model_name="gemini-1.5-flash"):
    """Generate answer using RAG with Gemini AI"""
    if not gemini_available:
        return "Gemini AI not configured for RAG", []
    
    try:
        context_text = ""
        sources = []
        
        for i, chunk in enumerate(context_chunks):
            context_text += f"--- Source {i+1} (Similarity: {chunk['score']:.3f}) ---\n"
            context_text += f"From: {chunk['payload'].get('original_filename', 'Unknown')}\n"
            context_text += f"Content: {chunk['full_text']}\n\n"
            
            sources.append({
                'source': chunk['payload'].get('original_filename', 'Unknown'),
                'similarity_score': chunk['score'],
                'text_preview': chunk['text_preview'],
                'chunk_id': chunk['payload'].get('chunk_id', 'N/A'),
                'full_text': chunk['full_text']
            })
        
        prompt = f"""
You are an expert AI assistant answering questions based on retrieved document content.

USER QUESTION: {query}

RETRIEVED DOCUMENT CONTEXT:
{context_text}

INSTRUCTIONS:
1. Answer the question using ONLY the provided context
2. If the context doesn't contain relevant information, say "I cannot find this information in the uploaded documents"
3. Be precise and factual
4. Cite sources when possible (mention which document the information came from)
5. Keep the answer concise but comprehensive
6. If multiple sources provide similar information, synthesize them
7. Do not make up information or use external knowledge

Please provide a helpful answer based on the available documents:
"""
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text, sources
        else:
            return "No answer generated - please try again", sources
        
    except Exception as e:
        return f"RAG Error: {str(e)}", []

def rag_search_and_answer(query, n_results=10, model_name="gemini-1.5-flash"):
    """Complete RAG pipeline: search + generate answer"""
    if not qdrant_available:
        return "Vector database not available", []
    
    processed_query = query.lower().strip()
    similar_chunks = search_qdrant(processed_query, n_results * 2)
    
    if not similar_chunks:
        return "No relevant documents found in the database. Please upload and process documents first.", []
    
    if similar_chunks:
        max_score = max(chunk['score'] for chunk in similar_chunks)
        threshold = max(0.05, max_score * 0.3)
    else:
        threshold = 0.05
    
    relevant_chunks = []
    for chunk in similar_chunks:
        if chunk['score'] > threshold:
            relevant_chunks.append(chunk)
        elif any(word in chunk['full_text'].lower() for word in processed_query.split() if len(word) > 2):
            relevant_chunks.append(chunk)
    
    seen_ids = set()
    unique_chunks = []
    for chunk in relevant_chunks:
        if chunk['id'] not in seen_ids:
            seen_ids.add(chunk['id'])
            unique_chunks.append(chunk)
    
    relevant_chunks = unique_chunks[:n_results]
    
    if not relevant_chunks:
        relevant_chunks = similar_chunks[:min(3, len(similar_chunks))]
    
    answer, sources = generate_rag_answer(query, relevant_chunks, model_name)
    
    return answer, sources

# =============================================================================
# GEMINI AI TEXT ENHANCEMENT
# =============================================================================

def get_available_gemini_models():
    """Get available Gemini models"""
    if not gemini_available:
        return []
    
    try:
        models = genai.list_models()
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.split('/')[-1]
                available_models.append(model_name)
        return available_models
    except Exception as e:
        st.error(f"Error getting Gemini models: {e}")
        return []

def enhance_text_with_gemini(text, model_name="gemini-1.5-flash"):
    """Enhance text using Gemini AI for professional narration"""
    if not gemini_available:
        return "Gemini AI not configured", False
    
    if len(text.strip()) < 20:
        return "Text too short for enhancement", False
    
    try:
        prompt = f"""
You are an expert audiobook narrator.  
Your task is to transform the extracted text into listener-friendly audiobook-ready narration without leaving out details
ORIGINAL TEXT:
{text}

Please create an enhanced version following these guidelines:

Do NOT summarize or cut down the content. Keep all important details from the original.  
Begin with a warm greeting such as: "Hello listeners, welcome...".
Provide a short summary of what the listener will learn before diving into the content.
Make it engaging and conversational, not just a direct copy.
Rewrite the text so it flows naturally when spoken aloud.  
Break down long or complex sentences into clear, shorter sentences.  
Add natural pauses using "..." or line breaks for rhythm and engagement.  
Remove raw Markdown symbols (#, *, -, etc.), but keep all information they represent.  
Rewrite bullet points or lists into spoken style. For example: "First..., then..., finally...". 
Expand abbreviations (e.g., "e.g." to "for example", "etc." to "and so on").  
Maintain the same depth of information, just make it more engaging, warm, and listener-friendly.  

Return ONLY the enhanced narration text without any additional explanations or notes.
"""
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text, True
        else:
            return "AI enhancement failed - no response received", False
        
    except Exception as e:
        return f"Gemini AI Error: {str(e)}", False

# =============================================================================
# ENHANCED SENTENCE TRANSFORMERS EMBEDDINGS - USING PRE-ENHANCED TEXT
# =============================================================================

def create_chunks_with_overlap_simple(text: str, chunk_size: int = 400, overlap: int = 50):
    """SIMPLE and RELIABLE chunking using word count"""
    words = text.split()
    chunks = []
    chunk_id = 0
    
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = ' '.join(chunk_words)
        
        chunks.append({
            'text': chunk_text,
            'char_count': len(chunk_text),
            'word_count': len(chunk_words),
            'sentence_count': 1,
            'source_sentences': [chunk_text],
            'chunk_id': chunk_id
        })
        
        chunk_id += 1
        start += (chunk_size - overlap)
    
    return chunks

def generate_embeddings_from_pre_enhanced_text(enhanced_text, chunk_size=400):
    """Generate embeddings from PRE-ENHANCED text chunks"""
    if not sentence_transformers_available or embedding_model is not None:
        return generate_embeddings_fallback(enhanced_text, chunk_size)
    
    try:
        total_words = len(enhanced_text.split())
        logger.info(f"Generating embeddings from PRE-ENHANCED text of {total_words} words")
        
        chunks = create_chunks_with_overlap_simple(enhanced_text, chunk_size=chunk_size, overlap=50)
        logger.info(f"Created {len(chunks)} chunks from PRE-ENHANCED text")
        
        if not chunks:
            return generate_embeddings_fallback(enhanced_text, chunk_size)
        
        chunk_texts = [chunk['text'] for chunk in chunks]
        
        logger.info("Generating embeddings from PRE-ENHANCED text with progress tracking...")
        embeddings = embedding_model.encode(
            chunk_texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        if isinstance(embeddings, np.ndarray):
            embeddings_list = embeddings.tolist()
        else:
            embeddings_list = [emb.tolist() for emb in embeddings]
        
        results = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
            results.append({
                'enhanced_text': chunk['text'],
                'embedding': embedding,
                'chunk_id': i,
                'text_length': chunk['char_count'],
                'embedding_dimensions': len(embedding),
                'embedding_model': "sentence-transformers-enhanced",
                'word_count': chunk['word_count'],
                'sentence_count': chunk['sentence_count'],
                'source_sentences': chunk['source_sentences'],
                'processing_timestamp': datetime.now().isoformat()
            })
        
        logger.info(f"Successfully generated {len(results)} embeddings from PRE-ENHANCED text")
        return results
        
    except Exception as e:
        logger.error(f"Pre-enhanced embedding generation error: {e}")
        return generate_embeddings_fallback(enhanced_text, chunk_size)

def generate_embeddings_fallback(text, chunk_size=400):
    """Enhanced fallback embedding generation with professional features"""
    try:
        logger.info("Using fallback embedding generation")
        
        chunks = create_chunks_with_overlap_simple(text, chunk_size=chunk_size, overlap=50)
        
        if not chunks:
            return []
        
        results = []
        for i, chunk in enumerate(chunks):
            embedding = generate_simple_embedding(chunk['text'])
            results.append({
                'enhanced_text': chunk['text'],
                'embedding': embedding,
                'chunk_id': i,
                'text_length': len(chunk['text']),
                'embedding_dimensions': len(embedding),
                'embedding_model': "local-hashing-fallback",
                'word_count': chunk['word_count'],
                'sentence_count': chunk['sentence_count'],
                'source_sentences': chunk['source_sentences'],
                'processing_timestamp': datetime.now().isoformat()
            })
        
        logger.info(f"Fallback generated {len(results)} embeddings")
        return results
        
    except Exception as e:
        logger.error(f"Fallback embedding error: {e}")
        return []

def generate_simple_embedding(text):
    """Enhanced simple embedding with better vector distribution"""
    try:
        hash_functions = [
            hashlib.sha256(text.encode()).hexdigest(),
            hashlib.md5(text.encode()).hexdigest(),
            hashlib.sha1(text.encode()).hexdigest(),
            hashlib.blake2b(text.encode()).hexdigest()
        ]
        
        combined = ''.join(hash_functions)
        embedding = []
        
        for i in range(0, min(len(combined)-1, 768), 2):
            hex_val = combined[i:i+2]
            try:
                num_val = (int(hex_val, 16) / 255.0) * 2 - 1
                embedding.append(round(num_val, 6))
            except:
                embedding.append(0.0)
        
        while len(embedding) < 384:
            embedding.append(0.0)
        
        return embedding[:384]
        
    except Exception as e:
        logger.error(f"Simple embedding error: {e}")
        return [0.0] * 384

# =============================================================================
# TEXT ENHANCEMENT OPTIONS
# =============================================================================

def enhance_text_locally(text):
    """Local text enhancement fallback"""
    if len(text.strip()) < 20:
        return text, True
    
    try:
        styles = [
            {
                'intro': "Welcome to our audio presentation. Let me guide you through this content.",
                'outro': "Thank you for your attention. This concludes our session.",
                'pauses': ['[pause]', '[brief pause]']
            },
            {
                'intro': "Hello! Let's explore this interesting content together.", 
                'outro': "Thanks for listening! Hope you found that useful.",
                'pauses': ['[take a breath]', '[quick pause]']
            }
        ]
        
        style = random.choice(styles)
        lines = text.split('\n')
        enhanced_lines = []
        
        enhanced_lines.append("🎙️ " + style['intro'])
        enhanced_lines.append("")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            enhanced_lines.append(line)
            
            if i % 3 == 0 and i > 0:
                enhanced_lines.append(random.choice(style['pauses']))
        
        enhanced_lines.append("")
        enhanced_lines.append("📚 " + style['outro'])
        
        final_text = '\n'.join(enhanced_lines)
        return final_text, True
        
    except Exception as e:
        return f"Local enhancement error: {str(e)}", False

# =============================================================================
# AUDIO & FILE PROCESSING 
# =============================================================================

def generate_audio_edge_tts(text, voice_name="en-US-AriaNeural", rate="+0%"):
    """Generate audio using Edge-TTS"""
    if not edge_tts_available:
        return None, "Edge-TTS not available"
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def async_tts():
            communicate = edge_tts.Communicate(text, voice_name, rate=rate)
            audio_buffer = io.BytesIO()
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            
            audio_buffer.seek(0)
            return audio_buffer
        
        audio_buffer = loop.run_until_complete(async_tts())
        loop.close()
        
        return audio_buffer, None
        
    except Exception as e:
        return None, f"Edge-TTS Error: {str(e)}"

def generate_audio_gtts(text, slow_speed=False):
    """Fallback to gTTS"""
    if not gtts_available:
        return None, "gTTS not available"
    
    try:
        tts = gTTS(text=text, lang='en', slow=slow_speed)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer, None
    except Exception as e:
        return None, f"gTTS Error: {str(e)}"

def extract_text_from_file(uploaded_file):
    """Extract text from various file types"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        file_ext = uploaded_file.name.lower().split('.')[-1]
        text = ""
        
        if file_ext == 'txt':
            with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                
        elif file_ext == 'pdf':
            try:
                import pdfplumber
                with pdfplumber.open(tmp_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"--- Page {page.page_number} ---\n{page_text}\n\n"
            except ImportError:
                text = "📄 Install pdfplumber: pip install pdfplumber"
                
        elif file_ext == 'docx':
            try:
                from docx import Document
                doc = Document(tmp_path)
                text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            except ImportError:
                text = "📋 Install python-docx: pip install python-docx"
                
        elif file_ext in ['jpg', 'jpeg', 'png', 'bmp']:
            if tesseract_available:
                try:
                    original_image = Image.open(tmp_path)
                    text = pytesseract.image_to_string(original_image, config='--psm 6')
                    if not text.strip():
                        enhanced_image = enhance_image_for_ocr(original_image)
                        text = pytesseract.image_to_string(enhanced_image, config='--psm 6')
                except Exception as e:
                    text = f"🚫 OCR Error: {str(e)}"
            else:
                text = "🔍 Tesseract OCR not available"
        
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            
        return text.strip() if text.strip() else "📭 No text extracted from file."
        
    except Exception as e:
        return f"🚫 Extraction error: {str(e)}"

def enhance_image_for_ocr(image):
    """Enhance image for better OCR results"""
    try:
        if image.mode != 'L':
            image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        image = image.filter(ImageFilter.MedianFilter(3))
        return image
    except Exception:
        return image

# =============================================================================
# STREAMLIT UI - PROFESSIONAL AI AUDIOBOOK GENERATOR
# =============================================================================

def main():
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'current_processing' not in st.session_state:
        st.session_state.current_processing = False
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
    
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "🎵 Generate Audiobook"
    
    # Apply professional CSS with advanced animations
    st.markdown("""
    <style>
    /* Professional Dark Theme with Glass Morphism */
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0c0c2a 100%);
        color: #ffffff;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        min-height: 100vh;
    }
    
    /* Animated Gradient Header */
    .main-header {
        font-size: 3.5rem;
        background: linear-gradient(90deg, #8B5CF6, #3B82F6, #10B981, #F59E0B);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 900;
        padding: 1.5rem 0;
        text-shadow: 0 4px 20px rgba(59, 130, 246, 0.2);
        animation: gradient-shift 8s ease infinite;
    }
    
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .sub-header {
        font-size: 1.3rem;
        color: #94A3B8;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 400;
        letter-spacing: 0.5px;
        line-height: 1.6;
    }
    
    /* Professional Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 10px;
        margin-bottom: 2.5rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        white-space: pre-wrap;
        background: transparent;
        border-radius: 15px;
        color: #CBD5E1 !important;
        font-weight: 600;
        font-size: 1.1rem;
        border: none;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 0 1.5rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(139, 92, 246, 0.1);
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%) !important;
        color: white !important;
        font-weight: 700;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
        transform: translateY(-2px);
    }
    

    
    @keyframes card-enter {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Upload Section with Animation */
    .upload-section {
        border: 2px dashed #8B5CF6;
        border-radius: 20px;
        padding: 4rem 2rem;
        text-align: center;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(59, 130, 246, 0.05));
        margin: 2.5rem 0;
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
    }
    
    .upload-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .upload-section:hover {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1));
        border-color: #3B82F6;
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(139, 92, 246, 0.3);
    }
    
    
    @keyframes chat-appear {
        from {
            opacity: 0;
            transform: scale(0.95);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    /* Chat Header */
    .chat-header {
        background: linear-gradient(135deg, #1E40AF 0%, #3730A3 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 25px 25px 0 0;
        font-weight: 700;
        font-size: 1.3rem;
        display: flex;
        align-items: center;
        gap: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    /* Chat Messages Area */
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        gap: 16px;
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.6));
    }
    
    /* Professional Chat Bubbles */
    .message-bubble {
        max-width: 75%;
        padding: 16px 20px;
        border-radius: 22px;
        margin: 8px 0;
        word-wrap: break-word;
        position: relative;
        animation: message-slide 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        line-height: 1.6;
    }
    
    @keyframes message-slide {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #3730A3 0%, #7C3AED 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 8px;
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .ai-bubble {
        background: linear-gradient(135deg, #1E40AF 0%, #1D4ED8 100%);
        color: white;
        margin-right: auto;
        border-bottom-left-radius: 8px;
        box-shadow: 0 6px 20px rgba(30, 64, 175, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .bubble-time {
        font-size: 0.8rem;
        opacity: 0.8;
        margin-top: 6px;
        text-align: right;
        font-weight: 500;
    }
    
    /* Chat Input Area */
    .chat-input-container {
        padding: 1.5rem 2rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(30, 41, 59, 0.9);
        border-radius: 0 0 25px 25px;
        backdrop-filter: blur(10px);
    }
    
    /* Professional Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 15px;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 35px rgba(139, 92, 246, 0.6);
        background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #8B5CF6, #3B82F6, #10B981);
        border-radius: 15px;
        height: 12px;
        animation: progress-pulse 2s ease-in-out infinite;
    }
    
    @keyframes progress-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Status Badges */
    .status-badge {
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        padding: 8px 20px;
        border-radius: 25px;
        font-size: 0.95em;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Sidebar - Professional */
    .sidebar-header {
        background: linear-gradient(135deg, #1E40AF 0%, #3730A3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Metrics Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(139, 92, 246, 0.3);
    }
    
    /* Custom Scrollbar */
    .chat-messages::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-messages::-webkit-scrollbar-track {
        background: rgba(30, 41, 59, 0.3);
        border-radius: 10px;
    }
    
    .chat-messages::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #8B5CF6, #3B82F6);
        border-radius: 10px;
        border: 2px solid rgba(30, 41, 59, 0.3);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.5rem;
        }
        .sub-header {
            font-size: 1.1rem;
        }
        .tab-content-card {
            padding: 1.5rem;
            min-height: 500px;
        }
        .chat-container {
            height: 550px;
        }
        .message-bubble {
            max-width: 85%;
        }
    }
    
    /* Feature Cards */
    .feature-card {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1));
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(139, 92, 246, 0.3);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(139, 92, 246, 0.3);
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(59, 130, 246, 0.2));
    }
    
    /* Loading Animation */
    .loading-dots {
        display: flex;
        justify-content: center;
        gap: 8px;
        margin: 20px 0;
    }
    
    .loading-dots div {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #8B5CF6;
        animation: dot-pulse 1.4s ease-in-out infinite;
    }
    
    .loading-dots div:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .loading-dots div:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes dot-pulse {
        0%, 100% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.5);
            opacity: 0.7;
        }
    }
    
    </style>
    
    <h1 class="main-header">🎧 AI Audiobook Generator</h1>
    <h3 class="sub-header">Transform any document into professional audiobooks with AI-powered enhancement<br>and intelligent Q&A capabilities.</h3>
    """, unsafe_allow_html=True)
    
    # Get available models
    gemini_models = get_available_gemini_models() if gemini_available else []
    
    # Sidebar - Professional Control Panel
    with st.sidebar:
        st.markdown('<div class="sidebar-header"><h3>⚙️ Control Panel</h3></div>', unsafe_allow_html=True)
        
        # Feature Cards
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("**🎵 Audio**")
            st.markdown("**Quality**")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("**🤖 AI**")
            st.markdown("**Powered**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🧠 AI Configuration")
        
        # Text Enhancement Model
        with st.expander("📝 Text Enhancement", expanded=True):
            enhancement_method = st.radio(
                "Enhancement Method:",
                ["Gemini AI (Professional)", "Local Processing"],
                index=0,
                label_visibility="collapsed"
            )
            
            if enhancement_method == "Gemini AI (Professional)" and gemini_models:
                gemini_model = st.selectbox(
                    "Gemini Model:",
                    gemini_models,
                    index=0
                )
        
        # Embedding Model
        with st.expander("🔢 Embedding Generation"):
            embedding_method = st.radio(
                "Embedding Method:",
                ["Sentence Transformers", "Local Hashing"],
                index=0,
                label_visibility="collapsed"
            )
        
        st.markdown("---")
        st.markdown("### 🎵 Audio Settings")
        
        with st.expander("Voice & Speed", expanded=True):
            if edge_tts_available:
                voice_name = st.selectbox(
                    "Voice Selection:",
                    ["en-US-AriaNeural", "en-US-JennyNeural", "en-GB-SoniaNeural", "en-AU-NatashaNeural"],
                    index=0
                )
                speech_speed = st.select_slider(
                    "Speech Speed:",
                    options=["-30%", "-20%", "-10%", "+0%", "+10%", "+20%", "+30%"],
                    value="+0%"
                )
            else:
                speech_speed = st.radio("Speech Speed:", ["Normal", "Slow"])
        
        st.markdown("---")
        st.markdown("### ⚙️ Processing Settings")
        
        chunk_size = st.slider("Text Chunk Size:", 200, 1000, 400, help="Larger chunks = better context, smaller chunks = more precise retrieval")
        store_in_db = st.checkbox("💾 Store in Vector Database", value=True, help="Enable persistent storage for Q&A")
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        
        # Status indicators in grid
        status_cols = st.columns(3)
        with status_cols[0]:
            if gemini_available:
                st.markdown('<span class="status-badge">🤖</span>', unsafe_allow_html=True)
            else:
                st.warning("🤖")
        with status_cols[1]:
            if sentence_transformers_available:
                st.markdown('<span class="status-badge">🔢</span>', unsafe_allow_html=True)
            else:
                st.info("🔢")
        with status_cols[2]:
            if edge_tts_available or gtts_available:
                st.markdown('<span class="status-badge">🎵</span>', unsafe_allow_html=True)
            else:
                st.error("🎵")
        
        # Database info
        if qdrant_available:
            qdrant_stats = get_qdrant_stats()
            has_existing_data = check_existing_embeddings()
            
            if has_existing_data:
                st.success(f"**🗄️ {qdrant_stats['count']} vectors**")
                st.progress(min(qdrant_stats['count'] / 1000, 1.0))
            else:
                st.info("🗄️ No vectors yet")
            
            if st.button("🗑️ Clear Database", use_container_width=True, type="secondary"):
                try:
                    qdrant_client.delete_collection("documents")
                    init_qdrant_collection()
                    st.success("Database cleared!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.markdown("---")
        st.markdown("### 📁 Supported Formats")
        st.markdown("""
        <div style='background: rgba(30,41,59,0.5); padding: 1rem; border-radius: 15px;'>
        - 📝 **TXT** - Plain Text<br>
        - 📄 **PDF** - Documents<br>
        - 📋 **DOCX** - Word Files<br>
        - 🖼️ **JPG/PNG** - Images
        </div>
        """, unsafe_allow_html=True)
    
    # Main content with professional tabs
    tab1, tab2 = st.tabs(["🎵 Generate Audiobook", "💬 Advanced RAG Q&A"])
    
    # Tab 1: Audiobook Generation
    with tab1:
        st.markdown('<div class="tab-content-card fade-in">', unsafe_allow_html=True)
        
        # Hero Section
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h2 style='color: #8B5CF6; margin-bottom: 0.5rem;'>🎧 Professional Audiobook Creation</h2>
                <p style='color: #94A3B8;'>Upload any document and let AI transform it into engaging audio content</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Upload Section
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "**📁 Drag & Drop or Click to Upload**",
            type=['txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png', 'bmp'],
            help="Upload text documents, PDFs, Word files, or images with text",
            key="uploader"
        )
        
        if uploaded_file:
            # File Info Cards
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("📄 File", uploaded_file.name[:20] + "..." if len(uploaded_file.name) > 20 else uploaded_file.name)
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                file_ext = uploaded_file.name.split('.')[-1].upper()
                st.metric("📊 Type", file_ext)
                st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("💾 Size", f"{uploaded_file.size / 1024:.1f} KB")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Process Button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Start Audiobook Generation", type="primary", use_container_width=True):
                    st.session_state.current_processing = True
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Processing Pipeline
        if st.session_state.current_processing and uploaded_file is not None:
            st.markdown("---")
            st.markdown("## ⚙️ Processing Pipeline")
            
            # Create progress bar with steps
            steps = [
                {"label": "📥 Extracting text...", "progress": 15, "icon": "📥"},
                {"label": "🤖 Enhancing with AI...", "progress": 35, "icon": "🤖"},
                {"label": "🎵 Generating audio...", "progress": 55, "icon": "🎵"},
                {"label": "🔢 Creating embeddings...", "progress": 75, "icon": "🔢"},
                {"label": "💾 Storing in database...", "progress": 90, "icon": "💾"},
                {"label": "✅ Complete!", "progress": 100, "icon": "✅"}
            ]
            
            # Progress container
            progress_container = st.container()
            status_container = st.empty()
            results_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                
                # Step indicators
                step_cols = st.columns(len(steps))
                for i, step in enumerate(steps):
                    with step_cols[i]:
                        st.markdown(f"<div style='text-align: center; opacity: 0.5;'>{step['icon']}</div>", unsafe_allow_html=True)
            
            current_step = 0
            extracted_text = ""
            enhanced_text_for_audio = ""
            audio_buffer = None
            embeddings = []
            
            try:
                # Step 1: Text Extraction
                status_container.markdown(f"**{steps[current_step]['label']}**")
                progress_bar.progress(steps[current_step]['progress'])
                extracted_text = extract_text_from_file(uploaded_file)
                current_step += 1
                time.sleep(0.5)
                
                # Step 2: AI Text Enhancement
                status_container.markdown(f"**{steps[current_step]['label']}**")
                progress_bar.progress(steps[current_step]['progress'])
                enhanced_text_for_audio = extracted_text
                
                if len(extracted_text.strip()) > 20:
                    if enhancement_method == "Gemini AI (Professional)" and gemini_available:
                        enhanced_text_for_audio, success = enhance_text_with_gemini(extracted_text, gemini_model)
                    else:
                        enhanced_text_for_audio, success = enhance_text_locally(extracted_text)
                current_step += 1
                time.sleep(0.5)
                
                # Step 3: Audio Generation
                status_container.markdown(f"**{steps[current_step]['label']}**")
                progress_bar.progress(steps[current_step]['progress'])
                
                if edge_tts_available:
                    audio_buffer, error = generate_audio_edge_tts(enhanced_text_for_audio, voice_name, speech_speed)
                else:
                    slow_speed = (speech_speed == "Slow")
                    audio_buffer, error = generate_audio_gtts(enhanced_text_for_audio, slow_speed)
                current_step += 1
                time.sleep(0.5)
                
                # Step 4: Embedding Generation
                status_container.markdown(f"**{steps[current_step]['label']}**")
                progress_bar.progress(steps[current_step]['progress'])
                
                if embedding_method == "Sentence Transformers" and sentence_transformers_available:
                    embeddings = generate_embeddings_from_pre_enhanced_text(enhanced_text_for_audio, chunk_size)
                else:
                    embeddings = generate_embeddings_fallback(enhanced_text_for_audio, chunk_size)
                current_step += 1
                time.sleep(0.5)
                
                # Step 5: Database Storage
                status_container.markdown(f"**{steps[current_step]['label']}**")
                progress_bar.progress(steps[current_step]['progress'])
                
                if store_in_db and qdrant_available and embeddings:
                    db_success = store_enhanced_in_qdrant(
                        embeddings, 
                        uploaded_file.name,
                        metadata={
                            "file_type": uploaded_file.type,
                            "file_size": uploaded_file.size,
                            "processing_time": datetime.now().isoformat()
                        }
                    )
                current_step += 1
                time.sleep(0.5)
                
                # Step 6: Completion
                status_container.markdown(f"**{steps[current_step]['label']}**")
                progress_bar.progress(steps[current_step]['progress'])
                
                # Results Display
                with results_container:
                    st.success("✨ Audiobook Generation Complete!")
                    
                    # Results Grid
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("📝 Text Length", f"{len(extracted_text):,}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("🔢 Chunks", len(embeddings))
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("🎵 Audio", "✅" if audio_buffer else "❌")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Audio Player
                    if audio_buffer:
                        st.markdown("### 🎧 Listen to Your Audiobook")
                        audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode()
                        st.markdown(f"""
                        <div style='background: rgba(30,41,59,0.7); padding: 2rem; border-radius: 20px; border: 1px solid rgba(139,92,246,0.3);'>
                            <audio controls style='width: 100%; height: 60px; border-radius: 15px;'>
                                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                            </audio>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Audio",
                            data=audio_buffer,
                            file_name=f"{uploaded_file.name.split('.')[0]}_audiobook.mp3",
                            mime="audio/mp3",
                            use_container_width=True
                        )
                
            except Exception as e:
                st.error(f"❌ Error during processing: {str(e)}")
            
            st.session_state.current_processing = False
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 2: Document Q&A
    with tab2:
        st.markdown('<div class="tab-content-card fade-in">', unsafe_allow_html=True)
        
        # Chat Interface
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Chat Header
        st.markdown('<div class="chat-header">💬 Document RAG Q&A Assistant</div>', unsafe_allow_html=True)
        
        # Chat Messages Area
        with st.container():
            st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
            
            # Welcome message
            if not st.session_state.chat_history:
                welcome_msg = """
                <div class="message-bubble ai-bubble">
                    👋 Hello! I'm your AI Document Assistant. 
                    <br><br>
                    I can help you find information from your uploaded documents. Ask me anything about the content!
                    <br><br>
                    Try questions like:
                    • "What are the main topics?"
                    • "Find information about..."
                    • "Summarize the key points"
                    <div class="bubble-time">Just now</div>
                </div>
                """
                st.markdown(welcome_msg, unsafe_allow_html=True)
            
            # Display chat history
            for chat in st.session_state.chat_history:
                # User message
                user_msg = f"""
                <div class="message-bubble user-bubble">
                    {chat["question"]}
                    <div class="bubble-time">{chat["timestamp"]}</div>
                </div>
                """
                st.markdown(user_msg, unsafe_allow_html=True)
                
                # AI response
                ai_msg = f"""
                <div class="message-bubble ai-bubble">
                    {chat["answer"]}
                    <div class="bubble-time">{chat["timestamp"]}</div>
                </div>
                """
                st.markdown(ai_msg, unsafe_allow_html=True)
                
                # Sources (collapsible)
                if chat.get('sources'):
                    with st.expander(f"📚 Sources ({len(chat['sources'])})", expanded=False):
                        for i, source in enumerate(chat['sources']):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{i+1}. {source['source']}**")
                                st.caption(f"Preview: {source['text_preview'][:120]}...")
                            with col2:
                                st.metric("Relevance", f"{source['similarity_score']:.2f}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat Input Area
        st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
        
        if not qdrant_available:
            st.error("❌ Vector database not available.")
            st.info("Please process documents in the Audiobook tab first")
        else:
            qdrant_stats = get_qdrant_stats()
            if qdrant_stats["count"] == 0:
                st.info("📭 No documents in database. Upload and process documents in the Audiobook tab.")
            else:
                # Database status
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.success(f"✅ **{qdrant_stats['count']}** document chunks available for Q&A")
                with col2:
                    if st.button("🗑️ Clear Chat", use_container_width=True):
                        st.session_state.chat_history = []
                        st.rerun()
                
                # Quick questions
                quick_cols = st.columns(4)
                quick_questions = [
                    ("📊 Summarize", "Can you summarize the main topics in the documents?"),
                    ("🔍 Find info", "What specific information is available about?"),
                    ("📖 Key points", "What are the key points from the documents?"),
                    ("💡 Insights", "What insights can you provide from the documents?")
                ]
                
                for i, (label, question) in enumerate(quick_questions):
                    with quick_cols[i]:
                        if st.button(label, use_container_width=True):
                            st.session_state.current_question = question
                
                # Question input
                question = st.text_input(
                    "Type your question:",
                    value=st.session_state.current_question,
                    placeholder="Ask anything about your documents...",
                    key="chat_input",
                    label_visibility="collapsed"
                )
                
                # Send button
                if st.button("🚀 Ask AI", type="primary", use_container_width=True) and question.strip():
                    if not gemini_available:
                        st.error("Gemini AI is not available for Q&A.")
                    else:
                        with st.spinner("🤔 Processing your question..."):
                            # Show loading animation
                            st.markdown("""
                            <div class="loading-dots">
                                <div></div>
                                <div></div>
                                <div></div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            answer, sources = rag_search_and_answer(
                                question, 
                                5, 
                                gemini_models[0] if gemini_models else "gemini-1.5-flash"
                            )
                            
                            st.session_state.chat_history.append({
                                "question": question,
                                "answer": answer,
                                "sources": sources,
                                "timestamp": datetime.now().strftime("%H:%M")
                            })
                            
                            st.session_state.current_question = ""
                            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close chat-input-container
        st.markdown('</div>', unsafe_allow_html=True)  # Close chat-container
        st.markdown('</div>', unsafe_allow_html=True)  # Close tab-content-card

if __name__ == "__main__":
    main()
