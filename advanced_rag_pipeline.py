import chromadb
from typing import List
from google import genai
import os
import json # Needed for parsing the structured response from the LLM

# --- CONFIGURATION (Must match create_db.py) ---
EMBEDDING_MODEL = "gemini-embedding-001"
# We use gemini-2.5-flash for both query expansion and final generation
GENERATION_MODEL = "gemini-2.5-flash" 
COLLECTION_NAME = "gemini_document_embeddings"
PERSIST_DIRECTORY = "my_vector_db"
N_RESULTS_PER_QUERY = 2 # Number of relevant chunks to retrieve for *each* expanded query
EXPANDED_QUERY_COUNT = 3 # Number of new queries the LLM will generate
# ------------------------------------------------

try:
    # Client is initialized to read GEMINI_API_KEY from environment
    client = genai.Client()
except Exception as e:
    print("ERROR: Failed to initialize Gemini Client. Ensure GEMINI_API_KEY is set.")
    print(f"Details: {e}")
    exit()


# -----------------------------------------------------------------
# CORE FUNCTION: Query Expansion (The new Advanced Chain)
# -----------------------------------------------------------------

def generate_expanded_queries(original_query: str) -> List[str]:
    """
    Uses the LLM to generate multiple, nuanced versions of the user's original query.
    This increases the chance of finding relevant documents during retrieval.
    """
    print(f"\n--- ADVANCED RAG CHAIN: Query Expansion ---")
    print(f"1. Asking LLM to generate {EXPANDED_QUERY_COUNT} related queries...")
    
    # 1. Define the desired structured output format (JSON Schema)
    query_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "A refined or related search query."}
            },
            "required": ["query"]
        }
    }
    
    system_prompt = (
        f"You are a query expansion expert. Your task is to generate {EXPANDED_QUERY_COUNT} "
        f"highly relevant, slightly diversified search queries based on the single user input. "
        "The goal is to cover different facets of the original question to maximize document retrieval recall. "
        "Respond ONLY with the generated JSON array."
    )
    
    try:
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=[{"role": "user", "parts": [{"text": original_query}]}],
            system_instruction={"parts": [{"text": system_prompt}]},
            config={
                "response_mime_type": "application/json",
                "response_schema": query_schema
            }
        )

        # 2. Parse the JSON response
        json_text = response.text.strip()
        expanded_queries_data = json.loads(json_text)
        
        # 3. Extract the list of query strings
        queries = [item['query'] for item in expanded_queries_data]
        
        print(f"2. LLM generated queries: {queries}")
        return queries

    except Exception as e:
        print(f"Query Expansion Failed. Details: {e}")
        # Fallback: if expansion fails, just use the original query
        return [original_query]


# -----------------------------------------------------------------
# 3. CORE RAG FUNCTIONS (Reused/Updated)
# -----------------------------------------------------------------

def get_query_embedding(text: str) -> List[float]:
    """Converts the query text into a vector using the Gemini embedding model."""
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[text] 
        )
        return response.embeddings[0].values 
    except Exception as e:
        print(f"Embedding API Error: {e}") 
        return []

def generate_llm_response(query: str, context: List[str]) -> str:
    """Constructs the final prompt and calls the Gemini LLM for the answer."""
    
    context_str = "\n".join(context)
    
    system_prompt = (
        "You are an expert Q&A assistant. Use ONLY the following context "
        "to answer the user's question. Be concise and professional. "
        "If the answer is not present in the context, state politely that the information "
        "is not available in the provided documents."
    )
    
    user_message = f"""
    CONTEXT (Retrieved from multiple searches):
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


def run_query_search(original_query: str):
    """
    Executes the advanced RAG pipeline: Query Expansion -> Multi-Retrieval -> Generation.
    """
    
    # 1. Initialize DB Client
    try:
        db_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        collection = db_client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error loading database: {e}. Ensure you ran the indexing script first.")
        return

    # 2. Execute Advanced RAG Chain: Query Expansion
    all_queries = generate_expanded_queries(original_query)

    # 3. Execute Multi-Retrieval & Gather Context
    all_retrieved_documents = set() # Use a set to automatically deduplicate chunks
    
    print("\n3. Starting Multi-Retrieval Phase...")
    for i, query in enumerate(all_queries):
        print(f"   - Searching with query #{i+1}: '{query}'")
        
        # Generate embedding for the specific expanded query
        query_embedding = get_query_embedding(query)
        if not query_embedding:
            continue

        # Perform semantic search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=N_RESULTS_PER_QUERY,
            include=['documents']
        )
        
        retrieved_documents = results.get('documents', [[]])[0]
        for doc in retrieved_documents:
            all_retrieved_documents.add(doc)
            
    final_context_list = list(all_retrieved_documents)

    if not final_context_list:
        print("Warning: No context was retrieved from the database using any query.")
        
    print(f"4. Total unique chunks retrieved: {len(final_context_list)}")
    print("\n--- RETRIEVED CONTEXT (Used for Generation) ---")
    for i, doc in enumerate(final_context_list):
        print(f"[{i+1}] {doc[:100]}...") # Print first 100 characters
    print("------------------------------------------------")
    
    # 4. Generate the final answer (Augmented Generation)
    final_answer = generate_llm_response(original_query, final_context_list)
    
    print("\n\n--- FINAL ANSWER ---")
    print(final_answer)
    print("--------------------")


if __name__ == "__main__":
    
    user_query = input("Enter your question about the document (try a complex one!): ")
    if user_query:
        run_query_search(user_query)
    else:
        print("No query entered. Exiting.")