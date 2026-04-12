import requests
import os
import re  # 新增：用於解析自然語言中的代號

# 從系統環境變數中讀取 Groq 的 API Key
GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(user_input):
    """
    輸入使用者的一句話，自動偵測代號並根據問題內容精簡回答
    """
    print(f"\n[AI] 收到用戶請求: {user_input}")
    
    try:
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到 GROQ_KEY。"

        # --- 第一階段：自然語言解析 (Regex) ---
        # 尋找訊息中是否有 4 位數字的台股代號
        match = re.search(r'\d{4}', user_input)
        if not match:
            return "💡 請提供 4 位數台股代號（例如：2330），並告訴我想查詢什麼。"
        
        stock_id = match.group()
        ticker_id = f"{stock_id}.TW"

        # --- 第二階段：抓取數據與中文名稱定位 ---
        url_yahoo = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_id}"
        headers_yahoo = {"User-Agent": "Mozilla/5.0"} 
        resp_yahoo = requests.get(url_yahoo, headers=headers_yahoo, timeout=10)
        
        if resp_yahoo.status_code == 200:
            data = resp_yahoo.json()
            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice')
            
            # 嘗試抓取公司名稱，如果 Yahoo 回傳英文，我們在下一階段強迫 AI 轉中文
            raw_name = meta.get('shortName') or meta.get('symbol') or stock_id
            stock_name = raw_name.replace(".TW", "").strip()
            print(f"[AI] 定錨成功 -> 代號: {stock_id}, 股價: {price:.2f}")
        else:
            return f"⚠️ 找不到代號 {stock_id} 的即時資料，請確認輸入是否正確。"

        # --- 第三階段：AI Agent 提示詞設定 (具備思考與過濾功能) ---
        system_prompt = f"""
        角色設定：你是一位精通全球資本市場的「資深投資分析助理」。
        當前分析對象：台股代號 [{stock_id}]，請務必使用中文名稱（例如：臻鼎、台積電）進行回覆。

        🛠 任務規則：
        請根據使用者的問題內容，決定回覆的範圍：
        1. 如果使用者只問「股價」、「多少錢」、「本益比」，請只回覆【第一步：財務看板】。
        2. 如果使用者只問「新聞」、「發生什麼事」，請只回覆【第二步：市場焦點新聞】。
        3. 如果使用者只問「籌碼」、「法人」，請只回覆【第一步】中的籌碼部分。
        4. 如果使用者只輸入「代號」或問「評價如何」，請提供完整的三步驟報告。

        📋 回覆格式規範：
        - 標題：📈 [{stock_id} / 中文公司名稱] 分析報告
        - 使用 Markdown 格式。
        - 嚴禁誤判為台積電。如果代號是 4958，分析對象就是臻鼎。
        """

        # --- 第四階段：呼叫 Groq API ---
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
                    "content": f"使用者問題：『{user_input}』。目前該股最新股價為 {price:.2f} 元。請根據指令精確回答。"
                }
            ],
            "temperature": 0.2
        }

        print(f"[AI] 正在分析問題意圖...")
        resp_groq = requests.post(url_groq, headers=headers_groq, json=payload, timeout=20)
        
        if resp_groq.status_code == 200:
            return resp_groq.json()['choices'][0]['message']['content']
        else:
            return "❌ AI 目前無法回應，請稍後再試。"

    except Exception as e:
        print(f"❌ 發生異常: {str(e)}")
        return "❌ 系統分析失敗，請檢查網路連線或稍後再試。"