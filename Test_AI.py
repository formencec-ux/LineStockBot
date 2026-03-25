import yfinance as yf
import requests
import os

# 放到函式外面，確保啟動時就讀取
GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(stock_id):
    # 偵錯用：印出 Key 的前三個字 (確保有讀到，又不外流)
    key_check = str(GROQ_KEY)[:3] if GROQ_KEY else "無"
    print(f"\n[AI] 啟動 Groq 分析. 代號: {stock_id}, Key檢查: {key_check}...")

    if not GROQ_KEY or len(GROQ_KEY) < 10:
        return "❌ 系統錯誤：Render 環境變數 GROQ_KEY 設定不正確或未讀取。"

    try:
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        stock = yf.Ticker(ticker_id)
        price_history = stock.history(period="1d")
        
        if price_history.empty:
            return f"❌ 找不到股票 {stock_id} 的價格。"
            
        price = price_history['Close'].iloc[-1]

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_KEY.strip()}", # 增加 .strip() 自動去掉可能存在的空格
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "你是一位台股分析師，請用繁體中文回覆，約 60 字。"},
                {"role": "user", "content": f"分析台股 {stock_id}，股價 {price:.2f}。"}
            ]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            # 這裡會印出更詳細的錯誤原因
            print(f"❌ Groq API 詳細錯誤: {response.text}")
            return f"❌ 服務暫時繁忙 (代碼 {response.status_code})，請稍後再試。"

    except Exception as e:
        return f"❌ 程式異常: {str(e)}"