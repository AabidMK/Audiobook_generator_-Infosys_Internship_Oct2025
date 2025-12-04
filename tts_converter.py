"""
Text-to-Speech Converter Module
Converts text to natural-sounding speech using Edge-TTS
"""

import os
import asyncio
from pathlib import Path
import edge_tts
from pydub import AudioSegment
import tempfile


class TTSConverter:
    """Convert text to speech using Edge-TTS"""
    
    def __init__(self, output_folder="audio_output"):
        """
        Initialize the TTS converter
        
        Args:
            output_folder: Folder to save audio files
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
    
    async def get_voices(self):
        """
        Get list of available voices
        
        Returns:
            List of available voice names
        """
        voices = await edge_tts.list_voices()
        return voices
    
    def find_best_voice(self, voices=None, language="en", gender="Female"):
        """
        Find the best voice for the specified language and gender
        
        Args:
            voices: List of voices (if None, will fetch)
            language: Language code (default: "en" for English)
            gender: "Female" or "Male"
            
        Returns:
            Voice name string
        """
        if voices is None:
            voices = asyncio.run(self.get_voices())
        
        # Prefer US English for clarity, then other English variants
        preferred_locales = ["en-US", "en-GB", "en-AU", "en-CA"]
        
        for locale in preferred_locales:
            # Filter by preferred locale and gender
            filtered = [
                v for v in voices
                if locale.lower() in v.get("Locale", "").lower()
                and v.get("Gender", "").lower() == gender.lower()
            ]
            
            if filtered:
                # Prefer neural voices for better quality
                neural_voices = [v for v in filtered if "neural" in v.get("VoiceType", "").lower()]
                if neural_voices:
                    # Prefer popular voices like Aria, Jenny, or similar
                    preferred_names = ["Aria", "Jenny", "Michelle", "Sara"]
                    for name in preferred_names:
                        for voice in neural_voices:
                            if name in voice.get("Name", ""):
                                return voice["Name"]
                    return neural_voices[0]["Name"]
                return filtered[0]["Name"]
        
        # Fallback to any English neural voice
        english_neural = [
            v for v in voices
            if "en" in v.get("Locale", "").lower()
            and "neural" in v.get("VoiceType", "").lower()
            and v.get("Gender", "").lower() == gender.lower()
        ]
        if english_neural:
            return english_neural[0]["Name"]
        
        # Ultimate fallback
        return "en-US-AriaNeural"  # High-quality default
    
    async def text_to_speech_async(self, text, output_path, voice=None, rate="+0%", pitch="+0Hz"):
        """
        Convert text to speech asynchronously
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
            voice: Voice name (if None, will auto-select best voice)
            rate: Speech rate (e.g., "+0%", "-10%", "+10%")
            pitch: Speech pitch (e.g., "+0Hz", "+5Hz", "-5Hz")
        """
        if voice is None:
            voices = await self.get_voices()
            voice = self.find_best_voice(voices, language="en", gender="Female")
        
        print(f"Using voice: {voice}")
        print(f"Converting text to speech... (This may take a moment for long texts)")
        
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(str(output_path))
    
    def text_to_speech(self, text, output_path, voice=None, rate="+0%", pitch="+0Hz"):
        """
        Convert text to speech (synchronous wrapper)
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
            voice: Voice name (if None, will auto-select best voice)
            rate: Speech rate (e.g., "+0%", "-10%", "+10%")
            pitch: Speech pitch (e.g., "+0Hz", "+5Hz", "-5Hz")
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        asyncio.run(self.text_to_speech_async(text, output_path, voice, rate, pitch))
    
    def convert_file(self, text_file_path, output_filename=None, voice=None, rate="+0%", pitch="+0Hz"):
        """
        Convert text file to speech (handles both short and long texts)
        
        Args:
            text_file_path: Path to text file
            output_filename: Optional output filename (if None, auto-generated)
            voice: Voice name (if None, will auto-select)
            
        Returns:
            Path to saved audio file (single file, even for long texts)
        """
        text_file_path = Path(text_file_path)
        if not text_file_path.exists():
            raise FileNotFoundError(f"Text file not found: {text_file_path}")
        
        # Read text from file
        with open(text_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Generate output filename
        if output_filename is None:
            output_filename = text_file_path.stem.replace("_enriched", "").replace("_extracted", "") + "_audio.mp3"
        else:
            if not output_filename.endswith('.mp3'):
                output_filename += ".mp3"
        
        # Check if text is long and needs chunking
        if len(text) > 4000:
            # Use convert_long_text for chunking and combining
            return self.convert_long_text(text_file_path, output_filename, voice, rate=rate, pitch=pitch)
        else:
            # Direct conversion for short texts
            output_path = self.output_folder / output_filename
            print(f"Converting '{text_file_path.name}' to speech...")
            self.text_to_speech(text, output_path, voice, rate=rate, pitch=pitch)
            return output_path
    
    def split_text_for_tts(self, text, max_length=5000):
        """
        Split long text into chunks for TTS (to avoid limits)
        
        Args:
            text: Text to split
            max_length: Maximum length per chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _convert_chunks_async(self, chunks, temp_files, voice, rate="+0%", pitch="+0Hz", concurrency: int = 3):
        """Convert multiple text chunks to audio concurrently and save to temp_files."""
        sem = asyncio.Semaphore(concurrency)

        async def worker(text, path):
            async with sem:
                await self.text_to_speech_async(text, path, voice=voice, rate=rate, pitch=pitch)

        tasks = [worker(chunk, path) for chunk, path in zip(chunks, temp_files)]
        await asyncio.gather(*tasks)

    def convert_long_text(self, text_file_path, output_filename=None, voice=None, rate="+0%", pitch="+0Hz"):
        """Convert long text file to speech by splitting into chunks, converting
        them concurrently, and combining into a single file."""
        text_file_path = Path(text_file_path)
        if not text_file_path.exists():
            raise FileNotFoundError(f"Text file not found: {text_file_path}")
        
        # Read text
        with open(text_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Split into chunks
        chunks = self.split_text_for_tts(text)
        print(f"Text split into {len(chunks)} chunks for processing...")

        # Resolve voice once for all chunks to avoid repeated lookups
        if voice is None:
            voices = asyncio.run(self.get_voices())
            voice = self.find_best_voice(voices, language="en", gender="Female")
        print(f"Using voice: {voice}")
        
        # Generate base output filename
        if output_filename is None:
            base_name = text_file_path.stem.replace("_enriched", "").replace("_extracted", "")
            output_filename = base_name + "_audio.mp3"
        else:
            if not output_filename.endswith('.mp3'):
                output_filename += ".mp3"
        
        final_output_path = self.output_folder / output_filename
        
        # Create temporary directory for chunk files
        temp_dir = Path(tempfile.mkdtemp())
        temp_files = []
        
        try:
            # Prepare temp file paths and convert chunks concurrently
            print("Converting chunks to audio (parallel)...")
            for i in range(len(chunks)):
                temp_file = temp_dir / f"chunk_{i+1:03d}.mp3"
                temp_files.append(temp_file)

            asyncio.run(self._convert_chunks_async(chunks, temp_files, voice, rate=rate, pitch=pitch))
            
            # Combine all audio files into one
            print(f"\nCombining {len(chunks)} audio chunks into single file...")
            combined_audio = AudioSegment.empty()
            
            for i, temp_file in enumerate(temp_files):
                print(f"Adding chunk {i+1}/{len(chunks)}...")
                audio_segment = AudioSegment.from_mp3(str(temp_file))
                combined_audio += audio_segment
                # Add a small pause between chunks for natural flow
                combined_audio += AudioSegment.silent(duration=500)  # 500ms pause
            
            # Export the combined audio
            print(f"Exporting final audio file...")
            combined_audio.export(str(final_output_path), format="mp3")
            
            file_size_mb = final_output_path.stat().st_size / (1024 * 1024)
            print(f"\n✅ Single audio file created: {final_output_path.name} ({file_size_mb:.2f} MB)")
            
            return final_output_path
            
        finally:
            # Clean up temporary files
            import shutil
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

