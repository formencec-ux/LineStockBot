import requests
import os
import re
import db_helper

GROQ_KEY = os.environ.get("GROQ_KEY")

try:
    db_helper.init_db()
except Exception as db_err:
    print(f"[DB] 自動初始化提示: {db_err}")

def get_ai_analysis(user_input, user_id="default"):
    """
    優化版：精確鎖定單純代號意圖，放寬知識庫限制以利產出 1~8 點大報告
    """
    print(f"\n[AI] 啟動智慧助理流程，用戶輸入: {user_input}")
    
    try:
        if not GROQ_KEY:
            return "❌ 系統錯誤：找不到系統中的 GROQ_KEY。"

        # 1. 代號提取
        match = re.search(r'(\d{4})', user_input)
        if not match:
            return "💡 您好！我是您的 AI 股市助理。請在您的訊息中輸入 4 位數台股代號（例如：2330 多少錢），我隨時為您分析！"
        
        stock_id = match.group(1)
        ticker_id = f"{stock_id}.TW"

        # 檢查用戶是否「只傳了代號」（把 4 位數數字拔掉後，如果只剩空白或長度小於 3，視為純代號指令）
        clean_input = user_input.replace(stock_id, "").strip()
        is_pure_id = len(clean_input) == 0  # True 代表使用者真的只打數字代號
        print(f"[意圖偵測] 是否為純代號查詢: {is_pure_id}")

        # 2. 數據抓取
        url_yahoo = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_id}"
        headers_yahoo = {"User-Agent": "Mozilla/5.0"} 
        resp_yahoo = requests.get(url_yahoo, headers=headers_yahoo, timeout=10)
        
        price = 0
        stock_name = stock_id
        
        if resp_yahoo.status_code == 200:
            data = resp_yahoo.json()
            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 0)
            
            raw_name = meta.get('shortName') or meta.get('longName') or stock_id
            stock_name = raw_name.replace(".TW", "").strip()
        else:
            return f"⚠️ 報告主人，目前在市場上查不到代號 {stock_id} 的即時數據，要不要確認一下代號呢？"

        # 3. 歷史數據累積
        last_price = db_helper.get_last_price(stock_id)
        db_helper.record_price(stock_id, stock_name, price)

        history_context = ""
        if last_price:
            diff = price - last_price
            if diff > 0:
                history_context = f"（系統歷史追蹤提示：該用戶上一次查詢此股時價格為 {last_price:.2f} 元，目前股價相比上一次『上漲』了 {abs(diff):.2f} 元）"
            elif diff < 0:
                history_context = f"（系統歷史追蹤提示：該用戶上一次查詢此股時價格為 {last_price:.2f} 元，目前股價相比上一次『下跌』了 {abs(diff):.2f} 元）"
            else:
                history_context = f"（系統歷史追蹤提示：目前股價與上一次查詢時完全相同，價格持平穩定）"
        else:
            history_context = "（系統歷史追蹤提示：這是該用戶第一次在本系統查詢此股票，暫無歷史對比數據）"

        # 4. Prompt 調整
        system_prompt = f"""
        角色設定：你是一位親切、專業且非常有耐心的「私人 AI 資深股票研究分析師」。請一律使用繁體中文回答。
        
        【重要修正任務】：
        目前系統傳入的股票簡稱為 [{stock_name}]。如果這個名稱是英文（例如 KINSUS...），請利用你大模型的內部知識庫，自動將其翻譯轉換為台灣市場熟知的「繁體中文公司名稱」（例如：3189請務必稱呼為『景碩』、4958稱呼為『臻鼎』、2330為『台積電』）。在回答中絕對不要使用一整串英文名稱來稱呼公司！
        
        【當前服務對象】：台股代號 [{stock_id}]。
        【系統資料庫追蹤到的歷史變動】：{history_context}

        🛠 任務規則：
        強制的動態模式切換：
        - 如果【目前模式】為「簡短問答」：請嚴格遵循「沒問到的部分絕對不要主動顯示」，隱藏尚未公開等無用欄位。
        - 如果【目前模式】為「深度完整報告」：請【完全釋放你的知識庫】，針對該公司進行全方位的推估與分析，必須完整包含 1 至 8 點的架構，不需隱藏！

        📋 各意圖執行細則：
        1. 如果用戶問「股價」、「價格」、「多少錢」，切換為【簡短問答】，請【只回覆】最新股價與歷史變動對比。
        2. 如果用戶問「新聞」、「發生什麼事」，切換為【簡短問答】，請【只回覆】近期新聞摘要與潛在影響。
        3. 如果用戶問「籌碼」、「法人」、「大戶」，切換為【簡短問答】，請【只回覆】籌碼面分析。
        4. 如果用戶問「值不值得投資」、「建議投資嗎」，切換為【簡短問答】，請分析該公司最近的發展並明確回答【是】或【否】。
        5. 只有在用戶「只傳單純代號」時，強制切換為【深度完整報告】，請務必完整產出以下 1~8 點內容（允許根據你的知識庫進行深度合理推估，不可留白）：
           【執行摘要：
           1. 簡要概述公司的業務、整體投資論點（買入/持有/賣出評級）、主要催化劑與風險。
           2. 財務表現與健康狀況：分析收入增長、毛利率趨勢；評估債務水平與資產負債表強弱；分析自由現金流量(FCF)。
           3. 估值：對比自身5年歷史與行業平均之市盈率/市淨率，並對比前3名直接競爭對手，得出高估或低估結論。
           4. 商業模式與競爭護城河：描述核心業務部門貢獻度，並分析競爭優勢來源（品牌/專利/技術）與強度。
           5. 增長策略與未來展望：確定未來增長催化劑與總體潛在市場(TAM)份額。
           6. 管理與治理：概述領導團隊、資本配置政策（股息/回購）與內部人持股。
           7. 風險分析：列舉前3大特殊風險（如產品/關鍵人物）與前3大系統性風險（如經濟衰退/監管）。
           8. 最終建議：綜合以上要點，給出最終買入/持有/賣出評級與精煉理由。】

        - 【助理式引導結尾】：不論哪種模式，在回覆的最後一行，必須加上一句親切的主動引導問句。
        """

        # 根據我們前面偵測的結果，在 user 訊息中對 AI 下死命令，強迫它切換模式
        mode_instruction = "【當前模式：深度完整報告】。用戶僅發送了純代號，請立即針對該公司啟動 1~8 點的完整研究報告框架，火力全開進行深度分析。" if is_pure_id else "【當前模式：簡短問答】。請針對用戶的問題精確且簡短回答，沒問到的欄位絕對不要多嘴顯示。"

        url_groq = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"系統指令：{mode_instruction}\n\n用戶問：『{user_input}』。目前的即時股價為 {price:.2f} 元。請依私人資深分析師身份，為我進行精確的繁體中文解答。"}
            ],
            "temperature": 0.2 # 稍微調高到 0.2，讓 AI 在產出 1~8 點大報告時有足夠的文字發揮力
        }

        resp_groq = requests.post(url_groq, headers={"Authorization": f"Bearer {GROQ_KEY.strip()}", "Content-Type": "application/json"}, json=payload, timeout=20)
        
        if resp_groq.status_code == 200:
            ai_reply = resp_groq.json()['choices'][0]['message']['content']
            db_helper.save_chat_log(user_id, user_input, ai_reply)
            return ai_reply
        else:
            return f"❌ 報告主人，AI 助理在思考時遇到了點小麻煩，請稍後再試試看。"

    except Exception as e:
        return f"❌ 報告主人，系統發生異常！\n詳細原因：{str(e)}"