import os
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import chromadb

# -----------------------------
# 1. Split text into chunks
# -----------------------------
def split_text(text, chunk_size=400):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks

# -----------------------------
# 2. Load text files
# -----------------------------
text_folder = "./"
documents = []

for filename in os.listdir(text_folder):
    if filename.endswith("_extractedtext_output.txt"):
        with open(os.path.join(text_folder, filename), "r", encoding="utf-8") as f:
            full_text = f.read()
            chunks = split_text(full_text)
            documents.extend(chunks)

if not documents:
    print("No text files found!")
    exit()

print(f"✅ {len(documents)} chunks created from text files.")

# -----------------------------
# 3. Embeddings
# -----------------------------
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embedding_model.encode(documents).tolist()

# -----------------------------
# 4. ChromaDB
# -----------------------------
client = chromadb.Client()
collection = client.create_collection("audiobook_chunks")

for i, chunk in enumerate(documents):
    collection.add(
        ids=[str(i)],
        documents=[chunk],
        embeddings=[embeddings[i]]
    )

# -----------------------------
# 5. LLM
# -----------------------------
MODEL_NAME = "google/flan-t5-small"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

llm = pipeline(
    "text2text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=150
)

# -----------------------------
# 6. USER QUESTION (GENERALIZED)
# -----------------------------
query = input("\nEnter your question: ")

query_embedding = embedding_model.encode([query]).tolist()

results = collection.query(
    query_embeddings=query_embedding,
    n_results=2
)

context = " ".join(results["documents"][0])

# -----------------------------
# 7. PROMPT
# -----------------------------
prompt = f"""
Answer the question using only the context given.
Be concise and specific.

Context:
{context}

Question:
{query}

Answer:
"""

print("\nGenerating answer using LLM...\n")

response = llm(prompt)[0]["generated_text"]

print("="*80)
print("✅ FINAL ANSWER:\n")
print(response.strip())
print("="*80)
