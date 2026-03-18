import yfinance as yf
import google.generativeai as genai
import os

# 從系統環境變數讀取金鑰
GEMINI_KEY = os.environ.get("GEMINI_KEY") 

# 設定 Google AI
genai.configure(api_key=GEMINI_KEY)

# 使用正式版 1.5 Flash 模型 (額度較高且穩定)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_analysis(stock_id):
    """
    輸入股票代號，抓取數據並回傳 AI 分析結果
    """
    print(f"\n[AI Agent] 正在分析股票: {stock_id}")
    
    try:
        # 1. 處理代號 (數字則加 .TW，英文如 AAPL 則維持原樣)
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        stock = yf.Ticker(ticker_id)
        
        # 2. 抓取股價與基本資料
        fast_info = stock.fast_info
        price = fast_info['last_price']
        stock_name = stock.info.get('longName', stock_id)
        print(f"✅ 抓取成功: {stock_name}, 現價: {price:.2f}")
        
        # 3. 準備 AI 指令
        prompt = f"你是一位專業分析師，請針對台股 {stock_name} ({stock_id}) 目前約 {price:.2f} 元的股價，提供一段簡短的繁體中文分析，重點在於近期趨勢與市場表現。"
        
        # 4. 呼叫 Gemini
        response = model.generate_content(prompt)
        print("✅ AI 生成完畢")
        return response.text
    
    except Exception as e:
        error_str = str(e)
        print(f"❌ 錯誤詳情: {error_str}")
        
        # 針對常見錯誤回傳親切的提示
        if "429" in error_str or "Rate limited" in error_str:
            return "❌ 目前 API 請求過於頻繁，請等候約 5 分鐘後再試。"
        elif "last_price" in error_str:
            return f"❌ 找不到股票代號 '{stock_id}'，請確認輸入是否正確。"
        return f"❌ 抱歉，暫時無法分析：{error_str}"

# 本地測試區 (在雲端時不會跑這段)
if __name__ == "__main__":
    code = input("請輸入測試代號 (如 2330): ")
    print(get_ai_analysis(code))