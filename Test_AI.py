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
            
        # 強制使用 rest 傳輸模式，對雲端環境最穩定
        genai.configure(api_key=GEMINI_KEY, transport='rest')
        
        # 【核心修正】：直接使用 'gemini-1.5-flash'
        # 如果還是 404，SDK 會自動處理前綴
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 3. 處理代號
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        print(f"[AI] 正在抓取 yfinance 資料: {ticker_id}")
        
        stock = yf.Ticker(ticker_id)
        
        # 4. 抓取價格 (使用 history 確保穩定)
        price_history = stock.history(period="1d")
        if not price_history.empty:
            price = price_history['Close'].iloc[-1]
            print(f"[AI] 成功獲取價格: {price:.2f}")
        else:
            # 備用方案
            price = stock.fast_info['last_price']
            print(f"[AI] 使用 fast_info 獲取價格: {price:.2f}")

        # 5. 準備 Prompt
        prompt = f"你是一位證券分析師，請針對台股 {stock_id} (目前股價約 {price:.2f} 元) 提供一段約 100 字的繁體中文分析，重點在於該公司的產業地位與近期趨勢。"
        
        print("[AI] 正在呼叫 Gemini API...")
        # 6. 執行生成
        response = model.generate_content(prompt)
        
        # 檢查回應是否存在
        if response and response.text:
            print("[AI] 分析成功完成")
            return response.text
        else:
            return "❌ AI 暫時無法產出分析內容，請稍後再試。"
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 錯誤詳情: {error_msg}")
        
        # 針對 404 錯誤提供自動修復建議
        if "404" in error_msg:
            return "❌ 模型連線路徑錯誤。請確認 GEMINI_KEY 是否正確且具備 Gemini 1.5 存取權限。"
        elif "429" in error_msg:
            return "❌ API 請求過於頻繁，請等候約 5 分鐘再試。"
        return f"❌ 分析失敗: {error_msg}"

if __name__ == "__main__":
    # 本地測試
    print(get_ai_analysis("2330"))