# [file name]: qa_chain.py
# [file content begin]
import os
from typing import List, Tuple

def answer_question(question: str, context_chunks: List[Tuple[str, float]]) -> str:
    """Answer question based on context chunks using OpenAI or fallback."""
    # Combine context chunks
    context = "\n\n".join([chunk[0] for chunk in context_chunks])
    
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key
            
            prompt = f"""Based on the following context, answer the question. If the answer cannot be found in the context, say "I don't have enough information to answer this question based on the document."

Context:
{context}

Question: {question}

Answer:"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI QA failed: {e}")
    
    # Fallback: simple keyword-based answering
    return fallback_qa(question, context_chunks)

def fallback_qa(question: str, context_chunks: List[Tuple[str, float]]) -> str:
    """Simple fallback question answering."""
    if not context_chunks:
        return "I don't have enough information to answer this question. No relevant documents were found."
    
    # Simple keyword matching
    question_lower = question.lower()
    best_chunk = max(context_chunks, key=lambda x: x[1])
    
    # Very basic response generation
    words = question_lower.split()
    if any(word in best_chunk[0].lower() for word in ['what', 'who', 'when', 'where', 'why', 'how']):
        return f"Based on the document: {best_chunk[0][:300]}..."
    else:
        return f"The document contains relevant information: {best_chunk[0][:400]}..."
# [file content end]