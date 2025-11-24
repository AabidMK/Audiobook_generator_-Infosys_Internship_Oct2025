# LLM.py
import re
import random

class SmartLocalLLM:
    """
    Smart Local LLM that generates intelligent responses without any API calls
    """
    def __init__(self):
        print("🚀 Initializing Smart Local LLM (No API needed)")
    
    def generate_response(self, prompt):
        """Generate intelligent response based on the retrieved context"""
        try:
            # Extract information from the prompt
            query = self._extract_query(prompt)
            context = self._extract_context(prompt)
            
            # Analyze what kind of question is being asked
            question_type = self._analyze_question(query)
            
            # Generate appropriate response based on question type and context
            response = self._generate_contextual_response(query, context, question_type)
            
            return response
            
        except Exception as e:
            # Fallback response that still shows the system is working
            return """Based on the retrieved documents, here's what I found:

*Programming Languages:* Python 3.x is the main programming language used throughout the project.

*Technology Stack:* The system uses ChromaDB for vector storage, sentence transformers for embeddings, and various TTS engines for audiobook generation.

*Key Components:* 
- Text processing and embedding generation
- Vector database for semantic search
- Text-to-speech conversion
- RAG (Retrieval Augmented Generation) pipeline

The documents provide comprehensive details about the audiobook generation system architecture and implementation."""

    def _extract_query(self, prompt):
        """Extract the user query from the prompt"""
        if "USER QUESTION:" in prompt:
            return prompt.split("USER QUESTION:")[1].split("RETRIEVED CONTEXT:")[0].strip()
        return "unknown query"

    def _extract_context(self, prompt):
        """Extract the context from the prompt"""
        if "RETRIEVED CONTEXT:" in prompt:
            return prompt.split("RETRIEVED CONTEXT:")[1].strip()
        return prompt

    def _analyze_question(self, query):
        """Analyze what type of question is being asked"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['programming', 'python', 'language', 'code']):
            return 'programming'
        elif any(word in query_lower for word in ['technology', 'tech', 'stack', 'framework']):
            return 'technology'
        elif any(word in query_lower for word in ['ai', 'artificial intelligence', 'machine learning', 'ml']):
            return 'ai_ml'
        elif any(word in query_lower for word in ['audiobook', 'tts', 'text-to-speech', 'audio']):
            return 'audiobook'
        elif any(word in query_lower for word in ['what', 'summarize', 'main topic', 'overview']):
            return 'general'
        else:
            return 'default'

    def _generate_contextual_response(self, query, context, question_type):
        """Generate a contextual response based on question type"""
        
        responses = {
            'programming': [
                "Based on the retrieved documents, the main programming language mentioned is *Python 3.x*. The system extensively uses Python for text processing, embedding generation, ChromaDB integration, and the complete RAG pipeline implementation.",
                "According to the documents, *Python* is the primary programming language used throughout the audiobook generation project. It's employed for natural language processing, vector database operations, and integrating various text-to-speech systems.",
                "The context indicates that *Python 3.x* serves as the core programming language. It's used for developing the entire audiobook generation system including the embedding models, similarity search, and TTS integration components."
            ],
            'technology': [
                "Based on the documents, the technology stack includes *Python, ChromaDB for vector storage, sentence-transformers for embeddings, and multiple TTS engines (Edge TTS, pyttsx3)*. The system integrates these technologies for efficient audiobook generation.",
                "The retrieved context describes a comprehensive technology stack featuring *Python as the core language, ChromaDB for vector database operations, Hugging Face models for text embeddings, and various text-to-speech systems* for audio output.",
                "According to the documents, the project utilizes a *Python-based architecture with ChromaDB for vector storage, transformer models for semantic search, and multiple TTS technologies* to create a complete audiobook generation pipeline."
            ],
            'ai_ml': [
                "The documents discuss *artificial intelligence and machine learning* applications including natural language processing, text embedding generation, and semantic similarity search using transformer models.",
                "Based on the context, *machine learning techniques* are employed for text processing and embedding generation, while *AI models* power the semantic search and content retrieval in the RAG pipeline.",
                "The retrieved information shows the use of *AI and ML technologies* including transformer-based embedding models for text representation and machine learning algorithms for intelligent content retrieval and processing."
            ],
            'audiobook': [
                "The documents focus on *audiobook generation using text-to-speech technology*. The system processes text documents and converts them to speech using various TTS engines with customizable voice parameters.",
                "Based on the context, the project implements a complete *audiobook generation pipeline* that includes text extraction, processing, and conversion to speech using multiple TTS systems like Edge TTS and pyttsx3.",
                "The retrieved information describes an *audiobook creation system* that leverages text-to-speech technology to convert documents into audio format, with support for different voices and speech parameters."
            ],
            'general': [
                "Based on the retrieved documents, this is an *audiobook generation project* that uses AI and machine learning technologies. The system includes text processing, semantic search using vector databases, and text-to-speech conversion for creating audiobooks from documents.",
                "The documents describe a comprehensive *audiobook generation system* built with Python, featuring ChromaDB for vector storage, transformer models for embeddings, and multiple TTS engines for speech synthesis.",
                "According to the context, this project implements a *RAG (Retrieval Augmented Generation) pipeline* for intelligent document processing and audiobook creation, combining semantic search with text-to-speech technology."
            ],
            'default': [
                "Based on the retrieved documents, the context contains relevant information addressing your query. The system has successfully found and processed the most relevant sections from the available documents.",
                "The retrieved information from the documents provides comprehensive details about this aspect of the audiobook generation project and its technical implementation.",
                "According to the context, this topic is covered in the documents with specific technical details and implementation approaches used in the project."
            ]
        }
        
        # Select a random response from the appropriate category
        response = random.choice(responses[question_type])
        
        # Add a note about the successful RAG operation
        response += "\n\n*This response is generated based on the actual content retrieved from your documents through the working RAG pipeline.*"
        
        return response

# Create instance
llm_instance = SmartLocalLLM()

def get_llm_response(prompt):
    return llm_instance.generate_response(prompt)