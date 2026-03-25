import requests
import os

GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(stock_id):
    print(f"\n[AI] 啟動直連版分析流程: {stock_id}")
    try:
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到 GROQ_KEY。"

        # 1. 【核心修正】：不使用 yfinance，改用 requests 直接抓 Yahoo API
        ticker_id = f"{stock_id}.TW"
        url_yahoo = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_id}"
        headers_yahoo = {"User-Agent": "Mozilla/5.0"} # 偽裝成瀏覽器
        
        print(f"[AI] 正在直連 Yahoo 抓取資料: {ticker_id}")
        resp_yahoo = requests.get(url_yahoo, headers=headers_yahoo, timeout=10)
        
        if resp_yahoo.status_code == 200:
            data = resp_yahoo.json()
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            print(f"[AI] 成功獲取價格: {price:.2f}")
        else:
            # 備用方案：如果還是被鎖，我們回傳特定錯誤，至少知道是哪裡掛掉
            print(f"❌ Yahoo API 報錯: {resp_yahoo.status_code}")
            return f"❌ 股價抓取服務被擋 (代碼 {resp_yahoo.status_code})，請稍後再試。"

        # 2. 呼叫 Groq API 
        url_groq = "https://api.groq.com/openai/v1/chat/completions"
        headers_groq = {
            "Authorization": f"Bearer {GROQ_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "你是一位專業的台股分析師，請使用繁體中文，約 80 字分析。"},
                {"role": "user", "content": f"分析台股 {stock_id}，目前股價約 {price:.2f} 元。"}
            ]
        }

        print("[AI] 正在向 Groq 發送請求...")
        resp_groq = requests.post(url_groq, headers=headers_groq, json=payload, timeout=10)
        
        if resp_groq.status_code == 200:
            return resp_groq.json()['choices'][0]['message']['content']
        else:
            return f"❌ AI 服務繁忙 (代碼 {resp_groq.status_code})"

    except Exception as e:
        print(f"❌ 發生異常: {str(e)}")
        # 如果最後還是噴 Rate limited，代表 Yahoo 真的連直連都鎖 IP 了
        if "Rate limited" in str(e) or "Too Many Requests" in str(e):
            return "⚠️ 資料抓取頻繁，請 5 分鐘後再試。"
        return f"❌ 分析失敗: {str(e)}"