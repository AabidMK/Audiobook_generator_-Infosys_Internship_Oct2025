from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Optional

from utils import ensure_dirs, UPLOADS_DIR
from extractor import extract_and_save
from llm_enrich import enrich_text
from tts import tts_synthesize

# watchdog is installed as a dependency via streamlit; we import it directly.
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent

SUPPORTED_EXTS = {".txt", ".pdf", ".docx", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}


def wait_for_complete(path: Path, timeout: float = 30.0, poll: float = 0.25) -> bool:
    """Wait until file stops growing (best-effort) or timeout."""
    end = time.time() + timeout
    last_size = -1
    while time.time() < end:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            time.sleep(poll)
            continue
        if size == last_size and size > 0:
            return True
        last_size = size
        time.sleep(poll)
    return False


class UploadsHandler(FileSystemEventHandler):
    def __init__(self, enrich: bool = False, tts_engine: Optional[str] = None, rate: int = 180, lang: str = "en") -> None:
        super().__init__()
        self.enrich = enrich
        self.tts_engine = tts_engine
        self.rate = rate
        self.lang = lang

    def _process(self, path: Path) -> None:
        if path.suffix.lower() not in SUPPORTED_EXTS:
            return
        if not wait_for_complete(path):
            print(f"Skipping (not stable): {path}")
            return
        print(f"Processing: {path}")
        out_txt = extract_and_save(path)
        print(f"Extracted text saved: {out_txt}")

        if self.enrich:
            text = out_txt.read_text(encoding="utf-8")
            enriched = enrich_text(text)
            out_txt.write_text(enriched, encoding="utf-8")
            print(f"Enriched text updated: {out_txt}")

        if self.tts_engine:
            text = out_txt.read_text(encoding="utf-8")
            audio_path = tts_synthesize(
                text,
                engine=self.tts_engine,  # type: ignore[arg-type]
                rate=self.rate if self.tts_engine == "pyttsx3" else None,
                language=self.lang if self.tts_engine == "gtts" else "en",
                basename=path.stem,
            )
            print(f"Audio saved: {audio_path}")

    def on_created(self, event):  # type: ignore[override]
        if isinstance(event, FileCreatedEvent):
            self._process(Path(event.src_path))

    def on_moved(self, event):  # type: ignore[override]
        if isinstance(event, FileMovedEvent):
            self._process(Path(event.dest_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch the uploads/ folder and auto-extract to outputs/text/")
    parser.add_argument("--enrich", action="store_true", help="Enrich text with OpenAI if OPENAI_API_KEY is set")
    parser.add_argument("--tts", choices=["pyttsx3", "gtts"], help="Generate speech for each file")
    parser.add_argument("--rate", type=int, default=180, help="pyttsx3 rate (wpm)")
    parser.add_argument("--lang", default="en", help="gTTS language (default: en)")
    args = parser.parse_args()

    ensure_dirs()
    uploads = UPLOADS_DIR
    uploads.mkdir(parents=True, exist_ok=True)

    handler = UploadsHandler(enrich=args.enrich, tts_engine=args.tts, rate=args.rate, lang=args.lang)
    observer = Observer()
    observer.schedule(handler, str(uploads), recursive=False)
    observer.start()

    print(f"Watching folder: {uploads}")
    print("Drop files to process automatically. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
