import google.generativeai as genai
import os

# ✅ Your Gemini API Key
API_KEY = "AIzaSyBqpmh1O0CwchICLzcwD1mcNivyWbO8vts"

# ✅ Configure Gemini
genai.configure(api_key=API_KEY)

# ✅ Load Input Text
input_file = r"C:\Users\hp\Desktop\SM\infy internship\text_enrichment\input.txt"
output_file = r"C:\Users\hp\Desktop\SM\infy internship\text_enrichment\output.txt"

def enrich_text():
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("❌ Input file is empty.")
        return

    print("✨ Sending text to Gemini for enrichment...")

    try:
        # Use one of the available models from your list
        model = genai.GenerativeModel(model_name="models/gemini-2.0-flash-001")
        
        prompt = f"""Please enhance the clarity and readability of the following academic content while maintaining its original meaning and academic tone:

{text}

Please provide an improved version that is:
- More structured and organized
- Clearer and more concise  
- Better flowing and readable
- Maintains academic integrity
- Preserves all key information and concepts"""

        response = model.generate_content(prompt)
        enriched_text = response.text.strip()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(enriched_text)

        print("✅ Enrichment complete!")
        print(f"💾 Output saved to: {output_file}")
        
        # Print a preview of the enriched text
        print("\n📝 Enriched Text Preview:")
        print(enriched_text[:500] + "..." if len(enriched_text) > 500 else enriched_text)

    except Exception as e:
        print(f"❌ Error during enrichment: {str(e)}")

if __name__ == "__main__":
    enrich_text()