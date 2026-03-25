import yfinance as yf
from google import genai
import os

# 1. 讀取環境變數
GEMINI_KEY = os.environ.get("GEMINI_KEY")

def get_ai_analysis(stock_id):
    print(f"\n[AI] 啟動新版 SDK 分析流程: {stock_id}")
    try:
        if not GEMINI_KEY:
            return "❌ 系統錯誤：找不到 GEMINI_KEY。"

        # 2. 初始化最新版 Client
        client = genai.Client(api_key=GEMINI_KEY)

        # 3. 處理股票代號
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        print(f"[AI] 正在抓取股票資料: {ticker_id}")
        
        stock = yf.Ticker(ticker_id)
        
        # 抓取價格
        price_history = stock.history(period="1d")
        if not price_history.empty:
            price = price_history['Close'].iloc[-1]
        else:
            price = stock.fast_info['last_price']
            
        print(f"[AI] 獲取價格成功: {price:.2f}")

        # 4. 準備 Prompt
        prompt = f"你是一位證券分析師，請針對台股 {stock_id} (目前股價約 {price:.2f} 元) 提供一段約 100 字的繁體中文分析，重點在於該公司的產業地位與近期趨勢。"
        
        print("[AI] 正在呼叫最新版 Gemini API...")
        # 5. 執行生成 (使用最新語法)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        
        if response and response.text:
            print("[AI] 分析成功完成")
            return response.text
        else:
            return "❌ AI 暫時無法產出文字內容。"
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 錯誤詳情: {error_msg}")
        # 針對 429 錯誤給予提示
        if "429" in error_msg:
            return "❌ 目前 API 請求量過大，請稍候 5 分鐘再試。"
        return f"❌ 分析失敗: {error_msg}"

if __name__ == "__main__":
    # 本地測試
    print(get_ai_analysis("2330"))