import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
import sys
from dotenv import load_dotenv  # <--- NEW IMPORT

# --- CONFIGURATION ---
# 1. Load environment variables from .env file
load_dotenv()  # <--- THIS READS YOUR .ENV FILE

# 2. Verify the key is loaded
if "GEMINI_API_KEY" not in os.environ:
    print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
    print("Please ensure you have a .env file with: GOOGLE_API_KEY=your_key_here")
    sys.exit(1)

# 3. Configure the Gemini Client
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def query_rag(user_question):
    print(f"🔎 Processing Query: '{user_question}'")
    
    # --- STEP 1: RETRIEVAL (The "R") ---
    
    # A. Connect to the Database
    client = chromadb.PersistentClient(path="my_vectordb")
    collection = client.get_collection(name="document_chunks")
    
    # B. Load the Embedding Model
    print("⏳ Loading embedding model...")
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # C. Embed the User's Question
    query_embedding = embed_model.encode([user_question]).tolist()
    
    # D. Query the Database for Top 5 Results
    print("📚 Searching database for relevant chunks...")
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=5
    )
    
    retrieved_chunks = results['documents'][0]
    
    if not retrieved_chunks:
        print("❌ No relevant information found in the database.")
        return

    # --- STEP 2: AUGMENTATION (The "A") ---
    context_block = "\n\n".join(retrieved_chunks)
    
    rag_prompt = f"""
    You are a helpful assistant. Use the provided Context to answer the User's Question.
    If the answer is not in the context, strictly state "I cannot answer this based on the provided documents."
    
    Context:
    {context_block}
    
    User Question: 
    {user_question}
    """
    
    # --- STEP 3: GENERATION (The "G") ---
    print("🤖 Sending to Gemini for rephrasing...")
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(rag_prompt)
    
    print("\n" + "="*50)
    print(f"📝 ANSWER:")
    print("-" * 50)
    print(response.text)
    print("="*50)
    
    # Optional: Show sources
    print("\n🔍 Context Sources Used:")
    for i, chunk in enumerate(retrieved_chunks):
        print(f"[{i+1}] {chunk[:100]}...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        query_rag(query)
    else:
        query_rag("What is Algo Trading?")