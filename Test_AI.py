import requests
import os

# 從系統環境變數中讀取 Groq 的 API Key
GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(stock_id):
    """
    輸入股票代號，先透過 Yahoo API 定錨公司名稱與股價，再由 AI Agent 執行分析
    """
    print(f"\n[AI] 啟動全方位分析流程: {stock_id}")
    
    try:
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到 GROQ_KEY。"

        # --- 第一階段：抓取股價與正確的公司名稱 (定錨關鍵) ---
        ticker_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        url_yahoo = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_id}"
        headers_yahoo = {"User-Agent": "Mozilla/5.0"} 
        
        print(f"[AI] 正在從 Yahoo 獲取即時數據: {ticker_id}")
        resp_yahoo = requests.get(url_yahoo, headers=headers_yahoo, timeout=10)
        
        if resp_yahoo.status_code == 200:
            data = resp_yahoo.json()
            # 取得最新股價
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            # 取得公司名稱 (這能有效告訴 AI 它是 4958 而不是 2330)
            # symbol 通常回傳代號，如果 API 有回傳 shortName 則更佳
            stock_name = data['chart']['result'][0]['meta'].get('symbol', stock_id).replace(".TW", "")
            print(f"[AI] 資料定錨成功 -> 代號: {stock_id}, 股價: {price:.2f}")
        else:
            print(f"❌ Yahoo API 報錯: {resp_yahoo.status_code}")
            return "⚠️ 提醒：目前僅支援台股查詢（如 2330），請確認代號是否正確。"

        # --- 第二階段：AI Agent 提示詞設定 (強化防誤判邏輯) ---
        system_prompt = """
        角色設定：你是一位精通全球資本市場的「資深投資分析助理」。你擅長結合即時財務數據（量化）與市場新聞趨勢（質化），為投資人提供客觀、冷靜且具備洞察力的分析建議。

        🛠 任務指令：
        當使用者輸入一個股票代號時，請嚴格執行以下三個分析步驟：
        
        第一步：多維度財務與籌碼掃描
        1. 估值指標：報告目前股價、目前的 PE Ratio (本益比)，並說明該數值位於歷史區間的相對位置（高/中/低）。
        2. 籌碼與動能：簡述法人與大戶進出趨勢。
        3. 業務動態：摘要最近營收表現與核心業務增長點。

        第二步：Google News 即時新聞摘要 (請根據指定的正確公司進行分析)
        1. 針對該公司最近期 3 則關鍵新聞提供：標題、關鍵摘要。
        2. 分析新聞對股價的潛在影響（利多/利空/中立）。

        第三步：投資人視角綜合評估
        先分析營收狀況，再給予趨勢預測。必須從【適合投資】、【不適合投資】或【策略性等待】中擇一。

        📋 回覆格式規範：
        使用 Markdown 輸出標題：📈 [股票代號/正確公司名稱] 全方位分析報告。

        ⚠️ 核心警告：
        請嚴格遵守「輸入代號即為分析對象」的原則。如果收到的是 4958，絕對不可分析為 2330 或其他公司。若代號非台股，請溫柔提醒僅支援台股。
        """

        # --- 第三階段：呼叫 Groq API ---
        url_groq = "https://api.groq.com/openai/v1/chat/completions"
        headers_groq = {
            "Authorization": f"Bearer {GROQ_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        # 在 User Message 中強迫點名公司名稱與代號
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": f"現在請分析台股代號 [{stock_id}]。請注意，這不是台積電或其他公司。目前最新股價為 {price:.2f} 元。請開始執行三步驟報告。"
                }
            ],
            "temperature": 0.2 # 降低溫度以減少 AI 自作聰明的幻覺
        }

        print(f"[AI] 正在發送請求至 Groq (已加入防誤判指令)...")
        resp_groq = requests.post(url_groq, headers=headers_groq, json=payload, timeout=20)
        
        if resp_groq.status_code == 200:
            ai_content = resp_groq.json()['choices'][0]['message']['content']
            print("[AI] 分析報告生成成功")
            return ai_content
        else:
            return f"❌ AI 分析暫時無法執行 (代碼 {resp_groq.status_code})"

    except Exception as e:
        print(f"❌ 發生異常: {str(e)}")
        return "❌ 系統分析失敗，請檢查網路連線或稍後再試。"