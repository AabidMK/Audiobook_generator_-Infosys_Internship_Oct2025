import os
import wave
import contextlib
from pathlib import Path
from typing import Optional

def process_file(
    tts_model,
    txt_path: Path,
    out_dir: Path,
    chunk_size_chars: int = 2000,
    silence_duration: float = 0.4,
    export_mp3: bool = False,
) -> Path:
    """
    Generate a spoken audiobook-style narration from text.
    
    Args:
        tts_model: Instance of TTS (from TTS.api import TTS or similar)
        txt_path (Path): Path to text file to read
        out_dir (Path): Directory to store output audio
        chunk_size_chars (int): Approx. text length per TTS call
        silence_duration (float): Seconds of silence between chunks
        export_mp3 (bool): Whether to convert final output to MP3
    
    Returns:
        Path to the final WAV (or MP3) file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        text = txt_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        raise RuntimeError(f"❌ Failed to read input text: {e}")

    # --- Split text into safe TTS chunks ---
    words = text.split()
    chunks, cur, cur_len = [], [], 0
    for w in words:
        if cur_len + len(w) + 1 > chunk_size_chars:
            chunks.append(" ".join(cur))
            cur, cur_len = [], 0
        cur.append(w)
        cur_len += len(w) + 1
    if cur:
        chunks.append(" ".join(cur))

    print(f"🗣️ Generating audio in {len(chunks)} parts...")

    temp_files = []
    for i, chunk in enumerate(chunks):
        tmp = out_dir / f"{txt_path.stem}_part_{i}.wav"
        try:
            tts_model.tts_to_file(text=chunk, file_path=str(tmp))
            temp_files.append(tmp)
            print(f"✅ Part {i+1}/{len(chunks)} generated.")
        except Exception as e:
            print(f"⚠️ Failed to generate TTS for chunk {i+1}: {e}")

    if not temp_files:
        raise RuntimeError("❌ No audio generated — all chunks failed.")

    # --- Combine WAVs ---
    final_wav = out_dir / f"{txt_path.stem}.wav"
    print("🔊 Combining parts...")

    with wave.open(str(final_wav), "wb") as fout:
        with wave.open(str(temp_files[0]), "rb") as first:
            fout.setparams(first.getparams())

        for i, tf in enumerate(temp_files):
            with contextlib.closing(wave.open(str(tf), "rb")) as fr:
                frames = fr.readframes(fr.getnframes())
                fout.writeframes(frames)
                # Add silence between chunks (to simulate natural pause)
                silence_frames = b"\x00\x00" * int(fout.getframerate() * silence_duration)
                fout.writeframes(silence_frames)

    # --- Cleanup intermediate files ---
    for tf in temp_files:
        try:
            tf.unlink()
        except Exception:
            pass

    # --- Optional MP3 conversion ---
    if export_mp3:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_wav(final_wav)
            final_mp3 = final_wav.with_suffix(".mp3")
            audio.export(final_mp3, format="mp3", bitrate="192k")
            print(f"🎧 MP3 exported: {final_mp3}")
            final_wav.unlink(missing_ok=True)
            return final_mp3
        except Exception as e:
            print(f"⚠️ MP3 conversion failed: {e}")

    print(f"✅ Final narration saved at: {final_wav}")
    return final_wav
