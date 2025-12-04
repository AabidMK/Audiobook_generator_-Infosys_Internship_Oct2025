"""
Text Enrichment Module
Enriches extracted text using Google Gemini API
"""

import os
import google.generativeai as genai
from pathlib import Path


class TextEnricher:
    """Enrich text using Google Gemini API"""
    
    def __init__(self, api_key=None, output_folder="enriched_texts"):
        """
        Initialize the text enricher
        
        Args:
            api_key: Google Gemini API key (or set GEMINI_API_KEY env variable)
            output_folder: Folder to save enriched text files
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Google Gemini API key is required. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        genai.configure(api_key=self.api_key)
        
        # Try to use a modern model, fallback to available ones
        try:
            # Try gemini-2.5-flash first (faster and cheaper)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except:
            try:
                # Fallback to gemini-2.5-pro (more capable)
                self.model = genai.GenerativeModel('gemini-2.5-pro')
            except:
                # Last resort: use gemini-pro-latest
                self.model = genai.GenerativeModel('gemini-pro-latest')
        
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
    
    def _post_process_enriched_text(self, enriched_text: str) -> str:
        """Clean up enriched text before saving/using.

        Removes any leading staging instructions (like intro music/sound
        descriptions) and, when possible, starts from the first line that
        contains a welcome-style introduction.
        """
        if not enriched_text:
            return enriched_text

        lines = list(enriched_text.splitlines())

        # Prefer to start from the first line containing "welcome"
        start_idx = None
        for idx, line in enumerate(lines):
            lower = line.strip().lower()
            if not lower:
                continue
            if "welcome" in lower:
                start_idx = idx
                break

        if start_idx is not None and start_idx > 0:
            cleaned_lines = lines[start_idx:]
        else:
            cleaned_lines = lines

        # Strip leading/trailing blank lines
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()

        return "\n".join(cleaned_lines)

    def enrich_text(self, text, enhancement_prompt=None):
        """Enrich text using Google Gemini API.

        Optionally uses a custom enhancement_prompt; otherwise falls back to the
        default audiobook-style prompt.
        """
        if not enhancement_prompt:
            enhancement_prompt = """Transform this text into an engaging, conversational audiobook script. Make it sound natural and warm when spoken aloud.

SPECIFIC INSTRUCTIONS:
1. Make it engaging and conversational - rewrite it so it feels like a friendly narrator is speaking directly to the listener, not just reading a document.

2. Optimize for spoken flow - rewrite sentences so they flow naturally when spoken aloud. Break down long or complex sentences into clear, shorter sentences that are easy to follow.

3. Add natural pauses - use "..." (three dots) to indicate natural pauses for rhythm and engagement. Add line breaks between major sections for better pacing.

4. Remove all Markdown formatting - remove raw Markdown symbols like #, *, -, [], (), etc., but keep ALL the information they represent. Convert headings into spoken introductions, convert bullet points into conversational lists.

5. Rewrite lists conversationally - transform bullet points or numbered lists into spoken style. For example: "First... then... finally..." or "You'll need to consider several things. First... Second... And finally..."

6. Expand abbreviations - replace abbreviations with full phrases:
   - "e.g." → "for example"
   - "etc." → "and so on"
   - "i.e." → "that is"
   - "vs." → "versus" or "compared to"
   - Any other abbreviations should be expanded naturally

7. Maintain information depth - keep all the same information and depth, just make it more engaging, warm, and listener-friendly. Don't remove any technical details or important information.

8. Use conversational transitions - add phrases like "Now, let's talk about...", "Here's something interesting...", "What you need to know is...", "Let me explain..."

The output should sound like a skilled narrator telling a story, not like someone reading a technical document. Make it engaging while preserving all the original content."""
        
        try:
            full_prompt = f"{enhancement_prompt}\n\nOriginal text:\n{text}"
            
            print("Enriching text using Google Gemini API...")
            response = self.model.generate_content(full_prompt)
            
            if response.text:
                cleaned = self._post_process_enriched_text(response.text.strip())
                return cleaned
            else:
                raise Exception("No response from Gemini API")
                
        except Exception as e:
            raise Exception(f"Error enriching text: {str(e)}")
    
    def enrich_file(self, file_path):
        """
        Read text from file, enrich it, and return enriched text
        
        Args:
            file_path: Path to text file
            
        Returns:
            Enriched text as string
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return self.enrich_text(text)
    
    def save_enriched_text(self, original_file_path, enriched_text):
        """
        Save enriched text to a file
        
        Args:
            original_file_path: Original extracted text file path
            enriched_text: Enriched text to save
            
        Returns:
            Path to saved enriched text file
        """
        original_file = Path(original_file_path)
        output_filename = original_file.stem.replace("_extracted", "_enriched") + ".txt"
        output_path = self.output_folder / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(enriched_text)
        
        return output_path
    
    def process_file(self, extracted_file_path, enhancement_prompt=None):
        """
        Enrich text from extracted file and save it
        
        Args:
            extracted_file_path: Path to extracted text file
            enhancement_prompt: Custom prompt for enrichment (optional)
            
        Returns:
            Tuple of (enriched_text, saved_file_path)
        """
        print(f"Enriching text from: {extracted_file_path}")
        
        with open(extracted_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        enriched_text = self.enrich_text(text, enhancement_prompt)
        saved_path = self.save_enriched_text(extracted_file_path, enriched_text)
        print(f"Text enriched and saved to: {saved_path}")
        return enriched_text, saved_path

