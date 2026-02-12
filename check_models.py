# File: check_models.py
from google import genai
import os
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found, please check your .env file")
else:
    print(f"API Key loaded: {api_key[:5]}...")
    
    # 2. Initialize Client with new SDK
    client = genai.Client(api_key=api_key)

    print("\n🔍 Fetching available models for your API Key...")
    try:
        found = False
        for m in client.models.list():
            # The new SDK has a different structure - just list all models
            print(f"   - {m.name}")
            found = True
        
        if not found:
            print("Strange, no models were found.")
    except Exception as e:
        print(f"Query failed: {e}")
