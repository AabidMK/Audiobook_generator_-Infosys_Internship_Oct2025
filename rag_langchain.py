"""
RAG with LangChain + ChromaDB + Gemini
Following LangChain best practices for retrieval-augmented generation

API Key: Automatically loaded from .env file (GOOGLE_API_KEY)

Usage:
    python rag_langchain.py --query "What is the objective?" --top-k 5
    python rag_langchain.py --query "Explain the workflow" --top-k 3 --verbose
    python rag_langchain.py --query "What are the milestones?" --show-sources
"""

import os
import argparse
from typing import List
from dotenv import load_dotenv

load_dotenv()

# LangChain imports
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_vectorstore(
    collection_name: str = "audiobook_embeddings",
    persist_directory: str = "./vectordb"
) -> Chroma:
    """
    Load existing ChromaDB vector store with HuggingFace embeddings (all-MiniLM-L6-v2).
    Uses local embeddings - no API calls needed.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory
    )
    
    logger.info(f"Loaded vector store with HuggingFace embeddings: {collection_name}")
    return vectorstore


def create_rag_chain(
    vectorstore: Chroma,
    top_k: int = 5,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.2
):
    """
    Create LangChain RAG chain with retriever + LLM + prompt template.
    
    Chain flow:
    1. User query → Retriever (fetch top-k docs)
    2. Format context + query → Prompt template
    3. LLM generates answer based on context
    4. Parse output as string
    """
    
    # Create retriever from vectorstore
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )
    
    # Define prompt template
    template = """You are a precise assistant answering questions using ONLY the provided context.
If the answer is not in the context, say you don't know based on the document.
Be concise, accurate, and avoid speculation.

Context:
{context}

Question: {question}

Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Initialize Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Format retrieved documents
    def format_docs(docs: List[Document]) -> str:
        formatted = []
        for i, doc in enumerate(docs, 1):
            metadata = doc.metadata
            source = metadata.get('source', 'unknown')
            idx = metadata.get('index', i)
            formatted.append(f"[Chunk {i} | source={source} | idx={idx}]\n{doc.page_content}")
        return "\n\n".join(formatted)
    
    # Build RAG chain using LCEL (LangChain Expression Language)
    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain, retriever


def query_with_sources(
    query: str,
    vectorstore: Chroma,
    top_k: int = 5,
    show_sources: bool = False,
    verbose: bool = False
) -> str:
    """
    Query the RAG system and optionally show source documents.
    """
    # Create chain and retriever
    rag_chain, retriever = create_rag_chain(vectorstore, top_k=top_k)
    
    # Get answer
    if verbose:
        logger.info(f"Query: {query}")
        logger.info(f"Retrieving top-{top_k} documents...")
    
    answer = rag_chain.invoke(query)
    
    # Optionally append sources
    if show_sources:
        docs = retriever.invoke(query)
        sources = "\n\nSources:\n"
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata
            source = meta.get('source', 'unknown')
            idx = meta.get('index', '?')
            # Note: distance not directly available in this retrieval mode
            sources += f"- {i}. source={source} | idx={idx}\n"
        answer += sources
    
    return answer


def main():
    parser = argparse.ArgumentParser(
        description="RAG query using LangChain + ChromaDB + Gemini"
    )
    parser.add_argument("--query", required=True, help="User query text")
    parser.add_argument("--top-k", type=int, default=5, help="Top K documents to retrieve")
    parser.add_argument("--collection", default="audiobook_embeddings", help="ChromaDB collection name")
    parser.add_argument("--db-dir", default="./vectordb", help="ChromaDB persist directory")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model name")
    parser.add_argument("--show-sources", action="store_true", help="Show source documents")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Check API key (loaded from .env file)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error(
            "GOOGLE_API_KEY not found in .env file!\n"
            "Please add the following line to your .env file:\n"
            "GOOGLE_API_KEY = \"your-api-key-here\""
        )
        return
    
    try:
        # Load vector store with Google Gemini embeddings
        vectorstore = get_vectorstore(args.collection, args.db_dir)
        
        # Query
        answer = query_with_sources(
            query=args.query,
            vectorstore=vectorstore,
            top_k=args.top_k,
            show_sources=args.show_sources,
            verbose=args.verbose
        )
        
        print("\n" + "="*70)
        print("ANSWER")
        print("="*70)
        print(answer)
        print("="*70)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        raise


if __name__ == "__main__":
    main()