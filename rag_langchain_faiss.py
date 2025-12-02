

import os
import faiss
import pickle
import numpy as np
from dotenv import load_dotenv
load_dotenv()

from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate


MODEL_NAME = "gpt-4o-mini"
EMBED_MODEL = "all-MiniLM-L6-v2"

INDEX_FILE = "faiss_index.bin"
META_FILE = "faiss_metadata.pkl"

TOP_K = 5




def load_faiss():
    print(" Loading FAISS index & metadata...")

    if not os.path.exists(INDEX_FILE):
        raise FileNotFoundError("ERROR: faiss_index.bin not found")

    index = faiss.read_index(INDEX_FILE)

    with open(META_FILE, "rb") as f:
        metadata = pickle.load(f)

    return index, metadata



def embed_query(query):
    print(" Generating query embedding...")
    model = SentenceTransformer(EMBED_MODEL)
    embedding = model.encode([query])
    return np.array(embedding).astype("float32")




def search_index(index, query_vector, k=TOP_K):
    print(f" Searching FAISS (top {k})...")
    distances, indices = index.search(query_vector, k)
    return indices[0]



def generate_answer(query, chunks):
    print(" Querying LLM...")

    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0
    )

    STRICT_PROMPT = """
You MUST answer the question using ONLY the PDF context provided.

RULES:
1. Use ONLY information from the context.
2. If the answer is NOT present, reply exactly: ANSWER NOT FOUND IN PDF.
3. Do NOT guess.

CONTEXT:
{context}

QUESTION:
{question}
"""

    prompt = PromptTemplate(
        template=STRICT_PROMPT,
        input_variables=["context", "question"]
    )

    formatted = prompt.format(
        context="\n\n".join(chunks),
        question=query
    )

    response = llm.invoke(formatted)
    return response.content.strip()




def answer_query(query):
    print("\n" + "=" * 60)
    print("USER QUERY:", query)
    print("=" * 60)

    index, metadata = load_faiss()

    qvec = embed_query(query)
    top_ids = search_index(index, qvec, TOP_K)

    retrieved_chunks = [metadata["chunks"][i] for i in top_ids]

    print("\n Retrieved Chunks:")
    for i, c in enumerate(retrieved_chunks, 1):
        print(f"\n[{i}] {c[:200]}...\n")

    answer = generate_answer(query, retrieved_chunks)

    print("\n" + "=" * 60)
    print("FINAL ANSWER:")
    print(answer)
    print("=" * 60)

    return answer




if __name__ == "__main__":
    answer_query("What role does the LLM play in the system?")
