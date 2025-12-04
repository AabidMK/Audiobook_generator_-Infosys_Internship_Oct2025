import re
from pathlib import Path
from typing import List, Dict
import json

# Optional: use nltk for sentence splitting if available
try:
    import nltk
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)
except ImportError:
    nltk = None

DEFAULT_CONFIG = {
    "greeting": "Hello listeners, welcome...",
    "auto_summary_template": "In this audio, you will learn about: {first_line_summary}",
    "max_sentence_length": 140,
    "split_on_commas_after": 60,
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
        merged = DEFAULT_CONFIG.copy()
        merged.update(cfg)
        if "abbreviations" in cfg:
            merged_abbr = DEFAULT_CONFIG["abbreviations"].copy()
            merged_abbr.update(cfg["abbreviations"])
            merged["abbreviations"] = merged_abbr
        return merged
    else:
        return DEFAULT_CONFIG.copy()

def smart_sentence_split(text: str, cfg: Dict) -> List[str]:
    if nltk:
        sents = nltk.tokenize.sent_tokenize(text)
    else:
        sents = re.split(r'(?<=[.!?])\s+', text.strip())

    out = []
    for s in sents:
        s = s.strip()
        if len(s) <= cfg["max_sentence_length"]:
            out.append(s)
            continue
        parts = re.split(r',\s+', s)
        if any(len(p) < cfg["split_on_commas_after"] for p in parts) and len(parts) > 1:
            out.extend([p.strip() for p in parts if p.strip()])
            continue
        parts2 = re.split(r';\s+', s)
        if len(parts2) > 1:
            out.extend([p.strip() for p in parts2 if p.strip()])
            continue
        words = s.split()
        chunk_size = max(12, int(cfg["max_sentence_length"] / 8))
        for i in range(0, len(words), chunk_size):
            out.append(" ".join(words[i:i + chunk_size]))
    return out

def expand_abbreviations(text: str, abbr_map: Dict[str, str]) -> str:
    def repl(match):
        key = match.group(0)
        lower = key.lower()
        if lower in abbr_map:
            replacement = abbr_map[lower]
            if key[0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            return replacement
        return key
    keys = sorted(abbr_map.keys(), key=len, reverse=True)
    pattern = r'\b(' + '|'.join(re.escape(k) for k in keys) + r')\b'
    return re.sub(pattern, repl, text, flags=re.IGNORECASE)

def remove_markdown_symbols(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        new = re.sub(r'^\s{0,3}(#{1,6})\s*', '', line)
        new = re.sub(r'^\s*[-\*\•]\s+', '', new)
        new = new.replace('**', '').replace('*', '').replace('__', '').replace('_', '')
        cleaned_lines.append(new.strip())
    return "\n".join(cleaned_lines)

def detect_and_convert_lists(lines: List[str], cfg: Dict) -> List[str]:
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
        if any(re.match(r'^\s*' + re.escape(ind) + r'\s+', line) for ind in indicators):
            items = []
            while i < n and lines[i].strip() and any(re.match(r'^\s*' + re.escape(ind) + r'\s+', lines[i].strip()) for ind in indicators):
                txt = re.sub(r'^\s*(' + '|'.join(re.escape(ind) for ind in indicators) + r')\s*', '', lines[i].strip())
                items.append(txt)
                i += 1
            if items:
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
    pause = cfg.get("pause_token", "...")
    out = []
    for s in sentences:
        s = s.strip()
        if not s:
            out.append("")
            continue
        if len(s) > cfg.get("split_on_commas_after", 60):
            s = re.sub(r',\s*', ', ' + pause + ' ', s)
        if not s.endswith(('.', '!', '?', pause)):
            s = s.rstrip('.') + '.'
        s = s + ' ' + pause
        out.append(s.strip())
    return out

# ---------- Main Enricher class ----------
class TextEnricher:
    def __init__(self, config_path: str = None):
        self.cfg = load_config(config_path)

    def enrich_text(self, text: str, model: str = None) -> str:
        """
        Enrich the input text and return enriched text.
        model parameter included for compatibility with app.py
        """
        cfg = self.cfg
        text = remove_markdown_symbols(text)
        text = expand_abbreviations(text, cfg.get("abbreviations", {}))
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        lines = text.splitlines()
        lines = detect_and_convert_lists(lines, cfg)
        text = "\n".join(lines)

        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        spoken_paragraphs = []
        for p in paragraphs:
            sentences = smart_sentence_split(p, cfg)
            sentences = [s.strip() for s in sentences if s.strip()]
            sentences = insert_pauses_and_linebreaks(sentences, cfg)
            spoken_paragraphs.append("\n".join(sentences))

        first_line_summary = ""
        if spoken_paragraphs:
            first_para = re.sub(r'\s+', ' ', re.sub(r'\.\.\.|\.{2,}', '.', spoken_paragraphs[0]))
            candidate = first_para.split('.')[0].strip()
            words = candidate.split()
            if len(words) >= cfg.get("min_words_for_summary", 3):
                first_line_summary = candidate[:150]

        summary_text = cfg.get("auto_summary_template", "").format(first_line_summary=first_line_summary) if first_line_summary else ""
        greeting = cfg.get("greeting", "")
        final_parts = []
        if greeting:
            final_parts.append(greeting)
        if summary_text:
            final_parts.append(summary_text)
        final_parts.extend(spoken_paragraphs)
        final_text = "\n\n".join(final_parts)
        final_text = re.sub(r'(\.\.\.)\s*(\.\.\.)+', r'\1', final_text)
        return final_text.strip()

# Convenience function to match app.py usage
def enrich_text(text: str, model: str = "gpt-4o-mini") -> str:
    enricher = TextEnricher()
    return enricher.enrich_text(text, model=model)
