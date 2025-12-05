import chromadb
from typing import List
from google import genai
import os

# --- CONFIGURATION (Must match create_db.py) ---
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-2.5-flash" # The model used for generating the final text
COLLECTION_NAME = "gemini_document_embeddings"
PERSIST_DIRECTORY = "my_vector_db"
N_RESULTS = 3 # Number of relevant chunks to retrieve from the database
# ------------------------------------------------

try:
    # Client is initialized to read GEMINI_API_KEY from environment
    client = genai.Client()
except Exception as e:
    print("ERROR: Failed to initialize Gemini Client. Ensure GEMINI_API_KEY is set.")
    print(f"Details: {e}")
    exit()

# -----------------------------------------------------------------
# 1. RETRIEVAL: Generate Query Embedding
# -----------------------------------------------------------------

def get_query_embedding(text: str) -> List[float]:
    """Converts the query text into a vector using the Gemini embedding model."""
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[text] 
        )
        
        # Correctly extracts the list of floats (the vector)
        return response.embeddings[0].values 
        
    except Exception as e:
        print(f"Embedding API Error: {e}") 
        return []

# -----------------------------------------------------------------
# 2. GENERATION: Call LLM
# -----------------------------------------------------------------
def generate_llm_response(query: str, context: List[str]) -> str:
    """Constructs the prompt and calls the Gemini LLM for the final answer."""
    
    # CORRECTED: Uses the standard Python .join method
    context_str = "\n".join(context)
    
    system_prompt = (
        "You are an expert Q&A assistant. Use ONLY the following context "
        "to answer the user's question. Be concise and professional. "
        "If the answer is not present in the context, state politely that the information "
        "is not available in the provided documents."
    )
    
    user_message = f"""
    CONTEXT:
    ---
    {context_str}
    ---
    USER QUESTION: {query}
    """
    
    try:
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=[
                {"role": "user", "parts": [{"text": system_prompt}]},
                {"role": "user", "parts": [{"text": user_message}]}
            ]
        )
        return response.text
        
    except Exception as e:
        return f"LLM API Call Failed. Details: {e}"


def run_query_search(query_text: str):
    """Loads the database, retrieves context, and calls the LLM."""
    
    # 1. Load the database (from my_vector_db)
    try:
        db_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        collection = db_client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error loading database: {e}. Ensure you ran create_db.py first.")
        return

    # 2. Generate query embedding
    query_embedding = get_query_embedding(query_text)
    if not query_embedding:
        print("Failed to generate query embedding. Cannot search.")
        return

    # 3. Perform retrieval (Semantic Search on my_vector_db)
    print(f"\nSearching for top {N_RESULTS} results relevant to: '{query_text}'")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=N_RESULTS,
        include=['documents']
    )
    
    retrieved_documents = results.get('documents', [[]])[0]

    if not retrieved_documents:
        print("Warning: No context was retrieved from the database.")
    
    # 4. Generate the final answer (Augmented Generation)
    final_answer = generate_llm_response(query_text, retrieved_documents)
    
    print("\n\n--- FINAL ANSWER ---")
    print(final_answer)
    print("--------------------")


if __name__ == "__main__":
    
    user_query = input("Enter your question about the document: ")
    if user_query:
        run_query_search(user_query)
    else:
        print("No query entered. Exiting.")