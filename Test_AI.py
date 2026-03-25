import yfinance as yf
import google.generativeai as genai
import os
import time

GEMINI_KEY = os.environ.get("GEMINI_KEY") 

def get_ai_analysis(stock_id):
    print(f"\n[AI] 啟動分析流程: {stock_id}")
    try:
        if not GEMINI_KEY:
            return "❌ 系統錯誤：找不到 GEMINI_KEY。"
            
        genai.configure(api_key=GEMINI_KEY, transport='rest')
        
        # 【終極修正】：換成 gemini-1.5-flash-8b (請求限制最寬鬆的模型)
        model = genai.GenerativeModel('gemini-1.5-flash-8b')

        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        print(f"[AI] 正在抓取股票資料: {ticker_id}")
        
        stock = yf.Ticker(ticker_id)
        
        # 使用最快的方式抓取股價
        price_history = stock.history(period="1d")
        if not price_history.empty:
            price = price_history['Close'].iloc[-1]
            print(f"[AI] 成功獲取價格: {price:.2f}")
        else:
            price = stock.fast_info['last_price']
            print(f"[AI] 使用 fast_info 獲取價格: {price:.2f}")

        prompt = f"你是一位分析師，請針對台股 {stock_id} (目前股價約 {price:.2f} 元) 提供一段約 100 字的繁體中文分析，重點在於該公司的產業地位與近期趨勢。"
        
        print("[AI] 正在呼叫 Gemini API (8b 輕量版)...")
        # 加上最後的保險：如果失敗，等 1 秒重試一次
        try:
            response = model.generate_content(prompt)
        except:
            time.sleep(1)
            response = model.generate_content(prompt)
            
        if response and response.text:
            print("[AI] 分析成功完成")
            return response.text
        else:
            return "❌ AI 暫時無法產出分析，請稍後再試。"
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 錯誤詳情: {error_msg}")
        if "429" in error_msg:
            return "❌ Google API 偵測到流量異常。請等候 5 分鐘再查詢，或嘗試輸入其他代號。"
        return f"❌ 分析失敗: {error_msg}"