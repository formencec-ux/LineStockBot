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
    更新版：強制將英文名稱轉為中文、修正漲跌為0的說法
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
                # 修正問題：如果 diff == 0，主動給出溫和的持平提示，避免 AI 寫出「漲了 0」
                history_context = f"（系統歷史追蹤提示：目前股價與上一次查詢時完全相同，價格持平穩定）"
        else:
            history_context = "（系統歷史追蹤提示：這是該用戶第一次在本系統查詢此股票，暫無歷史對比數據）"

        # 4. Prompt 調整（優化一：強制翻譯中文名稱）
        system_prompt = f"""
        角色設定：你是一位親切、專業且非常有耐心的「私人 AI 資深股票研究分析師」。請一律使用繁體中文回答。
        
        【重要修正任務】：
        目前系統傳入的股票簡稱為 [{stock_name}]。如果這個名稱是英文（例如 KINSUS...），請利用你大模型的內部知識庫，自動將其翻譯轉換為台灣市場熟知的「繁體中文公司名稱」（例如：3189請務必稱呼為『景碩』、4958稱呼為『臻鼎』、2330為『台積電』）。在回答中絕對不要使用一整串英文名稱來稱呼公司！
        
        【當前服務對象】：台股代號 [{stock_id}]。
        【系統資料庫追蹤到的歷史變動】：{history_context}

        🛠 任務規則：
        1. 精準對話過濾：
           - 如果用戶問「股價」、「價格」、「多少錢」之類的話語，請【只回覆】最新股價，並主動結合【系統資料庫追蹤到的歷史變動】告訴用戶跟上次比是漲還是跌。
           - 如果用戶問「新聞」、「發生什麼事」之類的話語，請【只回覆】近期新聞摘要與潛在影響。
           - 如果用戶問「籌碼」、「法人」、「大戶」之類的話語，請【只回覆】籌碼面分析。
           - 如果用戶問「值不值得投資」、「建議投資嗎」之類的話語，請分析整支股票最近的新聞與未來訂單，並進行籌碼面分析，並回答【是】或【否】值得投資，並告知原因。
           - 只有在用戶只傳單純「代號」時，執行以下內容【執行摘要：
           1.簡要概述公司的業務
           用 2-3 句話陳述您的整體投資論點。 以目前的估值來看，是買入、持有還是賣出？
           總結主要的積極催化劑和主要風險。
           2. 財務表現與健康狀況：
           損益表分析：分析過去 5 年 + TTM 的收入增長、毛利率、營業利潤率和淨利潤率趨勢。
           資產負債表分析：評估公司的債務水平、債務權益比率、流動比率和現金狀況。 資產負債表是強勁還是疲軟？
           現金流量分析：分析經營現金流量、資本支出和自由現金流量 (FCF) 的產生。 該公司是否持續 FCF 為正？
           3. 估值：
           倍數分析：將公司的當前市盈率、市銷率、市淨率和企業價值/EBITDA 比率與以下內容進行比較：
           其自身的 5 年歷史平均值&行業平均值。其前 3 名直接競爭對手：[Competitor A]、[Competitor B] 和 [Competitor C]。
           結論：基於此分析，得出股票是高估、低估還是合理定價的結論。
           4. 商業模式與競爭護城河：
           業務部門：簡要描述公司的核心業務部門及其對收入的貢獻。
           經濟護城河：確定並解釋其競爭優勢的來源（例如，品牌、專利、網絡效應、成本領先地位）。 評估這條護城河的耐用性和強度。
           5. 增長策略與未來展望：增長動力：確定預計將推動未來增長的主要催化劑（例如，新產品、市場擴張、行業趨勢）。
           市場機會：分析總體潛在市場 (TAM) 以及公司佔據更大市場份額的潛力。
           6. 管理與治理：
           領導力：簡要概述首席執行官和高級管理團隊。 評論他們的任期和業績記錄。
           資本配置：評估管理層在配置資本方面的有效性。 審查他們關於股息、股票回購和併購活動的政策。
           內部人持股：注意內部人持股的水平。
           7. 風險分析：
           特殊風險：公司特有的前 3 大風險是什麼（例如，產品故障、關鍵人物風險、訴訟）？
           系統性風險：前 3 大外部風險是什麼（例如，經濟衰退、監管變化、競爭性破壞）？
           8. 最終建議：
           將以上所有要點綜合成最終的投資結論。 重申您的買入/持有/賣出評級，並根據當前價格的機會和風險的平衡，給出簡潔的理由。】
     
       2. 規範：
           - 隱藏「尚未公開」等無用欄位。
           - 【助理式引導結尾】：在回覆的最後一行，必須加上一句親切的主動引導問句。
        """

        url_groq = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"用戶問：『{user_input}』。目前的即時股價為 {price:.2f} 元。請依私人助理身份精確且溫柔地為我解答。"}
            ],
            "temperature": 0.1
        }

        resp_groq = requests.post(url_groq, headers={"Authorization": f"Bearer {GROQ_KEY.strip()}", "Content-Type": "application/json"}, json=payload, timeout=20)
        
        if resp_groq.status_code == 200:
            ai_reply = resp_groq.json()['choices'][0]['message']['content']
            # --- 新增：將成功的對話紀錄存入資料庫，供下一輪對話當記憶 ---
            db_helper.save_chat_log(user_id, user_input, ai_reply)
            return ai_reply
        else:
            return f"❌ 報告主人，AI 助理在思考時遇到了點小麻煩，請稍後再試試看。"

    except Exception as e:
        return f"❌ 報告主人，系統發生異常！\n詳細原因：{str(e)}"