import requests
import os

GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(stock_id):
    print(f"\n[AI] 進入純 AI 測試階段. 代號: {stock_id}")
    
    if not GROQ_KEY:
        return "❌ 系統錯誤：找不到 GROQ_KEY。"

    try:
        # --- 暫時不用 yfinance，直接給一個固定股價測試 ---
        test_price = 265.0 
        print(f"[AI] 略過抓取，直接使用測試股價: {test_price}")

        # 呼叫 Groq API
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "你是一位台股分析師，請用繁體中文回覆，約 60 字。"},
                {"role": "user", "content": f"分析台股 {stock_id}，目前股價約 {test_price}。"}
            ]
        }

        print("[AI] 正在直連 Groq API...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"❌ Groq 錯誤: {response.status_code} - {response.text}")
            return f"⚠️ AI 暫時無法回應 (代碼 {response.status_code})"

    except Exception as e:
        print(f"❌ 異常發生: {str(e)}")
        return f"❌ 異常: {str(e)}"