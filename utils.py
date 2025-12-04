# utils.py
from pathlib import Path

# Output directories for text and audio
OUTPUT_TEXT_DIR = Path("outputs/text")
OUTPUT_AUDIO_DIR = Path("outputs/audio")

def ensure_dirs():
    """Create required output directories if missing"""
    OUTPUT_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def file_stem(file_path: str) -> str:
    """Return file name without extension"""
    return Path(file_path).stem

def safe_filename(filename: str) -> str:
    """Generate a OS-safe filename"""
    import re
    filename = filename.lower().strip()
    filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
    return filename

def get_output_text_file(input_path: Path) -> Path:
    """Return path where extracted/enriched text should be saved"""
    name = safe_filename(file_stem(str(input_path)))
    return OUTPUT_TEXT_DIR / f"{name}.txt"

def get_output_audio_file(input_path: Path) -> Path:
    """Return path where audio file should be saved"""
    name = safe_filename(file_stem(str(input_path)))
    return OUTPUT_AUDIO_DIR / f"{name}.mp3"
