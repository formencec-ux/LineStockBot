import requests
import os

# 從系統環境變數中讀取 Groq 的 API Key
GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(user_query):
    """
    user_query 可能是一個代號（如 2330）或是一個問題（如 2330 股價如何）
    """
    print(f"\n[AI] 啟動智慧分析流程，用戶輸入: {user_query}")
    
    try:
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到 GROQ_KEY。"

        # 1. 從用戶輸入中提取 4 位數代號 (例如從 '2330股價' 提取出 '2330')
        import re
        stock_match = re.search(r'\d{4}', user_query)
        if not stock_match:
            return "💡 請輸入 4 位數台股代號（例如：2330），我將為您進行分析。"
        
        stock_id = stock_match.group()
        ticker_id = f"{stock_id}.TW"

        # 2. 抓取 Yahoo Finance 數據 (含名稱定錨)
        url_yahoo = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_id}"
        headers_yahoo = {"User-Agent": "Mozilla/5.0"} 
        resp_yahoo = requests.get(url_yahoo, headers=headers_yahoo, timeout=10)
        
        if resp_yahoo.status_code == 200:
            data = resp_yahoo.json()
            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 0)
            # 獲取正確的公司名稱 (定錨關鍵)
            stock_name = meta.get('shortName') or meta.get('symbol') or stock_id
            stock_name = stock_name.replace(".TW", "")
        else:
            return f"⚠️ 找不到代號 {stock_id} 的資料，請確認輸入是否正確。"

        # 3. 定義具備「思考與篩選」能力的 AI Agent 提示詞
        system_prompt = f"""
        角色：你是一位精通全球資本市場的「資深投資分析助理」。
        當前分析對象：台股代號 [{stock_id}]，公司名稱為 [{stock_name}]。

        🛠 任務邏輯：
        請根據使用者的問題內容，決定回應的深度：
        1. 如果使用者只問「股價」、「多少錢」，請只提供【財務看板】中的股價與本益比資訊。
        2. 如果使用者只問「新聞」、「發生什麼事」，請只提供【市場焦點新聞】。
        3. 如果使用者只問「籌碼」、「買賣超」，請針對籌碼面或法人與外資買賣狀況進行深入分析。
        4. 如果使用者只輸入「代號」或問「評價如何」，請提供「三步驟全方位報告」。

        📋 回覆規範：
        - 標題一律使用：📈 [{stock_id} {stock_name}] 分析報告
        - 使用 Markdown 格式。
        - 嚴禁將 {stock_id} 誤判為台積電或其他公司。
        - 內容要冷靜、客觀且具備洞察力。
        """

        # 4. 呼叫 Groq API
        url_groq = "https://api.groq.com/openai/v1/chat/completions"
        headers_groq = {
            "Authorization": f"Bearer {GROQ_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": f"使用者問題：『{user_query}』。目前該股最新股價為 {price:.2f} 元。請根據問題提供精準解答。"
                }
            ],
            "temperature": 0.2
        }

        resp_groq = requests.post(url_groq, headers=headers_groq, json=payload, timeout=20)
        
        if resp_groq.status_code == 200:
            return resp_groq.json()['choices'][0]['message']['content']
        else:
            return "❌ AI 思考中斷，請稍後再試。"

    except Exception as e:
        print(f"❌ 異常: {e}")
        return "❌ 系統暫時無法處理您的請求。"