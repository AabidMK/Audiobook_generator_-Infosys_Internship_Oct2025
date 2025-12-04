"""
Quick test script to verify Google Gemini API key is working
"""

import os
import google.generativeai as genai

# API key
API_KEY = "AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak"

try:
    # Configure the API
    genai.configure(api_key=API_KEY)
    
    # List available models first
    print("Checking available models...")
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    print(f"Available models: {models}")
    
    # Use the first available model (usually gemini-1.5-flash or gemini-1.5-pro)
    if models:
        model_name = models[0].split('/')[-1]  # Get just the model name
        print(f"\nUsing model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        # Test with a simple prompt
        print("Testing Google Gemini API connection...")
        response = model.generate_content("Say 'Hello, API is working!' in one sentence.")
        
        if response.text:
            print(f"✅ API is working! Response: {response.text}")
            print(f"\n🎉 Your API key is valid! Using model: {model_name}")
        else:
            print("❌ API responded but with no text content")
    else:
        print("❌ No available models found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease check:")
    print("1. API key is correct")
    print("2. You have internet connection")
    print("3. API quota hasn't been exceeded")
