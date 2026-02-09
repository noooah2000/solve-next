# File: check_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found, please check your .env file")
else:
    print(f"✅ API Key loaded: {api_key[:5]}...")
    
    # 2. Configure API
    genai.configure(api_key=api_key)

    print("\n🔍 Fetching available models for your API Key...")
    try:
        found = False
        for m in genai.list_models():
            # We only need models that support 'generateContent' (text generation)
            if 'generateContent' in m.supported_generation_methods:
                print(f"   - {m.name}")
                found = True
        
        if not found:
            print("❌ Strange, no models supporting text generation were found.")
    except Exception as e:
        print(f"❌ Query failed: {e}")