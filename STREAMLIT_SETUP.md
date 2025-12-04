# Streamlit Setup Guide

## Issue: Module Not Found Error

If you see `ModuleNotFoundError: No module named 'edge_tts'` or similar errors, it means Streamlit is using a different Python interpreter than your virtual environment.

## Solution 1: Use the Run Script (Recommended)

Always use the provided script which ensures the correct Python interpreter:

```bash
cd "/Users/adityakachhot/audio gen"
./run_streamlit.sh
```

## Solution 2: Manual Activation

Make sure to activate the virtual environment BEFORE running Streamlit:

```bash
cd "/Users/adityakachhot/audio gen"
source venv/bin/activate

# Verify you're using venv Python
which python
# Should show: /Users/adityakachhot/audio gen/venv/bin/python

# Run Streamlit using venv Python
python -m streamlit run app.py
```

## Solution 3: Install Packages in Current Environment

If you want to use Anaconda Python instead:

```bash
# Activate your Anaconda environment (if using one)
conda activate your_env_name

# Install all requirements
pip install -r requirements.txt

# Run Streamlit
streamlit run app.py
```

## Verify Installation

Check if all packages are installed:

```bash
source venv/bin/activate
python -c "import edge_tts; import streamlit; import chromadb; print('All packages installed!')"
```

## Troubleshooting

1. **Check which Python Streamlit is using:**
   ```bash
   which streamlit
   ```

2. **If it's not using venv Python, use:**
   ```bash
   source venv/bin/activate
   python -m streamlit run app.py
   ```

3. **Reinstall packages if needed:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

