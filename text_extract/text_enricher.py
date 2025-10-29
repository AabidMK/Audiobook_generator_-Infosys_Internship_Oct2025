import re
import json
from pathlib import Path
from typing import List, Dict

# Optional: use nltk for sentence splitting if available (recommended)
try:
    import nltk
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
except ImportError:
    nltk = None



# ---------- Default config (overwritten by JSON config if provided) ----------
DEFAULT_CONFIG = {
    "greeting": "Hello listeners, welcome...",
    "auto_summary_template": "In this audio, you will learn about: {first_line_summary}",
    "max_sentence_length": 140,             # characters before attempting to split
    "split_on_commas_after": 60,            # split long sentences at commas if prior length > this
    "pause_token": "...",
    "abbreviations": {
        "e.g.": "for example",
        "eg.": "for example",
        "i.e.": "that is",
        "etc.": "and so on",
        "vs.": "versus",
        "mr.": "mister",
        "mrs.": "missus",
        "dr.": "doctor"
    },
    "list_indicators": ["-", "*", "•", "–", "—", "1.", "1)"],
    "list_to_spoken_prefix": "First, ",
    "list_item_connector": ", then ",
    "min_words_for_summary": 3
}

# ---------- Helper functions ----------
def load_config(path: str = None) -> Dict:
    if path and Path(path).exists():
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Merge defaults with provided
        merged = DEFAULT_CONFIG.copy()
        merged.update(cfg)
        # If abbreviations provided, merge dicts
        if "abbreviations" in cfg:
            merged_abbr = DEFAULT_CONFIG["abbreviations"].copy()
            merged_abbr.update(cfg["abbreviations"])
            merged["abbreviations"] = merged_abbr
        return merged
    else:
        return DEFAULT_CONFIG.copy()

def smart_sentence_split(text: str, cfg: Dict) -> List[str]:
    """
    Split text into sentences. Prefer nltk if available, otherwise fall back to regex.
    Then further split long sentences by commas / semicolons / 'and' boundaries.
    """
    # Basic sentence tokenizer
    if nltk:
        sents = nltk.tokenize.sent_tokenize(text)
    else:
        # fallback: naive regex split by . ! ?
        sents = re.split(r'(?<=[.!?])\s+', text.strip())

    # further split overly long sentences
    out = []
    for s in sents:
        s = s.strip()
        if len(s) <= cfg["max_sentence_length"]:
            out.append(s)
            continue

        # attempt comma splits at sensible positions
        parts = re.split(r',\s+', s)
        if any(len(p) < cfg["split_on_commas_after"] for p in parts) and len(parts) > 1:
            for p in parts:
                p = p.strip()
                if p:
                    out.append(p)
            continue

        # attempt split at semicolons
        parts2 = re.split(r';\s+', s)
        if len(parts2) > 1:
            out.extend([p.strip() for p in parts2 if p.strip()])
            continue

        # final fallback: break by approximate word count
        words = s.split()
        chunk_size = max(12, int(cfg["max_sentence_length"] / 8))  # heuristic chunk words
        for i in range(0, len(words), chunk_size):
            out.append(" ".join(words[i:i + chunk_size]))
    return out

def expand_abbreviations(text: str, abbr_map: Dict[str, str]) -> str:
    # Replace whole-word abbreviations (case-insensitive)
    def repl(match):
        key = match.group(0)
        lower = key.lower()
        if lower in abbr_map:
            # preserve capitalization of first letter if needed
            replacement = abbr_map[lower]
            if key[0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            return replacement
        return key

    # build pattern to find all keys (escape special chars)
    keys = sorted(abbr_map.keys(), key=len, reverse=True)
    pattern = r'\b(' + '|'.join(re.escape(k) for k in keys) + r')\b'
    return re.sub(pattern, repl, text, flags=re.IGNORECASE)

def remove_markdown_symbols(text: str) -> str:
    # Remove literal markdown characters but keep the content/meaning
    # e.g., remove leading '#', remove '*' used for emphasis, convert '### Title' -> 'Title'
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        # remove heading markers at start
        new = re.sub(r'^\s{0,3}(#{1,6})\s*', '', line)
        # remove list markers at start but keep content
        new = re.sub(r'^\s*[-\*\•]\s+', '', new)
        # remove inline markdown emphasis markers but keep text
        new = new.replace('**', '').replace('*', '').replace('__', '').replace('_', '')
        new = new.strip()
        cleaned_lines.append(new)
    return "\n".join(cleaned_lines)

def detect_and_convert_lists(lines: List[str], cfg: Dict) -> List[str]:
    """
    Detect contiguous blocks of list lines and convert them into spoken sentences.
    Example:
      - apples
      - bananas
      - cherries
    -> "First, apples, then bananas, then cherries."
    """
    out_lines = []
    i = 0
    n = len(lines)
    indicators = cfg.get("list_indicators", [])
    while i < n:
        line = lines[i].strip()
        if not line:
            out_lines.append("")
            i += 1
            continue

        # simple detection: line starts with list marker
        if any(re.match(r'^\s*' + re.escape(ind) + r'\s+', line) for ind in indicators):
            # gather block
            items = []
            while i < n and lines[i].strip() and any(re.match(r'^\s*' + re.escape(ind) + r'\s+', lines[i].strip()) for ind in indicators):
                # strip marker
                txt = re.sub(r'^\s*(' + '|'.join(re.escape(ind) for ind in indicators) + r')\s*', '', lines[i].strip())
                items.append(txt)
                i += 1
            if items:
                # build spoken list
                spoken = cfg.get("list_to_spoken_prefix", "First, ") + items[0]
                connector = cfg.get("list_item_connector", ", then ")
                for it in items[1:]:
                    spoken += connector + it
                spoken += "."
                out_lines.append(spoken)
            continue
        else:
            out_lines.append(line)
            i += 1
    return out_lines

def insert_pauses_and_linebreaks(sentences: List[str], cfg: Dict) -> List[str]:
    """
    Add pauses (cfg['pause_token']) at sentence boundaries or after commas when appropriate.
    Also wrap sentences into lines to aid spoken rhythm.
    """
    pause = cfg.get("pause_token", "...")
    out = []
    for s in sentences:
        s = s.strip()
        if not s:
            out.append("")
            continue
        # Add pause after commas only if sentence length is relatively long
        if len(s) > cfg.get("split_on_commas_after", 60):
            s = re.sub(r',\s*', ', ' + pause + ' ', s)
        # Add a pause at the end for a natural spoken break
        if not s.endswith(('.', '!', '?', pause)):
            s = s.rstrip('.') + '.'  # ensure period
        s = s + ' ' + pause
        out.append(s.strip())
    return out

# ---------- Main Enricher class ----------
class TextEnricher:
    def __init__(self, config_path: str = None):
        self.cfg = load_config(config_path)

    def enrich_text(self, text: str) -> str:
        cfg = self.cfg

        # 1) Remove Markdown control characters while keeping content
        text = remove_markdown_symbols(text)

        # 2) Expand abbreviations
        text = expand_abbreviations(text, cfg.get("abbreviations", {}))

        # 3) Normalize whitespace
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)  # limit excessive blank lines

        # 4) Detect and convert lists into spoken style
        lines = text.splitlines()
        lines = detect_and_convert_lists(lines, cfg)
        text = "\n".join(lines)

        # 5) Break into paragraphs and sentences, then smart split long sentences
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        spoken_paragraphs = []
        for p in paragraphs:
            # avoid over-splitting if paragraph is a short phrase
            sentences = smart_sentence_split(p, cfg)
            # make sentences more conversational: strip and capitalize appropriately
            sentences = [s.strip() for s in sentences if s.strip()]
            # insert pauses and line-breaks
            sentences = insert_pauses_and_linebreaks(sentences, cfg)
            # join paragraph sentences with a blank-line for breathing room
            spoken_paragraphs.append("\n".join(sentences))

        # 6) Prepend greeting and a short auto-summary
        first_line_summary = ""
        # attempt a quick summary by taking the first meaningful sentence (limited words)
        if spoken_paragraphs:
            first_para = re.sub(r'\s+', ' ', re.sub(r'\.\.\.|\.{2,}', '.', spoken_paragraphs[0]))
            candidate = first_para.split('.')[0].strip()
            words = candidate.split()
            if len(words) >= cfg.get("min_words_for_summary", 3):
                first_line_summary = candidate[:150]  # ensure not too long

        summary_text = cfg.get("auto_summary_template", "").format(first_line_summary=first_line_summary) if first_line_summary else ""
        greeting = cfg.get("greeting", "")

        # Combine all parts
        final_parts = []
        if greeting:
            final_parts.append(greeting)
        if summary_text:
            final_parts.append(summary_text)
        final_parts.extend(spoken_paragraphs)

        final_text = "\n\n".join(final_parts)
        # final clean: avoid multiple pause tokens stacking
        final_text = re.sub(r'(\.\.\.)\s*(\.\.\.)+', r'\1', final_text)
        return final_text.strip()

    def enrich_file(self, input_txt_path: str) -> str:
        path = Path(input_txt_path)
        if not path.exists():
            raise FileNotFoundError(f"{input_txt_path} not found.")
        raw = path.read_text(encoding="utf-8")
        return self.enrich_text(raw)

    def save_text(self, text: str, output_path: str):
        Path(output_path).write_text(text, encoding="utf-8")
        print(f"Enriched text saved to {output_path}")

    # convenience: run pipeline: read -> enrich -> save
    def enrich_and_save(self, input_txt_path: str, output_txt_path: str):
        enriched = self.enrich_file(input_txt_path)
        self.save_text(enriched, output_txt_path)
        return enriched

# If you want direct test run
if __name__ == "__main__":
    enricher = TextEnricher()
    example_in = "sample_extracted.txt"
    if Path(example_in).exists():
        print("Enriching sample_extracted.txt ...")
        out = enricher.enrich_and_save(example_in, "sample_extracted_enriched.txt")
        print("Done.")
    else:
        print("No sample_extracted.txt found. Import TextEnricher in your script and call it programmatically.")
