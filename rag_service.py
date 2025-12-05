import chromadb
from typing import List, Tuple, Set, Optional
from google import genai
from google.genai import types 
import json 
import os
import time

# --- CONFIGURATION (Must match app.py) ---
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-2.5-flash" 
COLLECTION_NAME = "gemini_document_embeddings"
PERSIST_DIRECTORY = "my_vector_db"
N_RESULTS_PER_QUERY = 2 
EXPANDED_QUERY_COUNT = 3
# ------------------------------------------------

# -----------------------------------------------------------------
# HELPER: Database Connection
# -----------------------------------------------------------------

def get_chroma_collection() -> Optional[chromadb.Collection]:
    """
    Initializes ChromaDB client and attempts to retrieve the collection.
    Returns the collection object or None if the collection doesn't exist.
    """
    try:
        db_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        if COLLECTION_NAME not in [c.name for c in db_client.list_collections()]:
            print(f"Collection '{COLLECTION_NAME}' does not exist yet. Please upload a document.")
            return None
            
        collection = db_client.get_collection(name=COLLECTION_NAME)
        if collection.count() == 0:
            print(f"Collection '{COLLECTION_NAME}' is empty.")
            return None
            
        return collection
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        return None


# -----------------------------------------------------------------
# 1. RETRIEVAL: Generate Query Embedding
# -----------------------------------------------------------------

def get_query_embedding(text: str, client: genai.Client) -> List[float]:
    """Converts the query text into a vector using the Gemini embedding model."""
    # Implement simple exponential backoff for robustness against API rate limits
    max_retries = 3
    delay = 1
    for attempt in range(max_retries):
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=[text] 
                # task_type="RETRIEVAL_QUERY" REMOVED
            )
            return response.embeddings[0].values 
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Embedding API Error (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"Embedding API Error: {e}") 
                return []
    return []

# -----------------------------------------------------------------
# 2. CORE ADVANCED RAG FUNCTION: Query Expansion
# -----------------------------------------------------------------

def generate_expanded_queries(original_query: str, client: genai.Client) -> List[str]:
    """
    Uses the LLM to generate multiple, nuanced versions of the user's original query 
    using structured JSON output.
    """
    
    query_schema = types.Schema(
        type=types.Type.ARRAY,
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(type=types.Type.STRING, description="A refined or related search query.")
            },
            required=["query"]
        )
    )
    
    system_prompt = (
        f"You are a query expansion expert. Your task is to generate {EXPANDED_QUERY_COUNT} "
        f"highly relevant, slightly diversified search queries based on the single user input. "
        "The goal is to cover different facets of the original question to maximize document retrieval recall. "
        "Respond ONLY with the generated JSON array."
    )
    
    try:
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=[original_query],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=query_schema
            )
        )

        json_text = response.text.strip()
        expanded_queries_data = json.loads(json_text)
        
        queries = [item['query'] for item in expanded_queries_data]
        queries.insert(0, original_query) # Always include the original query
        
        return queries

    except Exception as e:
        print(f"Query Expansion Failed. Details: {e}")
        return [original_query]

# -----------------------------------------------------------------
# 3. GENERATION: Call LLM
# -----------------------------------------------------------------

def generate_llm_response(query: str, context: List[str], client: genai.Client) -> str:
    """Constructs the final prompt and calls the Gemini LLM for the answer."""
    
    context_str = "\n".join(context)
    
    system_prompt = (
        "You are an expert Q&A assistant. Use ONLY the following context "
        "to answer the user's question. **Ensure you address all aspects of the query completely and concisely.** "
        "If the answer is not present in the context, state politely that the information "
        "is not available in the provided documents."
    )
    
    user_message = f"""
    CONTEXT (Retrieved from indexed documents via Advanced RAG):
    ---
    {context_str}
    ---
    USER QUESTION: {query}
    """
    
    try:
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=[user_message],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        )
        return response.text
    except Exception as e:
        return f"LLM API Call Failed. Details: {e}"

# -----------------------------------------------------------------
# 4. MAIN EXPOSED FUNCTION
# -----------------------------------------------------------------

def run_query_search(original_query: str, client: genai.Client) -> Tuple[str, List[str]]:
    """
    Executes the advanced RAG pipeline (Expansion -> Multi-Retrieval -> Generation) 
    and returns the final answer and context list.
    """
    
    # 1. Check for Collection existence
    collection = get_chroma_collection()
    if collection is None:
        return "Error: Document collection not found. Please upload and process a document in the 'Upload & Audio Generation' tab first.", []

    # 2. Execute Advanced RAG Chain: Query Expansion
    all_queries = generate_expanded_queries(original_query, client)

    # 3. Execute Multi-Retrieval & Gather Context
    all_retrieved_documents: Set[str] = set() 
    
    for query in all_queries:
        query_embedding = get_query_embedding(query, client)
        if not query_embedding:
            continue

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
        return "I could not find any relevant information for that question in the indexed documents, even with advanced search techniques.", []
        
    # 4. Generate the final answer (Augmented Generation)
    final_answer = generate_llm_response(original_query, final_context_list, client)
    
    return final_answer, final_context_list