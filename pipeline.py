"""
Audiobook generation pipeline.
Combines text extraction, enrichment, and text-to-speech conversion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from text_extractor import TextExtractor
from text_enricher import TextEnricher
from tts_converter import TTSConverter


class AudiobookPipeline:
    """High-level pipeline to convert source files into enriched text and audio."""

    def __init__(
        self,
        extracted_folder: str = "extracted_texts",
        enriched_folder: str = "enriched_texts",
        audio_folder: str = "audio_output",
    ) -> None:
        self.extracted_folder = Path(extracted_folder)
        self.enriched_folder = Path(enriched_folder)
        self.audio_folder = Path(audio_folder)

        self.extractor = TextExtractor(output_folder=self.extracted_folder)

    def _should_skip_extraction(self, source_path: Path) -> bool:
        """Return True if the provided path is already an extracted text file."""
        return (
            source_path.suffix.lower() == ".txt"
            and source_path.parent.resolve() == self.extracted_folder.resolve()
        )

    def _should_skip_enrichment(self, extracted_path: Path) -> bool:
        """Return True if the provided path is already an enriched text file."""
        return (
            extracted_path.suffix.lower() == ".txt"
            and extracted_path.parent.resolve() == self.enriched_folder.resolve()
        )

    def process(
        self,
        source_path: str,
        *,
        api_key: Optional[str] = None,
        convert_to_audio: bool = True,
        voice: Optional[str] = None,
        enhancement_prompt: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        verbose: bool = True,
    ) -> Dict[str, Optional[Path]]:
        """
        Run the full audiobook pipeline.

        Args:
            source_path: Path to the source file (PDF, DOCX, TXT, image, or extracted text).
            api_key: Google Gemini API key. If None, value from GEMINI_API_KEY env var is used.
            convert_to_audio: Whether to generate audio output.
            voice: Optional Edge-TTS voice name.
            enhancement_prompt: Optional custom enrichment prompt.
            rate: Speech rate for TTS (Edge-TTS format).
            pitch: Speech pitch for TTS (Edge-TTS format).
            verbose: If True, print progress to stdout.

        Returns:
            Dictionary with keys:
                - extracted_text_path
                - enriched_text_path
                - audio_path (None if convert_to_audio is False)
        """
        source = Path(source_path).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        results: Dict[str, Optional[Path]] = {
            "extracted_text_path": None,
            "enriched_text_path": None,
            "audio_path": None,
        }

        # Step 1: Extraction (skip if already in extracted_texts)
        if self._should_skip_extraction(source):
            if verbose:
                print("=" * 50)
                print("STEP 1: Text Extraction (skipped — already extracted)")
                print("=" * 50)
                print(f"Using existing extracted text: {source}")
            extracted_text_path = source
            extracted_text = extracted_text_path.read_text(encoding="utf-8")
        else:
            if verbose:
                print("=" * 50)
                print("STEP 1: Text Extraction")
                print("=" * 50)
                print(f"Extracting text from: {source}")
            extracted_text, extracted_text_path = self.extractor.process_file(source)
            if verbose:
                print(f"\nExtracted {len(extracted_text)} characters.")
        results["extracted_text_path"] = extracted_text_path

        # Step 2: Enrichment (skip if already enriched)
        if self._should_skip_enrichment(extracted_text_path):
            if verbose:
                print("\n" + "=" * 50)
                print("STEP 2: Text Enrichment (skipped — already enriched)")
                print("=" * 50)
                print(f"Using existing enriched text: {extracted_text_path}")
            enriched_text_path = extracted_text_path
            enriched_text = enriched_text_path.read_text(encoding="utf-8")
        else:
            if verbose:
                print("\n" + "=" * 50)
                print("STEP 2: Text Enrichment")
                print("=" * 50)
                print(f"Enriching text using Google Gemini API (source: {extracted_text_path})")
            enricher = TextEnricher(api_key=api_key, output_folder=self.enriched_folder)
            enriched_text, enriched_text_path = enricher.process_file(
                extracted_text_path, enhancement_prompt=enhancement_prompt
            )
            if verbose:
                print(f"\nEnriched text contains {len(enriched_text)} characters.")
        results["enriched_text_path"] = enriched_text_path

        # Step 3: Text-to-Speech
        if convert_to_audio:
            if verbose:
                print("\n" + "=" * 50)
                print("STEP 3: Text-to-Speech Conversion")
                print("=" * 50)
                print(f"Converting enriched text to speech: {enriched_text_path}")
            converter = TTSConverter(output_folder=self.audio_folder)
            audio_path = converter.convert_file(
                enriched_text_path,
                voice=voice,
                rate=rate,
                pitch=pitch,
            )
            if verbose:
                file_size_mb = audio_path.stat().st_size / (1024 * 1024)
                print(f"\n✅ Audio file saved: {audio_path.name} ({file_size_mb:.2f} MB)")
            results["audio_path"] = audio_path
        elif verbose:
            print("\n" + "=" * 50)
            print("STEP 3: Text-to-Speech Conversion (skipped)")
            print("=" * 50)

        if verbose:
            print("\n" + "=" * 50)
            print("PIPELINE COMPLETE")
            print("=" * 50)
            print(f"Original file: {source}")
            print(f"Extracted text: {results['extracted_text_path']}")
            print(f"Enriched text: {results['enriched_text_path']}")
            if results["audio_path"]:
                print(f"Audio file:   {results['audio_path']}")

        return results


def run_pipeline(
    source_path: str,
    *,
    api_key: Optional[str] = None,
    convert_to_audio: bool = True,
    voice: Optional[str] = None,
    enhancement_prompt: Optional[str] = None,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    verbose: bool = True,
) -> Dict[str, Optional[Path]]:
    """
    Convenience function to execute the pipeline without instantiating the class manually.
    """
    pipeline = AudiobookPipeline()
    return pipeline.process(
        source_path,
        api_key=api_key,
        convert_to_audio=convert_to_audio,
        voice=voice,
        enhancement_prompt=enhancement_prompt,
        rate=rate,
        pitch=pitch,
        verbose=verbose,
    )

