#!/bin/bash
# Script to run Streamlit app

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Verify we're using the venv Python
if [[ "$VIRTUAL_ENV" != "$SCRIPT_DIR/venv" ]]; then
    echo "Error: Virtual environment not activated properly"
    exit 1
fi

# Use the venv's Python to run Streamlit
python -m streamlit run app.py

