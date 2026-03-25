import yfinance as yf
from google import genai
import os
import time

GEMINI_KEY = os.environ.get("GEMINI_KEY")

def get_ai_analysis(stock_id):
    print(f"\n[AI] 啟動 8b 穩定版分析: {stock_id}")
    try:
        if not GEMINI_KEY:
            return "❌ 系統錯誤：找不到 GEMINI_KEY。"

        # 初始化 Client
        client = genai.Client(api_key=GEMINI_KEY)

        # 1. 快速抓取資料 (只抓價格，不抓 info 避免逾時)
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        stock = yf.Ticker(ticker_id)
        price_history = stock.history(period="1d")
        
        if not price_history.empty:
            price = price_history['Close'].iloc[-1]
        else:
            price = stock.fast_info['last_price']
            
        print(f"[AI] 價格獲取成功: {price:.2f}")

        # 2. 準備精簡 Prompt
        prompt = f"分析台股 {stock_id}，目前股價 {price:.2f}。請用繁體中文回覆兩句重點。"

        # 3. 嘗試呼叫 (加入重試機制)
        max_retries = 2
        for i in range(max_retries):
            try:
                print(f"[AI] 正在呼叫 Gemini 8b (第 {i+1} 次嘗試)...")
                response = client.models.generate_content(
                    model="gemini-1.5-flash-8b",
                    contents=prompt
                )
                if response and response.text:
                    print("[AI] 分析成功完成")
                    return response.text
            except Exception as e:
                if "429" in str(e) and i < max_retries - 1:
                    print("[AI] 遇到 429，等待 2 秒後重試...")
                    time.sleep(2)
                    continue
                else:
                    raise e
        
        return "❌ 目前 API 繁忙，請稍後再試。"

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 錯誤詳情: {error_msg}")
        if "429" in error_msg:
            return "❌ Google API 流量管制中。建議 15 分鐘後再嘗試，或更換 API Key。"
        return f"❌ 分析失敗: {error_msg}"