import os
import re
import time
from pathlib import Path
from typing import Iterable, List, Optional

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUT_TEXT_DIR = BASE_DIR / "outputs" / "text"
OUTPUT_AUDIO_DIR = BASE_DIR / "outputs" / "audio"


def ensure_dirs() -> None:
    for d in [UPLOADS_DIR, OUTPUT_TEXT_DIR, OUTPUT_AUDIO_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str, max_len: int = 120) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    if len(name) > max_len:
        stem, ext = os.path.splitext(name)
        name = f"{stem[: max_len - len(ext) - 1]}{ext}"
    return name


def timestamped_filename(basename: str, suffix: str = "") -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    base = sanitize_filename(Path(basename).stem)
    if suffix and not suffix.startswith("_"):
        suffix = f"_{suffix}"
    return f"{base}_{ts}{suffix}"


def write_text_file(text: str, basename: str, folder: Optional[Path] = None) -> Path:
    folder = folder or OUTPUT_TEXT_DIR
    ensure_dirs()
    fname = timestamped_filename(basename, suffix="extracted") + ".txt"
    path = folder / fname
    path.write_text(text, encoding="utf-8")
    return path


def chunk_text(text: str, max_chars: int = 4000, overlap: int = 200) -> List[str]:
    text = text or ""
    if max_chars <= 0:
        return [text]
    if len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def file_stem(path: str | Path) -> str:
    return Path(path).stem


def with_ext(path: str | Path, ext: str) -> Path:
    p = Path(path)
    if not ext.startswith('.'):
        ext = '.' + ext
    return p.with_suffix(ext)
