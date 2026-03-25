import yfinance as yf
import requests
import os

GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(stock_id):
    print(f"\n[AI] 啟動 Groq 最新模型分析: {stock_id}")
    try:
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到 GROQ_KEY 環境變數。"

        # 1. 抓取股票資料
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        stock = yf.Ticker(ticker_id)
        
        price_history = stock.history(period="1d")
        if not price_history.empty:
            price = price_history['Close'].iloc[-1]
            print(f"[AI] 成功獲取價格: {price:.2f}")
        else:
            return f"❌ 暫時無法抓取 {stock_id} 的股價資料。"

        # 2. 呼叫 Groq API 
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        # 【關鍵修正】：使用最新、沒下架的模型 llama-3.1-8b-instant
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system", 
                    "content": "你是一位專業的台股分析師，請使用繁體中文回覆。內容要專業、精簡，約 80 字以內。"
                },
                {
                    "role": "user", 
                    "content": f"分析台股代號 {stock_id}，目前股價為 {price:.2f} 元。請說明其產業地位與近期趨勢。"
                }
            ],
            "temperature": 0.5
        }

        print(f"[AI] 正在向 Groq 發送請求 (使用 Llama 3.1)...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            ai_text = result['choices'][0]['message']['content']
            print("[AI] 分析成功完成！")
            return ai_text
        else:
            print(f"❌ Groq 錯誤回報: {response.text}")
            return f"❌ AI 服務異常 (代碼 {response.status_code})"

    except Exception as e:
        print(f"❌ 發生異常: {str(e)}")
        return f"❌ 分析失敗: {str(e)}"

if __name__ == "__main__":
    print(get_ai_analysis("2330"))