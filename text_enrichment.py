import google.generativeai as genai

genai.configure(api_key="AIzaSyB6Ev_MuYb1cyovoYjEyb1DOrOlTWWbmFI")

model = genai.GenerativeModel("models/gemini-2.5-pro")

input_file = "text_extraction_outputs/sample4_extractedtext_output.txt"
output_file = "sample4_enriched_output.txt"

with open(input_file, "r", encoding="utf-8") as f:
    text = f.read()

prompt = f"""
Rewrite the following text clearly and professionally.
Do not include options or explanations — return only one improved version.
Keep the tone natural and fluent.

Text:
{text}
"""

response = model.generate_content(prompt)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(response.text)

print("✅ Enriched text saved successfully in enriched_text.txt")


