# LangChain RAG Integration

This document explains the LangChain-based RAG implementation (`rag_langchain.py`) and compares it with the custom implementation (`rag_query.py`).

## Overview

We now have **two RAG implementations**:

1. **Custom RAG** (`rag_query.py`): Lightweight, direct ChromaDB + Gemini integration
2. **LangChain RAG** (`rag_langchain.py`): Framework-based with LCEL chains

Both implementations work with the same vector database and produce high-quality answers.

## Installation

### LangChain Packages

```powershell
pip install langchain langchain-chroma langchain-google-genai langchain-community
```

### All Dependencies

```powershell
pip install -r requirements.txt
```

## Usage

### Setup API Key

The API key is stored in the `.env` file (already configured). No need to set it in terminal!

If you need to update it, edit the `.env` file:
```
GOOGLE_API_KEY = "your-api-key-here"
```

### Basic Query

```powershell
# Simply run the query - API key loads automatically from .env
python rag_langchain.py --query "What is the objective?" --top-k 3 --use-native
```

### With Source Citations

```powershell
python rag_langchain.py --query "What are the milestones?" --top-k 5 --use-native --show-sources
```

### Verbose Logging

```powershell
python rag_langchain.py --query "Explain the workflow" --top-k 3 --use-native --verbose
```

### Google Embeddings (Alternative)

```powershell
# Without --use-native flag, uses Google embeddings (models/embedding-001)
python rag_langchain.py --query "What technology is used?" --top-k 5
```

## Key Features

### LCEL Chain Pattern

LangChain uses **Expression Language (LCEL)** for chain composition:

```python
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

This creates a clean pipeline: **Retrieve → Format → Prompt → LLM → Parse**

### Two Embedding Strategies

1. **Native (HuggingFace)**: `--use-native` flag
   - Model: `sentence-transformers/all-MiniLM-L6-v2`
   - Dimensions: 384
   - Compatible with existing vector database
   - **Recommended** for backward compatibility

2. **Google Embeddings**: Default (no flag)
   - Model: `models/embedding-001`
   - Dimensions: 768
   - Better semantic understanding
   - Requires re-generating vector database

### Retriever Configuration

```python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": top_k}
)
```

Supports multiple search types:
- `similarity`: Cosine similarity (default)
- `mmr`: Maximum Marginal Relevance (diversity)
- `similarity_score_threshold`: Filter by minimum score

## Comparison: Custom vs LangChain

| Feature | Custom (`rag_query.py`) | LangChain (`rag_langchain.py`) |
|---------|-------------------------|--------------------------------|
| **Dependencies** | Minimal (chromadb, google-generativeai) | Full LangChain stack |
| **Code Size** | ~250 lines | ~200 lines (cleaner with LCEL) |
| **Performance** | Slightly faster (~10-20ms) | Minimal overhead |
| **Extensibility** | Manual implementation needed | Built-in patterns |
| **Async Support** | Manual async implementation | Native async chains |
| **Streaming** | Manual implementation | Built-in streaming |
| **Chain Composition** | Manual orchestration | LCEL operators |
| **Observability** | Custom logging | LangSmith integration |
| **Best For** | Production, lightweight, known requirements | Prototyping, complex workflows, rapid iteration |

## When to Use Each

### Use Custom RAG (`rag_query.py`) When:
- You need minimal dependencies
- Performance is critical (every millisecond counts)
- Your RAG pipeline is stable and well-defined
- You prefer explicit control over every step
- Deploying to resource-constrained environments

### Use LangChain RAG (`rag_langchain.py`) When:
- You're prototyping or experimenting
- You need advanced features (streaming, async, agents)
- You want to compose complex chains
- You're building multi-step workflows
- You want built-in observability with LangSmith
- You need to integrate with LangChain ecosystem

## Architecture

### LangChain Components

1. **Vector Store**: `Chroma` wrapper with embedding function
2. **Retriever**: `.as_retriever()` converts vector store to retriever
3. **Prompt Template**: `ChatPromptTemplate` with variables
4. **LLM**: `ChatGoogleGenerativeAI` wrapper for Gemini
5. **Output Parser**: `StrOutputParser` for clean string output
6. **Chain**: LCEL composition with `|` operator

### Data Flow

```
User Query
    ↓
Embeddings (HuggingFace or Google)
    ↓
Retriever (ChromaDB similarity search)
    ↓
Format Documents (text + metadata)
    ↓
Prompt Template (system + user message)
    ↓
LLM (Gemini 2.5 Flash)
    ↓
Output Parser (clean string)
    ↓
Final Answer
```

## Advanced Features (Future)

### 1. Streaming Responses

```python
for chunk in rag_chain.stream(query):
    print(chunk, end="", flush=True)
```

### 2. Async Execution

```python
answer = await rag_chain.ainvoke(query)
```

### 3. Multi-Query Fusion

```python
from langchain.retrievers import MultiQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm
)
```

### 4. Conversation History

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
chain = ConversationalRetrievalChain.from_llm(llm, retriever, memory=memory)
```

### 5. Hybrid Search (Keyword + Semantic)

```python
from langchain.retrievers import EnsembleRetriever

ensemble = EnsembleRetriever(
    retrievers=[keyword_retriever, semantic_retriever],
    weights=[0.3, 0.7]
)
```

## Embedding Model Compatibility

### Current Vector Database
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimensions: 384
- Created by: `embeddings.py` and `vectordb_save.py`

### Using with LangChain

**Option 1: Native Embeddings (Recommended)**
```bash
python rag_langchain.py --query "..." --use-native
```
- Uses same model as existing database
- Perfect compatibility
- No re-generation needed

**Option 2: Google Embeddings**
```bash
python rag_langchain.py --query "..."
```
- Uses Google `models/embedding-001`
- Better semantic understanding
- **Requires re-generating vector database**

### Migrating to Google Embeddings

If you want to use Google embeddings:

1. Create new collection:
```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

vectorstore = Chroma(
    collection_name="audiobook_embeddings_google",
    embedding_function=embeddings,
    persist_directory="./vectordb"
)
```

2. Add documents (requires source text files)
3. Update `rag_langchain.py` to use new collection

## Troubleshooting

### "No module named 'langchain.schema'"

**Solution**: Update imports to use `langchain_core`:
```python
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
```

### "HuggingFaceEmbeddings deprecated"

**Warning (non-critical)**: LangChain recommends `langchain-huggingface` package.

**To fix** (optional):
```bash
pip install langchain-huggingface
```
Then update import:
```python
from langchain_huggingface import HuggingFaceEmbeddings
```

### "Embedding dimension mismatch"

**Cause**: Trying to query with Google embeddings (768-dim) on HuggingFace database (384-dim).

**Solution**: Use `--use-native` flag or re-generate database with Google embeddings.

### "Rate limit exceeded"

**Cause**: Too many Gemini API calls.

**Solution**:
- Wait a minute before retrying
- Reduce `top_k` parameter
- Consider caching results

## Performance Tips

1. **Use Native Embeddings**: `--use-native` avoids Google API call overhead
2. **Optimize top-k**: Start with 3-5, increase only if answers lack detail
3. **Batch Queries**: Process multiple questions in one session to reuse vector store
4. **Enable Caching**: ChromaDB caches recent queries automatically
5. **GPU Acceleration**: Use GPU for embeddings if available

## Next Steps

- [ ] Implement streaming responses
- [ ] Add conversation memory
- [ ] Set up LangSmith observability
- [ ] Try multi-query fusion
- [ ] Experiment with hybrid search
- [ ] Add async support for batch processing

## Resources

- [LangChain Documentation](https://python.langchain.com/docs/)
- [ChromaDB Integration Guide](https://docs.langchain.com/oss/python/langchain/knowledge-base#chroma)
- [LCEL Documentation](https://python.langchain.com/docs/expression_language/)
- [Gemini API Docs](https://ai.google.dev/docs)

## License

Same as parent project.
