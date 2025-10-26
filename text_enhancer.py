import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class TextEnhancer:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def enhance_with_gemini(self, text, style):
        try:
            prompt = f"Enhance the following text in a {style} style:\n\n{text}"
            response = self.model.generate_content(prompt)
            return {
                "success": True,
                "enhanced_text": response.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
