import requests
import os
import re

GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(user_input):
    """
    輸入使用者的一句話，偵測 4 位數代號，並根據問題內容精簡回答
    """
    print(f"\n[AI] 收到用戶請求: {user_input}")
    
    try:
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到 GROQ_KEY。"

        # --- 1. 強化代號提取 ---
        # 尋找訊息中是否存在連續 4 位數字
        match = re.search(r'(\d{4})', user_input)
        if not match:
            # 如果使用者只輸入「台積電」而沒代號，這裡會提醒
            return "💡 請提供 4 位數台股代號（例如：2330），並告訴我想查詢什麼。"
        
        stock_id = match.group(1)
        ticker_id = f"{stock_id}.TW"

        # --- 2. 抓取 Yahoo 數據與「正確中文名稱」 ---
        url_yahoo = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_id}"
        headers_yahoo = {"User-Agent": "Mozilla/5.0"} 
        resp_yahoo = requests.get(url_yahoo, headers=headers_yahoo, timeout=10)
        
        stock_name = ""
        price = 0
        
        if resp_yahoo.status_code == 200:
            data = resp_yahoo.json()
            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 0)
            
            # 優先嘗試從 Yahoo 抓取名稱，抓不到就用代號
            raw_name = meta.get('shortName') or meta.get('longName') or stock_id
            stock_name = raw_name.replace(".TW", "").strip()
        else:
            return f"⚠️ 找不到代號 {stock_id} 的即時資料，請確認輸入是否正確。"

        # --- 3. 定義智慧過濾提示詞 ---
        system_prompt = f"""
        你是一位精通台股與全球資本市場的「資深投資分析助理」。
        【目前分析對象】：代號 {stock_id}，請務必使用對應的「中文公司名稱」（如：臻鼎、台積電）來稱呼。
        
        【任務規則】：
        根據使用者的問題，決定回覆內容：
        1. 問「股價」、「多少錢」：只提供【第一步：財務看板】。
        2. 問「新聞」、「發生什麼事」：只提供【第二步：市場焦點新聞】。
        3. 問「籌碼」、「大戶」：只提供【第一步】中的籌碼與法人概況。
        4. 只輸入「代號」或問「評價」：提供完整三步驟報告。

        【格式規範】：
        - 標題：📈 [{stock_id} / 中文名稱] 分析報告
        - 使用 Markdown，禁止張冠李戴（4958 是臻鼎，2330 是台積電）。
        """

        # --- 4. 呼叫 Groq API ---
        url_groq = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": f"用戶問：『{user_input}』。目前該股最新價 {price:.2f}。請以此代號與公司為唯一對象作答。"
                }
            ],
            "temperature": 0.2
        }

        resp_groq = requests.post(
            url_groq, 
            headers={"Authorization": f"Bearer {GROQ_KEY.strip()}", "Content-Type": "application/json"}, 
            json=payload, 
            timeout=20
        )
        
        if resp_groq.status_code == 200:
            return resp_groq.json()['choices'][0]['message']['content']
        return "❌ AI 思考中斷，請稍後再試。"

    except Exception as e:
        print(f"❌ 異常: {e}")
        return "❌ 系統分析失敗，請檢查網路或稍後再試。"