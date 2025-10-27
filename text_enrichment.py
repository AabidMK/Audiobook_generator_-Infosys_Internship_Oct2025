import google.generativeai as genai

# Step 1: Configure your Gemini API key
genai.configure(api_key="AIzaSyB6Ev_MuYb1cyovoYjEyb1DOrOlTWWbmFI")  # Replace with your actual API key

# Step 2: Select model (use the one from your working list)
model = genai.GenerativeModel("models/gemini-2.5-pro")

# Step 3: Read input text from file
input_file = "text_extraction_outputs/sample4_extractedtext_output.txt"
output_file = "sample4_enriched_output.txt"

with open(input_file, "r", encoding="utf-8") as f:
    input_text = f.read()

# Step 4: Create a system-style prompt
system_prompt = (
    "You are an expert text rewriter. Rewrite the following text to make it clearer, "
    "more engaging, grammatically correct, and professional, while keeping the same meaning:\n\n"
)

# Step 5: Generate enriched text from Gemini
print("⏳ Sending text to Gemini for enrichment...")

response = model.generate_content(system_prompt + input_text)

# Step 6: Save the enriched output
with open(output_file, "w", encoding="utf-8") as f:
    f.write(response.text)

print("✅ Enrichment complete! Enriched text saved to:", output_file)
