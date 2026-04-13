import requests
import os
import re

# 從系統環境變數中讀取 Groq 的 API Key
GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(user_input):
    """
    輸入使用者的一句話，自動偵測代號並根據問題內容精簡回答。
    優化重點：強制意圖過濾、隱藏無用欄位、中文定錨。
    """
    print(f"\n[AI] 收到用戶請求: {user_input}")
    
    try:
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到 GROQ_KEY。"

        # --- 1. 代號提取 (Regex) ---
        match = re.search(r'(\d{4})', user_input)
        if not match:
            return "💡 請提供 4 位數台股代號（例如：2330），並告訴我想查詢什麼。"
        
        stock_id = match.group(1)
        ticker_id = f"{stock_id}.TW"

        # --- 2. 抓取 Yahoo 數據與中文名稱 ---
        url_yahoo = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_id}"
        headers_yahoo = {"User-Agent": "Mozilla/5.0"} 
        resp_yahoo = requests.get(url_yahoo, headers=headers_yahoo, timeout=10)
        
        price = 0
        stock_name = stock_id # 預設值
        
        if resp_yahoo.status_code == 200:
            data = resp_yahoo.json()
            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 0)
            
            # 取得公司名稱
            raw_name = meta.get('shortName') or meta.get('longName') or stock_id
            stock_name = raw_name.replace(".TW", "").strip()
        else:
            return f"⚠️ 找不到代號 {stock_id} 的即時資料，請確認輸入是否正確。"

        # --- 3. 強化版 AI 提示詞 (防廢話、防誤判) ---
        system_prompt = f"""
        角色設定：你是一位精通台股的「資深投資分析助理」。
        當前分析對象：台股代號 [{stock_id}]，中文名稱為 [{stock_name}]。

        🛠 嚴格任務規則：
        1. 意圖判定優先：
           - 如果用戶問「股價」、「價格」、「多少錢」之類的，請【只回覆】關於最新股價數據。
           - 如果用戶問「新聞」、「發生什麼事」，請搜尋近期新聞【只回覆】近期1-2則新聞摘要。
           - 如果用戶問「籌碼」、「法人」、「大戶」、「買賣超」，請【只回覆】籌碼面分析與買超賣超相關。
           - 如果用戶問「未來展望」、「長期方向」、「是否適合投資」，請就新聞內容與所有該股票相關資料做分析【只回覆】未來是否值得買進，並且以三種方式回答1.(適合買進)因為______2.(不適合買進)因為______3.(暫不適合買進)因為______如果______才買進。
           - 只有在用戶只傳「代號」或問「評價」時，才提供完整四步驟報告。

        2. 廢話清理原則：
           - 禁止顯示「尚未公開」、「暫無資料」等欄位。如果數據不足，直接隱藏該部分。
           - 嚴禁提到台積電（除非代號真的是 2330）。

        📋 回覆規範：
        - 標題格式：📈 [{stock_id} {stock_name}]
        - 使用 Markdown。精簡為上，沒問到的部分絕對不要顯示。
        """

        # --- 4. 呼叫 Groq API (調低溫度) ---
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
                    "content": f"用戶的問題是：『{user_input}』。目前的即時股價為 {price:.2f} 元。請根據指令精確且簡短地回答。"
                }
            ],
            "temperature": 0.1 # 將溫度降到最低，確保 AI 乖乖聽話，不亂加格式
        }

        resp_groq = requests.post(url_groq, headers=headers_groq, json=payload, timeout=20)
        
        if resp_groq.status_code == 200:
            return resp_groq.json()['choices'][0]['message']['content']
        else:
            return f"❌ AI 分析暫時無法執行 (錯誤代碼 {resp_groq.status_code})"

    except Exception as e:
        print(f"❌ 發生異常: {str(e)}")
        return "❌ 系統分析失敗，請檢查網路連線或稍後再試。"