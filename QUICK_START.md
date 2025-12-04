# Quick Start Guide

## Your API Key is Ready! 🎉

Your Google Gemini API key has been configured: `AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak`

## Option 1: Set API Key as Environment Variable (Recommended)

Run this command to permanently add it to your shell:

```bash
./setup_api.sh
```

Or manually add to your `~/.zshrc` or `~/.bashrc`:
```bash
export GEMINI_API_KEY="AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak"
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

## Option 2: Pass API Key When Running

You can pass the API key directly when running the script:

```bash
source venv/bin/activate
python main.py your_file.pdf --api-key AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak
```

## Ready to Use!

1. **Extract text from any file**:
   ```bash
   source venv/bin/activate
   python main.py document.pdf
   python main.py document.docx
   python main.py document.txt
   python main.py image.png
   ```

2. **The system will**:
   - Extract text → Save to `extracted_texts/` folder
   - Enrich text using Gemini API → Save to `enriched_texts/` folder

## Test It Out

Try with a sample file:
```bash
source venv/bin/activate
python main.py your_test_file.pdf
```

## Note About API Quotas

If you see quota exceeded errors, wait a few minutes and try again. Free tier has rate limits. For production use, consider upgrading your Google AI plan.

## Troubleshooting

- **Import errors**: Make sure you've selected the virtual environment interpreter in your IDE (see SETUP.md)
- **API errors**: Check your internet connection and API key validity
- **Quota errors**: Wait a few minutes or check your usage at https://ai.dev/usage

