import os
import io
import zipfile
from typing import List, Tuple

import streamlit as st

from backend.text_extraction import (
	extract_text_from_pdf,
	extract_text_from_docx,
	extract_text_from_txt,
	chunk_text,
)
from backend.llm import enrich_text_chunks
from backend.tts import synthesize_audio_chunks, TTSError


st.set_page_config(page_title="AI AudioBook Generator", page_icon="🎧", layout="wide")

st.title("🎧 AI AudioBook Generator")

st.markdown(
	"Convert your documents (PDF, DOCX, TXT) into engaging audiobooks. Upload files, let the app enhance narration using an LLM (optional), and generate downloadable audio."
)

with st.sidebar:
	st.header("Settings")
	use_llm = st.toggle("Use LLM enrichment (set API keys in env)", value=False)
	rate = st.slider("Speech rate (wpm)", min_value=120, max_value=240, value=180, step=5)
	max_chars = st.number_input("Chunk size (chars)", min_value=500, max_value=8000, value=3000, step=100)

uploaded_files = st.file_uploader("Upload one or more documents", type=["pdf", "docx", "txt"], accept_multiple_files=True)

generate = st.button("Generate Audiobook")


def _extract_text(file) -> Tuple[str, str]:
	name = file.name.lower()
	bytes_data = file.read()
	if name.endswith(".pdf"):
		text, engine_src = extract_text_from_pdf(bytes_data)
		return text, f"pdf ({engine_src})"
	if name.endswith(".docx"):
		return extract_text_from_docx(bytes_data), "docx"
	if name.endswith(".txt"):
		return extract_text_from_txt(bytes_data), "txt"
	return "", "unknown"


if generate and uploaded_files:
	all_outputs: List[Tuple[str, bytes]] = []
	progress = st.progress(0, text="Processing files...")
	for idx, uf in enumerate(uploaded_files, start=1):
		st.write(f"Processing: `{uf.name}`")
		text, src = _extract_text(uf)
		if not text.strip():
			st.warning(f"No text found in `{uf.name}` (source: {src}). Skipping.")
			progress.progress(int(idx / len(uploaded_files) * 100))
			continue

		chunks = chunk_text(text, max_chars=max_chars)
		if not chunks:
			st.warning(f"No content after chunking for `{uf.name}`. Skipping.")
			progress.progress(int(idx / len(uploaded_files) * 100))
			continue

		if use_llm:
			st.write("Enriching text with LLM...")
			enriched = enrich_text_chunks(chunks)
		else:
			enriched = chunks

		st.write("Synthesizing speech...")
		try:
			out_path, used_format = synthesize_audio_chunks(enriched, rate=rate)
			with open(out_path, "rb") as f:
				data = f.read()
			filename = os.path.splitext(os.path.basename(uf.name))[0] + f".{used_format}"
			all_outputs.append((filename, data))
			st.success(f"Done: {filename}")
			mime = "audio/wav" if used_format == "wav" else "audio/mpeg"
			st.audio(io.BytesIO(data), format=mime)
		except TTSError as e:
			st.error(f"❌ TTS Error for `{uf.name}`: {str(e)}")
		except Exception as e:
			st.error(f"❌ Unexpected error processing `{uf.name}`: {str(e)}")
		progress.progress(int(idx / len(uploaded_files) * 100))

	if len(all_outputs) == 1:
		fname, blob = all_outputs[0]
		mime = "audio/wav" if fname.lower().endswith(".wav") else "audio/mpeg"
		st.download_button("Download Audio", data=blob, file_name=fname, mime=mime)
	else:
		zip_buffer = io.BytesIO()
		with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
			for fname, blob in all_outputs:
				zf.writestr(fname, blob)
		zip_buffer.seek(0)
		st.download_button("Download All as ZIP", data=zip_buffer, file_name="audiobooks.zip", mime="application/zip")

