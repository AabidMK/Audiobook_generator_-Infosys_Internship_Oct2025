import os
import traceback
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "uploads"
ENRICHED_DIR = PROJECT_ROOT / "enriched_texts"
AUDIO_DIR = PROJECT_ROOT / "audio_output"

for d in (INPUT_DIR, ENRICHED_DIR, AUDIO_DIR):
    d.mkdir(parents=True, exist_ok=True)

from backend.text_extractor import extract_text_from_file, split_text
import backend.generate_embeddings as genemb
import backend.text_enrich as tenrich
import backend.tts_generate as ttsgen

app = FastAPI(title="AI Audiobook Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static audio files
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# =====================================================
# Load TTS model
# =====================================================
from TTS.api import TTS

TTS_MODEL = os.getenv("TTS_MODEL", "tts_models/en/ljspeech/tacotron2-DDC")
print(f"🎙️ Loading TTS model: {TTS_MODEL}")
tts = TTS(model_name=TTS_MODEL, progress_bar=False, gpu=False)
print("✅ TTS model ready.")

# =====================================================
# Request Models
# =====================================================
class ChatQuery(BaseModel):
    query: str
    top_k: int = 3


# =====================================================
# 📘 Document Processing Endpoint
# =====================================================
@app.post("/process_document")
async def process_document(file: UploadFile = File(...)):
    """
    Full processing pipeline:
      1. Save uploaded file
      2. Extract text
      3. Enrich text
      4. Split into chunks
      5. Generate embeddings
      6. Generate audiobook
      7. Return audio URL + metadata
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing filename")

        # Save file
        saved_path = INPUT_DIR / file.filename
        content = await file.read()
        saved_path.write_bytes(content)
        print(f"📄 Saved: {saved_path.name}")

        # Step 1: Extract text
        extracted_text = extract_text_from_file(file.filename, content)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text extracted from file")
        print(f"✅ Extracted text length: {len(extracted_text)} chars")

        # Step 2: Enrich text
        enriched = tenrich.enrich_text(extracted_text)

        # Save enriched text
        enriched_path = ENRICHED_DIR / f"{Path(file.filename).stem}_narration.txt"
        enriched_path.write_text(enriched, encoding="utf-8")
        print(f"🗒️ Enriched text saved: {enriched_path.name}")

        # Step 3: Split into chunks
        chunks = split_text(enriched, chunk_size=int(os.getenv("CHUNK_SIZE", 2000)))
        print(f"🧩 Split into {len(chunks)} chunks")

        # Step 4: Store embeddings
        metadata_list = [{"source": file.filename, "chunk_idx": i} for i in range(len(chunks))]
        embedding_ids = genemb.embed_texts_and_store(chunks, metadata=metadata_list)
        print(f"💾 Stored {len(embedding_ids)} embeddings")

        # Step 5: Generate audiobook
        audio_path = ttsgen.process_file(tts, enriched_path, AUDIO_DIR)
        if not audio_path or not audio_path.exists():
            raise HTTPException(status_code=500, detail="Audio generation failed")

        print(f"🎧 Audio generated: {audio_path.name}")

        # Step 6: Return success
        return {
            "message": "processed",
            "audio_url": f"/audio/{audio_path.name}",
            "chunks": len(chunks),
            "embedding_ids": embedding_ids,
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 💬 Chat / Q&A Endpoint (Gemini-Enhanced)
# =====================================================
@app.post("/chat_query")
def chat_query(q: ChatQuery):
    """
    Smart Retrieval-Augmented Q&A:
    1️⃣ Retrieve top_k relevant chunks.
    2️⃣ If Gemini key is set, ask Gemini to answer only from those chunks.
    3️⃣ Otherwise, return summarized context.
    """
    try:
        top_k = q.top_k or 3
        res = genemb.query_chroma_by_text(q.query, n_results=top_k)
        docs, metas, dists = res["documents"], res["metadatas"], res["distances"]

        if not docs:
            return {"answer": "No relevant information found.", "sources": []}

        # Build combined context
        context_text = "\n\n".join(docs)[:6000]
        sources = [
            {"source": m.get("source", "unknown"), "distance": float(d)}
            for m, d in zip(metas, dists)
        ]

        # Gemini API key
        gemini_key = os.getenv("GEMINI_API_KEY")
        answer = None

        if gemini_key:
            try:
                from backend.text_enrich_gemini import _call_gemini
                prompt = f"""
                You are a precise assistant that answers questions using ONLY the provided CONTEXT.
                If the answer is not explicitly in the context, reply "I don't know".

                QUESTION:
                {q.query}

                CONTEXT:
                {context_text}

                Respond with a concise and factual paragraph.
                """
                answer = _call_gemini(prompt)
                if answer:
                    return {"answer": answer.strip(), "sources": sources}
            except Exception as e:
                print(f"[Gemini error] {e}")

        # Fallback: extractive summary
        snippet = "\n\n".join(d[:400] for d in docs)
        fallback_answer = snippet + ("\n\n[Truncated summary]" if len(snippet) > 1600 else "")
        return {"answer": fallback_answer, "sources": sources}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 🏠 Health Check
# =====================================================
@app.get("/")
def root():
    return {"status": "ok", "message": "AI Audiobook Backend is running!"}
