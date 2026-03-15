import yfinance as yf
import google.generativeai as genai
import os

# 設定 Gemini API Key
GEMINI_KEY = "AIzaSyD5bQNNQrEBmV8lbg5zoU0e74ZV2GmcQxI" 
genai.configure(api_key=GEMINI_KEY, transport='rest')

# 使用你清單中確認可用的模型
model = genai.GenerativeModel('models/gemini-3-flash-preview')

def get_ai_analysis(stock_id):
    """
    這是一個可以被外部呼叫的函數，輸入代號，回傳 AI 分析結果
    """
    print(f"\n[AI Agent] 開始處理股票: {stock_id}")
    
    try:
        # 處理股票代號 (加上 .TW 代表台股)
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        stock = yf.Ticker(ticker_id)
        
        # 抓取數據
        fast_info = stock.fast_info
        price = fast_info['last_price']
        stock_name = stock.info.get('longName', stock_id)
        print(f"✅ 成功獲取 {stock_name}，股價: {price:.2f}")
        
        # 準備送給 AI 的 Prompt
        prompt = f"你是一位專業分析師，請簡短分析台股 {stock_name} ({stock_id})，目前股價約 {price:.2f}。請用繁體中文回答。"
        
        # 執行生成
        response = model.generate_content(prompt)
        print("✅ AI 分析完成")
        return response.text
    
    except Exception as e:
        error_msg = f"❌ 分析失敗: {str(e)}"
        print(error_msg)
        return error_msg

# 測試用入口
if __name__ == "__main__":
    code = input("請輸入股票代號 (例如 2330): ")
    print(get_ai_analysis(code))