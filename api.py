import os
import io
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import chromadb

# Import your custom modules
from text_extraction import extractor
import text_enrichment
import tts
import rag_query

app = FastAPI(title="Audiobook Generator API", version="2.0")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---
class EnrichRequest(BaseModel):
    text: str
    model_name: str = "gemini-2.5-flash"

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-JennyNeural"
    rate: int = 180

class ChatRequest(BaseModel):
    query: str
    top_k: int = 5
    collection_name: str = "audiobook_embeddings"


# --- Helper: BytesIO Wrapper ---
class BytesIOWrapper(io.BytesIO):
    """Makes FastAPI UploadFile compatible with extractor.py"""
    def __init__(self, content, name):
        super().__init__(content)
        self.name = name


# --- Helper: Vector DB Ingestion ---
def ingest_text_to_chroma(text: str, filename: str):
    """
    Chunks the text and saves it to ChromaDB so RAG can find it.
    """
    try:
        # 1. Connect to DB
        client = chromadb.PersistentClient(path="./vectordb")
        collection = client.get_or_create_collection(name="audiobook_embeddings")

        # 2. Simple Chunking (Split by paragraphs)
        chunks = [c.strip() for c in text.split('\n\n') if len(c.strip()) > 50]

        if not chunks:
            return

        # 3. Add to ChromaDB
        ids = [f"{filename}_{str(uuid.uuid4())[:8]}" for _ in chunks]
        metadatas = [{"source": filename, "index": i} for i in range(len(chunks))]

        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✅ Ingested {len(chunks)} chunks from {filename}")

    except Exception as e:
        print(f"⚠️ Warning: Failed to ingest text to DB: {e}")


# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "running", "features": ["extraction", "enrichment", "tts", "rag"]}


@app.post("/extract")
async def extract_text(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Extract text from uploaded document (PDF, DOCX, image, etc.)
    """
    try:
        content = await file.read()
        file_wrapper = BytesIOWrapper(content, file.filename)

        # 1. Extract Text
        text = extractor.extract_text_from_file(file_wrapper)

        if "🚫" in text or "📭" in text:
            raise HTTPException(status_code=400, detail=text)

        # 2. Ingest to Vector DB (Background Task)
        background_tasks.add_task(ingest_text_to_chroma, text, file.filename)

        return {
            "filename": file.filename,
            "extracted_text": text,
            "message": "Text extracted successfully and stored for chat.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/enrich")
async def enrich_text(request: EnrichRequest):
    """
    Rewrite text for smoother audiobook narration using Gemini
    """
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="Server missing GOOGLE_API_KEY")
    try:
        enriched_text = text_enrichment.enrich_text_with_gemini(
            request.text, model_name=request.model_name
        )
        return {"enriched_text": enriched_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-audio")
async def generate_audio(request: TTSRequest, background_tasks: BackgroundTasks):
    """
    Convert text into audio (TTS)
    """
    try:
        # ✅ Use the sync function from tts.py
        audio_path, fmt = tts.synthesize_audio_chunks(
            chunks=[request.text],
            rate=request.rate,
            voice_name=request.voice
        )

        # Cleanup file after sending
        background_tasks.add_task(os.remove, audio_path)

        return FileResponse(
            path=audio_path,
            media_type=f"audio/{fmt}",
            filename=f"audiobook.{fmt}",
        )

    except Exception as e:
        print(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_with_docs(request: ChatRequest):
    """
    Query the extracted text using RAG (retrieval-augmented generation)
    """
    try:
        answer, chunks = rag_query.rag_answer(
            query=request.query,
            top_k=request.top_k,
            collection_name=request.collection_name,
        )

        sources = [
            {
                "text": c.text[:200] + "...",
                "source": c.metadata.get("source", "unknown"),
                "score": c.distance,
            }
            for c in chunks
        ]

        return {"answer": answer, "sources": sources}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
