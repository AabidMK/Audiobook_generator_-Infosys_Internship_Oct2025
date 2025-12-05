import os
import tempfile
import asyncio
from typing import List, Tuple

import edge_tts  # type: ignore


class TTSError(Exception):
	pass


DEFAULT_EDGE_VOICE = "en-US-JennyNeural"
BASE_WPM = 180

try:
	from gtts import gTTS  # type: ignore
except Exception:
	gTTS = None  # type: ignore

try:
	from TTS.api import TTS as CoquiTTS  # type: ignore
except Exception:
	CoquiTTS = None  # type: ignore


def _rate_to_percentage(rate_wpm: int) -> str:
	try:
		delta = int(round((rate_wpm / BASE_WPM - 1.0) * 100))
	except Exception:
		delta = 0
	# Clamp to a reasonable range
	delta = max(-50, min(100, delta))
	return f"{delta:+d}%"


def synthesize_audio_chunks(
	chunks: List[str],
	rate: int = BASE_WPM,
	voice_name: str = "",
) -> Tuple[str, str]:
	"""
	Try Coqui TTS first (offline/locally cached). If unavailable or fails, use Edge-TTS.
	On Edge 403 and ALLOW_TEMP_FALLBACK=true, fallback to gTTS.
	Returns (output_path, used_format).
	"""
	text = "\n\n".join(chunks)

	# 1) Try Coqui TTS → WAV
	if CoquiTTS is not None:
		try:
			model_name = os.getenv("COQUI_MODEL", "tts_models/en/ljspeech/tacotron2-DDC")
			tts = CoquiTTS(model_name=model_name)
			fd_wav, wav_path = tempfile.mkstemp(suffix=".wav")
			os.close(fd_wav)
			tts.tts_to_file(text=text, file_path=wav_path)
			return wav_path, "wav"
		except Exception as e:
			# Proceed to Edge-TTS
			pass

	# 2) Edge-TTS → MP3
	voice = voice_name or DEFAULT_EDGE_VOICE
	rate_pct = _rate_to_percentage(rate)
	fd_mp3, mp3_path = tempfile.mkstemp(suffix=".mp3")
	os.close(fd_mp3)

	async def _run_edge():
		try:
			communicate = edge_tts.Communicate(text, voice=voice, rate=rate_pct)
			with open(mp3_path, "wb") as f:
				async for chunk in communicate.stream():
					if chunk["type"] == "audio":
						f.write(chunk["data"])
		except Exception as e:
			error_msg = str(e)
			if ("403" in error_msg or "WSServerHandshakeError" in error_msg) and gTTS is not None:
				# Temporary fallback to gTTS automatically if available
				_fallback_with_gtts(text, mp3_path)
				return
			if "403" in error_msg or "WSServerHandshakeError" in error_msg:
				raise TTSError(
					"Edge-TTS is blocked or unavailable (403), and gTTS fallback is unavailable or failed. Try again later."
				)
			if "429" in error_msg or "Too Many Requests" in error_msg:
				raise TTSError(
					"Edge-TTS rate limit exceeded (429). Please wait and retry or reduce text size."
				)
			raise TTSError(f"Edge-TTS error: {error_msg}")

	asyncio.run(_run_edge())
	return mp3_path, "mp3"


def _fallback_with_gtts(text: str, out_path: str) -> None:
	if gTTS is None:
		raise TTSError("gTTS fallback requested but gTTS is not installed.")
	tts = gTTS(text=text, lang=os.getenv("GTTS_LANG", "en"), tld=os.getenv("GTTS_TLD", "com"))
	with open(out_path, "wb") as f:
		tts.write_to_fp(f)

