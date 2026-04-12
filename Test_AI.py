import yfinance as yf
import requests
import os

# 從系統環境變數中讀取 Groq 的 API Key
GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(stock_id):
    """
    輸入股票代號，執行資深投資分析助理的專業分析流程
    """
    print(f"\n[AI] 啟動直連版分析流程: {stock_id}")
    
    try:
        # 1. 檢查 API Key 是否存在
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到 GROQ_KEY。"

        # 2. 抓取股價資料 (採用直連 Yahoo API 避免 IP 封鎖)
        # 判斷輸入是否為純數字，若是則自動加上台股後綴 .TW
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        url_yahoo = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_id}"
        headers_yahoo = {"User-Agent": "Mozilla/5.0"} # 偽裝成一般瀏覽器
        
        print(f"[AI] 正在直連 Yahoo 抓取資料: {ticker_id}")
        resp_yahoo = requests.get(url_yahoo, headers=headers_yahoo, timeout=10)
        
        if resp_yahoo.status_code == 200:
            data = resp_yahoo.json()
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            print(f"[AI] 成功獲取價格: {price:.2f}")
        else:
            # 拒絕機制：如果是非台股或錯誤代碼，給予溫柔提醒
            print(f"❌ Yahoo API 報錯: {resp_yahoo.status_code}")
            return "⚠️ 提醒：目前僅支援台股查詢（如 2330），請確認代號是否正確。"

        # 3. AI Agent 提示詞設定 (角色設定與任務指令)
        system_prompt = """
        角色設定：你是一位精通全球資本市場的「資深投資分析助理」。你擅長結合即時財務數據（量化）與市場新聞趨勢（質化），為投資人提供客觀、冷靜且具備洞察力的分析建議。

        🛠 任務指令：
        當使用者輸入一個股票代號時，請嚴格執行以下三個分析步驟：

        第一步：多維度財務與籌碼掃描
        1. 估值指標：報告目前股價、目前的 PE Ratio (本益比)，並說明該數值位於歷史區間的相對位置（高/中/低）。
        2. 籌碼與動能：簡述法人與大戶進出趨勢。
        3. 業務動態：摘要最近營收表現與核心業務增長點。

        第二步：Google News 即時新聞摘要 (模擬最新趨勢)
        1. 針對最近期 3 則關鍵新聞提供：標題、關鍵摘要。
        2. 分析新聞對股價的潛在影響（利多/利空/中立）。

        第三步：投資人視視角綜合評估
        先分析營收狀況，再給予趨勢預測。基於上述數據，以投資人立場給予建議。必須涵蓋以下三種場景之一：
        【適合投資】、【不適合投資】或【策略性等待】。

        📋 回覆格式規範：
        請使用 Markdown 格式輸出，標題為：📈 [股票代號/名稱] 全方位分析報告。

        p.s 拒絕機制：如果輸入的代號不是台股，請溫柔地提醒使用者只支援台股查詢。
        """

        # 4. 呼叫 Groq API (整合 Llama 3.1 模型)
        url_groq = "https://api.groq.com/openai/v1/chat/completions"
        headers_groq = {
            "Authorization": f"Bearer {GROQ_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"分析台股 {stock_id}，目前股價約 {price:.2f} 元。請開始執行三步驟全方位分析。"}
            ],
            "temperature": 0.3 # 較低的溫度確保分析報告更具專業穩定性
        }

        print("[AI] 正在向 Groq 發送請求 (Agent 模式)...")
        resp_groq = requests.post(url_groq, headers=headers_groq, json=payload, timeout=20)
        
        if resp_groq.status_code == 200:
            ai_content = resp_groq.json()['choices'][0]['message']['content']
            print("[AI] 分析報告生成成功")
            return ai_content
        else:
            print(f"❌ Groq 報錯: {resp_groq.text}")
            return f"❌ AI 分析暫時無法執行 (代碼 {resp_groq.status_code})"

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 發生異常: {error_msg}")
        if "Too Many Requests" in error_msg:
            return "⚠️ 資料抓取過於頻繁，請 5 分鐘後再試。"
        return f"❌ 系統發生預期外錯誤，請稍後再試。"

if __name__ == "__main__":
    # 本地測試範例
    print(get_ai_analysis("2330"))