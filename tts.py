
from __future__ import annotations

import asyncio
import os
os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD'] = '0'
        
import logging
from pathlib import Path
from typing import Literal, Optional

from utils import ensure_dirs, timestamped_filename, OUTPUT_AUDIO_DIR

logger = logging.getLogger(__name__)

# Core engines (lightweight)
try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False
    pyttsx3 = None

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False
    gTTS = None

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False
    edge_tts = None

# Advanced engines (optional, heavy)
try:
    from TTS.api import TTS as CoquiTTS
    HAS_COQUI = True
except ImportError:
    HAS_COQUI = False
    CoquiTTS = None

try:
    from bark import SAMPLE_RATE, generate_audio, preload_models
    HAS_BARK = True
except ImportError:
    HAS_BARK = False
    SAMPLE_RATE = None
    generate_audio = None
    preload_models = None
    


EngineName = Literal["pyttsx3", "gtts", "edge-tts", "coqui", "bark"]


def validate_text(text: str) -> str:
    """Validate and clean text for TTS."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Cannot synthesize empty text")
    return text


def tts_synthesize(
    text: str,
    engine: EngineName = "gtts",
    language: str = "en",
    rate: Optional[int] = None,
    voice_id: Optional[str] = None,
    basename: str = "speech",
) -> Path:
    """Synthesize speech and return saved audio path.

    Engines:
    - pyttsx3: offline, fast, lower quality WAV
    - gtts: online, Google TTS, decent quality MP3
    - edge-tts: online, Microsoft Edge TTS, HIGH QUALITY MP3 ⭐
    - coqui: offline, neural TTS, high quality WAV (large models)
    - bark: offline, ULTRA HIGH QUALITY WAV with emotions (SLOW, large models 2-10GB) 🎭
    
    Recommended: gtts (simple, reliable) or edge-tts (best quality) or bark (best audio quality)
    """
    ensure_dirs()
    text = validate_text(text)

    if engine == "pyttsx3":
        if not HAS_PYTTSX3:
            raise RuntimeError("pyttsx3 not installed. Install: pip install pyttsx3")
        eng = pyttsx3.init()
        if rate is not None:
            eng.setProperty("rate", rate)
        if voice_id is not None:
            eng.setProperty("voice", voice_id)
        out_path = OUTPUT_AUDIO_DIR / (timestamped_filename(basename, "pyttsx3") + ".wav")
        eng.save_to_file(text, str(out_path))
        eng.runAndWait()
        logger.info(f"Synthesized with pyttsx3: {out_path}")
        return out_path

    elif engine == "gtts":
        if not HAS_GTTS:
            raise RuntimeError("gTTS not installed. Install: pip install gtts")
        tts = gTTS(text=text, lang=language, slow=False)
        out_path = OUTPUT_AUDIO_DIR / (timestamped_filename(basename, "gtts") + ".mp3")
        tts.save(str(out_path))
        logger.info(f"Synthesized with gTTS: {out_path}")
        return out_path

    elif engine == "edge-tts":
        if not HAS_EDGE_TTS:
            raise RuntimeError("edge-tts not installed. Install: pip install edge-tts")
        
        # Default to high-quality Jenny voice
        voice = voice_id or "en-US-JennyNeural"
        out_path = OUTPUT_AUDIO_DIR / (timestamped_filename(basename, "edge-tts") + ".mp3")
        
        # Edge-TTS requires async
        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(out_path))
        
        asyncio.run(_generate())
        logger.info(f"Synthesized with Edge-TTS ({voice}): {out_path}")
        return out_path

    elif engine == "coqui":
        if not HAS_COQUI:
            raise RuntimeError(
                "Coqui TTS not installed. Install: pip install TTS\n"
                "Note: Models are large (~100MB+) and download on first use."
            )
        
        model_name = "tts_models/en/ljspeech/tacotron2-DDC"
        tts = CoquiTTS(model_name)
        out_path = OUTPUT_AUDIO_DIR / (timestamped_filename(basename, "coqui") + ".wav")
        tts.tts_to_file(text=text, file_path=str(out_path))
        logger.info(f"Synthesized with Coqui: {out_path}")
        return out_path

    elif engine == "bark":
        if not HAS_BARK:
            raise RuntimeError(
                "Bark TTS not installed. Install: pip install git+https://github.com/suno-ai/bark.git\n"
                "Note: Models are VERY large (2-10GB) and download on first use. Generation is slow."
            )
        
        import scipy.io.wavfile as wavfile
        import torch
        import numpy as np
        import os
        
        # Force disable weights_only loading for Bark compatibility
        os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD'] = '0'
        
        # Add safe globals for Bark model loading (PyTorch 2.6+ compatibility)
        torch.serialization.add_safe_globals([np.core.multiarray.scalar, np.dtype, np.dtypes.Float64DType])
        
        logger.info("Loading Bark models (first time will download 2-10GB)...")
        preload_models()
        
        logger.info("Generating audio with Bark (this may take several seconds)...")
        audio_array = generate_audio(text)
        
        out_path = OUTPUT_AUDIO_DIR / (timestamped_filename(basename, "bark") + ".wav")
        wavfile.write(str(out_path), SAMPLE_RATE, audio_array)
        logger.info(f"Synthesized with Bark: {out_path}")
        return out_path

    else:
        raise ValueError(f"Unknown engine: {engine}")


def list_available_engines() -> dict[str, dict]:
    """List all available TTS engines with their status."""
    return {
        "pyttsx3": {
            "available": HAS_PYTTSX3,
            "quality": "Low-Medium",
            "speed": "Fast",
            "type": "Offline",
            "notes": "System TTS, robotic sound",
        },
        "gtts": {
            "available": HAS_GTTS,
            "quality": "Medium",
            "speed": "Medium",
            "type": "Online",
            "notes": "Google TTS, simple and reliable ⭐",
        },
        "edge-tts": {
            "available": HAS_EDGE_TTS,
            "quality": "High",
            "speed": "Fast",
            "type": "Online",
            "notes": "Microsoft Edge TTS, natural voices (BEST)",
        },
        "coqui": {
            "available": HAS_COQUI,
            "quality": "High",
            "speed": "Medium",
            "type": "Offline",
            "notes": "Neural TTS, large models required",
        },
        "bark": {
            "available": HAS_BARK,
            "quality": "ULTRA High (with emotions)",
            "speed": "Very Slow",
            "type": "Offline",
            "notes": "Suno AI Bark, best quality, includes emotions & effects (2-10GB models) 🎭⭐",
        },
    }


def get_recommended_engine() -> EngineName:
    """Get the best available TTS engine."""
    if HAS_GTTS:
        return "gtts"  # Simple, reliable, good quality
    elif HAS_EDGE_TTS:
        return "edge-tts"  # Best quality
    elif HAS_PYTTSX3:
        return "pyttsx3"  # Offline fallback
    else:
        raise RuntimeError("No TTS engine available. Install: pip install gtts")
