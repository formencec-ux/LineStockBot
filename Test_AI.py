import yfinance as yf
import google.generativeai as genai
import os

GEMINI_KEY = os.environ.get("GEMINI_KEY") 

def get_ai_analysis(stock_id):
    print(f"\n[AI] 啟動分析流程: {stock_id}")
    try:
        if not GEMINI_KEY:
            return "❌ 系統錯誤：找不到 GEMINI_KEY。"
            
        # 【核心修正】：強制使用 rest 模式，這在雲端環境最穩定
        genai.configure(api_key=GEMINI_KEY, transport='rest')
        model = genai.GenerativeModel('gemini-1.5-flash')

        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        print(f"[AI] 正在抓取股票資料: {ticker_id}")
        
        stock = yf.Ticker(ticker_id)
        
        # 使用快速抓取法
        price_history = stock.history(period="1d")
        if not price_history.empty:
            price = price_history['Close'].iloc[-1]
        else:
            price = stock.fast_info['last_price']
            
        print(f"[AI] 獲取價格成功: {price:.2f}")

        prompt = f"你是一位分析師，請針對台股 {stock_id} (股價 {price:.2f} 元) 提供一段約 80 字的繁體中文分析。"
        
        print("[AI] 正在呼叫 Gemini API (REST 模式)...")
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        else:
            return "❌ AI 暫時無法產出文字內容。"
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 錯誤詳情: {error_msg}")
        # 如果還是 429，我們回傳更具體的建議
        if "429" in error_msg or "Rate limited" in error_msg:
            return "❌ Google API 偵測到流量異常。請 10 分鐘後再嘗試查詢，或稍後再試一次。"
        return f"❌ 分析失敗: {error_msg}"