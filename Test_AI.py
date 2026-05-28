import requests
import os
import re
import db_helper  # 引入我們在第一步寫好的資料庫助手

# 從 Render 的系統環境變數中讀取 Groq API 金鑰
GROQ_KEY = os.environ.get("GROQ_KEY")

def get_ai_analysis(user_input):
    """
    輸入使用者發送的訊息（包含自然語言），偵測代號、儲存數據，並以助理口吻回覆
    """
    print(f"\n[AI] 啟動智慧助理流程，用戶輸入: {user_input}")
    
    try:
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到系統中的 GROQ_KEY。"

        # --- 1. 自然語言解析：用正則表達式(Regex)抓取 4 位數代號 ---
        match = re.search(r'(\d{4})', user_input)
        if not match:
            return "💡 您好！我是您的 AI 股市助理。請在您的訊息中輸入 4 位數台股代號與問題（例如：2330 多少錢），我隨時為您分析！"
        
        stock_id = match.group(1)
        ticker_id = f"{stock_id}.TW"

        # --- 2. 數據抓取與中文名稱精確定位 (防止台積電幻覺) ---
        url_yahoo = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_id}"
        headers_yahoo = {"User-Agent": "Mozilla/5.0"} 
        resp_yahoo = requests.get(url_yahoo, headers=headers_yahoo, timeout=10)
        
        price = 0
        stock_name = stock_id  # 如果 Yahoo 沒抓到，預設用代號代替
        
        if resp_yahoo.status_code == 200:
            data = resp_yahoo.json()
            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 0)
            
            # 從 Yahoo 抓取正確的公司簡稱（如 ZHEN DING），若沒抓到則用代號
            raw_name = meta.get('shortName') or meta.get('longName') or stock_id
            stock_name = raw_name.replace(".TW", "").strip()
        else:
            return f"⚠️ 報告主人，目前在市場上查不到代號 {stock_id} 的即時數據，要不要確認一下代號呢？"

        # --- 3. 【任務 2 實作】歷史數據累積與自動對比 ---
        # A. 撈出上一次的價格
        last_price = db_helper.get_last_price(stock_id)
        
        # B. 將這一次的價格「累積存入」資料庫
        db_helper.record_price(stock_id, stock_name, price)
        print(f"[DB] 已將 {stock_name}({stock_id}) 股價 {price} 寫入歷史累積資料表")

        # C. 根據有沒有歷史資料，自動生成一段對話背景交給 AI
        history_context = ""
        if last_price:
            diff = price - last_price
            if diff > 0:
                history_context = f"（系統歷史追蹤提示：該用戶上一次查詢此股時價格為 {last_price:.2f} 元，目前股價相比上一次『上漲』了 {abs(diff):.2f} 元）"
            elif diff < 0:
                history_context = f"（系統歷史追蹤提示：該用戶上一次查詢此股時價格為 {last_price:.2f} 元，目前股價相比上一次『下跌』了 {abs(diff):.2f} 元）"
            else:
                history_context = f"（系統歷史追蹤提示：該用戶上一次查詢此股時價格為 {last_price:.2f} 元，目前股價持平）"
        else:
            history_context = "（系統歷史追蹤提示：這是該用戶第一次在本系統查詢此股票，暫無歷史對比數據）"

        # --- 4. 【任務 1 實作】AI Agent 提示詞深度調整 (變身對話助理) ---
        system_prompt = f"""
        角色設定：你是一位親切、專業且非常有耐心的「私人 AI 投資助理」。請一律使用繁體中文回答，語氣要親切貼心，多使用「您」、「好的」、「報告」等詞彙，要把自己定位成理財秘書，而非冰冷的表格。
        
        【當前服務對象】：台股代號 [{stock_id}]，中文名稱為 [{stock_name}]。
        【系統資料庫追蹤到的歷史變動】：{history_context}

        🛠 任務規則（沒問到的部分絕對不要主動顯示）：
        1. 精準對話過濾：
           - 如果用戶問「股價」、「價格」、「多少錢」之類的話語，請【只回覆】最新股價，並主動結合【系統資料庫追蹤到的歷史變動】告訴用戶跟上次比是漲還是跌。
           - 如果用戶問「新聞」、「發生什麼事」之類的話語，請【只回覆】近期新聞摘要與潛在影響。
           - 如果用戶問「籌碼」、「法人」、「大戶」之類的話語，請【只回覆】籌碼面分析。
           - 如果用戶問「值不值得投資」、「建議投資嗎」之類的話語，請分析整支股票最近的新聞與未來訂單，並進行籌碼面分析，並回答【是】或【否】值得投資，並告知原因。
           - 只有在用戶只傳單純「代號」或問「綜合評價」時，才提供完整的三步驟報告。

        2. 廢話清理原則：
           - 禁止顯示「尚未公開」、「暫無資料」等無用欄位。如果數據不足，直接在回覆中隱藏該欄位。
           - 嚴禁提到台積電（除非代號真的是 2330）。
           - 【助理式引導結尾】：不論用戶問什麼，在回覆的最後一行，必須加上一句親切的主動引導問句。
             例如：「以上是為您整理的即時股價，需要進一步幫您追蹤它的最新焦點新聞嗎？」
        """

        # --- 5. 呼叫 Groq API ---
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
                    "content": f"用戶問：『{user_input}』。目前的即時股價為 {price:.2f} 元。請依私人助理身份，精確且溫柔地為我解答。"
                }
            ],
            "temperature": 0.1  # 調到最低，確保 AI 乖乖遵守任務規則，沒問到的絕不多嘴
        }

        print(f"[AI] 正在向 Groq 請求助理式對話內容...")
        resp_groq = requests.post(url_groq, headers=headers_groq, json=payload, timeout=20)
        
        if resp_groq.status_code == 200:
            return resp_groq.json()['choices'][0]['message']['content']
        else:
            return f"❌ 報告主人，AI 助理在思考時遇到了點小麻煩 (錯誤碼 {resp_groq.status_code})，請稍後再試試看。"

    except Exception as e:
        print(f"❌ 發生異常: {str(e)}")
        return "❌ 報告主人，系統連線失敗，請檢查網路或稍後再試。"