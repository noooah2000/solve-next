# 檔案：check_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. 載入環境變數
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 錯誤：找不到 GEMINI_API_KEY，請檢查 .env 檔案")
else:
    print(f"✅ 讀取到 API Key: {api_key[:5]}...")
    
    # 2. 設定 API
    genai.configure(api_key=api_key)

    print("\n🔍 正在查詢你的 API Key 可用的模型列表...")
    try:
        found = False
        for m in genai.list_models():
            # 我們只需要支援 'generateContent' (生成文字) 的模型
            if 'generateContent' in m.supported_generation_methods:
                print(f"   - {m.name}")
                found = True
        
        if not found:
            print("❌ 奇怪，沒有找到任何支援生成的模型。")
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")