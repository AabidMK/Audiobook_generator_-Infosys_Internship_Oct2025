# RAG Query Quick Start Guide

## Setup

The API key is automatically loaded from the `.env` file. No manual setup needed!

If you need to update the API key, edit `.env`:
```
GOOGLE_API_KEY = "your-api-key-here"
```

### Alternative: Manual Setup (Optional)

If you prefer to set it per PowerShell session:
```powershell
.\setup_env.ps1
```

Or manually:
```powershell
$env:GOOGLE_API_KEY = "AIzaSyAa2vAQjxEFJMwowuN25BFbOTbjkfTn84U"
```

## Usage Examples

### Basic Query
```powershell
python rag_query.py --query "What is the objective?" --top-k 3
```

### With Source Citations
```powershell
python rag_query.py --query "What are the milestones?" --top-k 5 --show-sources
```

### Different Number of Results
```powershell
# Get top 2 most relevant chunks
python rag_query.py --query "What technology is used?" --top-k 2

# Get top 10 for comprehensive answer
python rag_query.py --query "Explain the workflow" --top-k 10
```

### Custom Collection
```powershell
python rag_query.py --query "Your question" --collection "my_collection" --db-dir "./vectordb"
```

### Force Specific LLM Provider
```powershell
# Use Gemini (default)
python rag_query.py --query "Your question" --provider gemini

# Use OpenAI (requires OPENAI_API_KEY)
python rag_query.py --query "Your question" --provider openai
```

## How It Works

1. **Your Question** → Converted to embedding vector (384 dimensions)
2. **Vector Search** → ChromaDB finds top-k most similar text chunks
3. **Context Building** → Retrieved chunks assembled with metadata
4. **LLM Generation** → Gemini 2.5 Flash answers based ONLY on retrieved context
5. **Answer** → Accurate, grounded response with optional source citations

## Tips

- **top-k = 3-5**: Good for specific questions
- **top-k = 8-10**: Better for complex/multi-part questions
- **--show-sources**: See which chunks were used (useful for verification)
- Distance < 1.0 = very relevant, Distance > 2.0 = less relevant

## Troubleshooting

### "No LLM available"
→ API key not set. Run `.\setup_env.ps1` or set `$env:GOOGLE_API_KEY`

### "Collection not found"
→ Run embeddings first: `python vectordb_save.py "path/to/embeddings.csv"`

### "Quota exceeded"
→ Wait 1 hour for free tier reset or use different API key

## Current Setup

- **Model**: Gemini 2.5 Flash
- **Collection**: audiobook_embeddings
- **DB Location**: ./vectordb
- **Embedding Dimension**: 384 (all-MiniLM-L6-v2)
