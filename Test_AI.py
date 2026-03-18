import yfinance as yf
import google.generativeai as genai
import os

# 1. 讀取環境變數
GEMINI_KEY = os.environ.get("GEMINI_KEY") 

def get_ai_analysis(stock_id):
    print(f"\n[AI] 啟動分析流程: {stock_id}")
    try:
        # 2. 設定 API (確保 API Key 存在)
        if not GEMINI_KEY:
            return "❌ 系統錯誤：找不到 GEMINI_KEY 環境變數。"
            
        genai.configure(api_key=GEMINI_KEY)
        
        # 【關鍵修正】：直接使用 'gemini-1.5-flash'，不加 models/ 前綴，讓 SDK 自動適應版本
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 3. 處理代號
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        print(f"[AI] 正在抓取 yfinance 資料: {ticker_id}")
        
        stock = yf.Ticker(ticker_id)
        
        # 4. 嘗試抓取價格 (使用更相容的 history 方法)
        price_history = stock.history(period="1d")
        if not price_history.empty:
            price = price_history['Close'].iloc[-1]
            print(f"[AI] 成功獲取價格: {price:.2f}")
        else:
            # 備用方案：嘗試 fast_info
            price = stock.fast_info['last_price']
            print(f"[AI] 使用 fast_info 獲取價格: {price:.2f}")

        # 5. 準備 Prompt
        prompt = f"你是一位證券分析師，請針對台股 {stock_id} (目前股價約 {price:.2f} 元) 提供一段約 100 字的繁體中文分析，重點在於該公司的產業地位與近期趨勢。"
        
        print("[AI] 正在呼叫 Gemini API...")
        # 6. 執行生成
        response = model.generate_content(prompt)
        
        if response and response.text:
            print("[AI] 分析成功完成")
            return response.text
        else:
            return "❌ AI 回應為空，請稍後再試。"
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 錯誤詳情: {error_msg}")
        
        # 針對常見錯誤提供提示
        if "429" in error_msg:
            return "❌ API 請求過於頻繁，請等候約 5 分鐘再試。"
        elif "404" in error_msg:
            return "❌ 模型連線錯誤，請通知開發者調整 API 版本。"
        return f"❌ 分析失敗: {error_msg}"

if __name__ == "__main__":
    # 本地測試
    print(get_ai_analysis("2330"))