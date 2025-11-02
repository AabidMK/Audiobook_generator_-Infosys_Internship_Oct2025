"""
Generate complete audiobook using Bark TTS by processing text in chunks
"""
import os
os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD'] = '0'

import logging
from pathlib import Path
import scipy.io.wavfile as wavfile
import numpy as np
import torch

# Add safe globals for PyTorch compatibility BEFORE importing Bark
torch.serialization.add_safe_globals([
    np.core.multiarray.scalar, 
    np.dtype,
    np.dtypes.Float64DType
])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Bark
from bark import SAMPLE_RATE, generate_audio, preload_models

def split_text_into_chunks(text, max_words=100):
    """Split text into chunks by sentences, keeping under max_words"""
    # Split by periods to get sentences
    sentences = text.replace('\n', ' ').split('.')
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Add period back
        sentence = sentence + "."
        
        # Check if adding this sentence exceeds limit
        test_chunk = current_chunk + " " + sentence if current_chunk else sentence
        word_count = len(test_chunk.split())
        
        if word_count > max_words and current_chunk:
            # Save current chunk and start new one
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = test_chunk
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def main():
    # Read the extracted text
    text_file = Path("outputs/text/AI AudioBook Generator_extracted_20251031-183821_extracted.txt")
    
    if not text_file.exists():
        logger.error(f"Text file not found: {text_file}")
        return
    
    with open(text_file, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    logger.info(f"Read {len(full_text.split())} words from {text_file.name}")
    
    # Split into chunks
    chunks = split_text_into_chunks(full_text, max_words=100)
    logger.info(f"Split into {len(chunks)} chunks")
    
    # Preload Bark models once
    logger.info("Loading Bark models (this may take a while)...")
    preload_models()
    logger.info("Models loaded!")
    
    # Generate audio for each chunk
    all_audio = []
    
    for i, chunk in enumerate(chunks, 1):
        logger.info(f"Processing chunk {i}/{len(chunks)} ({len(chunk.split())} words)...")
        try:
            audio_array = generate_audio(chunk)
            all_audio.append(audio_array)
            logger.info(f"  ✓ Chunk {i} complete")
        except Exception as e:
            logger.error(f"  ✗ Error on chunk {i}: {e}")
            continue
    
    if not all_audio:
        logger.error("No audio generated!")
        return
    
    # Concatenate all audio chunks
    logger.info("Concatenating audio chunks...")
    final_audio = np.concatenate(all_audio)
    
    # Save to file
    output_dir = Path("outputs/audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "AI_AudioBook_Generator_FULL_bark.wav"
    wavfile.write(str(output_file), SAMPLE_RATE, final_audio)
    
    duration_seconds = len(final_audio) / SAMPLE_RATE
    duration_minutes = duration_seconds / 60
    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    
    logger.info("=" * 70)
    logger.info("COMPLETE AUDIOBOOK GENERATED!")
    logger.info("=" * 70)
    logger.info(f"Output file: {output_file}")
    logger.info(f"File size: {file_size_mb:.2f} MB")
    logger.info(f"Duration: {duration_minutes:.2f} minutes ({duration_seconds:.1f} seconds)")
    logger.info(f"Chunks processed: {len(all_audio)}/{len(chunks)}")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
