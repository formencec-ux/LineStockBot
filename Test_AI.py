import yfinance as yf
import google.generativeai as genai
import os

# 讀取環境變數
GEMINI_KEY = os.environ.get("GEMINI_KEY") 

# 設定 API (移除 transport='rest' 增加穩定度)
genai.configure(api_key=GEMINI_KEY)

# 【修改處】：使用更穩定的正式版 1.5 Flash 模型
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_analysis(stock_id):
    """
    輸入代號，抓取數據並回傳 AI 分析結果
    """
    print(f"\n[AI Agent] 開始處理股票: {stock_id}")
    
    try:
        # 處理股票代號 (加上 .TW 代表台股)
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        stock = yf.Ticker(ticker_id)
        
        # 抓取數據 (加入逾時保護與錯誤檢查)
        fast_info = stock.fast_info
        price = fast_info['last_price']
        stock_name = stock.info.get('longName', stock_id)
        print(f"✅ 成功獲取 {stock_name}，股價: {price:.2f}")
        
        # 準備送給 AI 的 Prompt
        prompt = f"你是一位專業分析師，請簡短分析台股 {stock_name} ({stock_id})，目前股價約 {price:.2f}。請用繁體中文回答，重點在於趨勢與近期表現。"
        
        # 執行生成
        response = model.generate_content(prompt)
        print("✅ AI 分析完成")
        return response.text
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 分析失敗: {error_msg}")
        # 如果是 API 流量限制的錯誤訊息，回傳清楚的提示
        if "429" in error_msg or "Rate limited" in error_msg:
            return "❌ 目前 API 請求過於頻繁，請等候約 5-10 分鐘再試。"
        return f"❌ 抓取資料或分析時發生錯誤: {error_msg}"

if __name__ == "__main__":
    code = input("請輸入股票代號 (例如 2330): ")
    print(get_ai_analysis(code))