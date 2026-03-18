import yfinance as yf
import google.generativeai as genai
import os

GEMINI_KEY = os.environ.get("GEMINI_KEY") 
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_analysis(stock_id):
    print(f"\n[AI Agent] 處理中: {stock_id}")
    try:
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        stock = yf.Ticker(ticker_id)
        
        # 改用 fast_info，這比 .info 快非常多
        price = stock.fast_info['last_price']
        
        # 準備簡單的 Prompt
        prompt = f"你是一位資深證券分析師，針對台股 {stock_id} 目前股價 {price:.2f} 元，請結合該公司的產業趨勢與近期大盤走勢，提供一段約 100 字的繁體中文深入分析。"
        
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            return "❌ API 忙碌中，請 5 分鐘後再試。"
        return f"❌ 錯誤: {stock_id} 抓取失敗。"

if __name__ == "__main__":
    print(get_ai_analysis("2330"))