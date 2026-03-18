import yfinance as yf
import google.generativeai as genai
import os

# 確保金鑰存在
GEMINI_KEY = os.environ.get("GEMINI_KEY") 

def get_ai_analysis(stock_id):
    print(f"\n[AI] 啟動分析流程: {stock_id}")
    try:
        # 設定 API
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 處理代號
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        print(f"[AI] 正在抓取 yfinance 資料: {ticker_id}")
        
        stock = yf.Ticker(ticker_id)
        
        # 嘗試抓取價格 (加上嘗試機制)
        try:
            price = stock.fast_info['last_price']
            print(f"[AI] 成功獲取價格: {price}")
        except:
            # 如果 fast_info 失敗，嘗試最原始的方法
            price_history = stock.history(period="1d")
            price = price_history['Close'].iloc[-1]
            print(f"[AI] 使用備用方案獲取價格: {price}")

        # 準備 Prompt
        prompt = f"你是一位證券分析師，請針對台股 {stock_id} (目前股價 {price:.2f}) 提供一段約 100 字的繁體中文深入分析，包含產業地位與近期趨勢。"
        
        print("[AI] 正在呼叫 Gemini API...")
        response = model.generate_content(prompt)
        print("[AI] 分析成功完成")
        return response.text
    
    except Exception as e:
        error_msg = f"❌ 分析過程出錯: {str(e)}"
        print(error_msg)
        return error_msg