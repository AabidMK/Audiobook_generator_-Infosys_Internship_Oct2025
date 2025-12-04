# Setup Guide - Fixing Import Errors

## The Problem
If you're seeing "could not be resolved" errors for imports like:
- `pdfplumber`
- `pytesseract`
- `PIL` (Pillow)
- `docx`
- `google.generativeai`

This means your IDE isn't using the virtual environment where the packages are installed.

## Solution: Configure Your IDE

### Option 1: VS Code / Cursor
1. Open the Command Palette (Cmd+Shift+P on Mac, Ctrl+Shift+P on Windows/Linux)
2. Type "Python: Select Interpreter"
3. Select the interpreter from the virtual environment:
   - Choose `./venv/bin/python` or
   - Look for `Python 3.13.x ('venv': venv) ./venv/bin/python`

The IDE will now recognize all installed packages!

### Option 2: PyCharm
1. Go to File → Settings → Project → Python Interpreter
2. Click the gear icon → Add Interpreter → Existing Environment
3. Select: `./venv/bin/python`
4. Click OK

### Option 3: Activate Virtual Environment in Terminal
If running from terminal, always activate the virtual environment first:

```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

Then run your scripts:
```bash
python main.py your_file.pdf
```

## Verify Installation
Run this to verify all packages are installed:
```bash
source venv/bin/activate  # Activate venv first
python -c "import pdfplumber; import pytesseract; from PIL import Image; from docx import Document; import google.generativeai; print('All imports successful!')"
```

## Quick Start Script
You can also use the provided `run.sh` script which automatically activates the venv.

