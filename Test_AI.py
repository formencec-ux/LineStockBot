import yfinance as yf
import requests
import os
import json

GEMINI_KEY = os.environ.get("GEMINI_KEY")

def get_ai_analysis(stock_id):
    print(f"\n[AI] 啟動直連版分析: {stock_id}")
    try:
        if not GEMINI_KEY:
            return "❌ 系統錯誤：找不到 GEMINI_KEY。"

        # 1. 快速抓取資料 (確保資料端沒問題)
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        stock = yf.Ticker(ticker_id)
        price_history = stock.history(period="1d")
        price = price_history['Close'].iloc[-1] if not price_history.empty else 0
        
        if price == 0:
            return f"❌ 找不到股票代號 {stock_id} 的價格資料。"

        # 2. 準備直接發送給 Google API 的 JSON 資料
        # 使用最新的 v1 版本 API，這比 v1beta 更穩定
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-8b:generateContent?key={GEMINI_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": f"你是一位分析師，針對台股 {stock_id} 目前股價 {price:.2f} 元，提供一段約 80 字的繁體中文分析。"}]
            }]
        }

        # 3. 發送請求
        print(f"[AI] 正在直連 Google API (模型: 1.5-flash-8b)...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()

        # 4. 處理回傳
        if response.status_code == 200:
            # 解析 Google 回傳的格式
            try:
                ai_text = result['candidates'][0]['content']['parts'][0]['text']
                print("[AI] 分析成功完成")
                return ai_text
            except:
                return "❌ AI 回傳格式異常，請稍後再試。"
        elif response.status_code == 429:
            print(f"❌ 觸發頻率限制 (429): {result}")
            return "⚠️ 目前 Google API 流量管制中，請 10 分鐘後再試。"
        else:
            print(f"❌ API 錯誤 ({response.status_code}): {result}")
            return f"❌ AI 連線失敗 (代碼 {response.status_code})"

    except Exception as e:
        print(f"❌ 程式發生錯誤: {str(e)}")
        return f"❌ 分析失敗: {str(e)}"

if __name__ == "__main__":
    print(get_ai_analysis("2330"))