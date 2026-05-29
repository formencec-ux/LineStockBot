import os
import time
import threading  # 用於異步處理，避免 Line 逾時
import re         # 用於提取文字中的股票代號
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from Test_AI import get_ai_analysis 

app = Flask(__name__)

# 讀取系統環境變數金鑰
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 狀態記錄
user_last_request_time = {}
processed_msg_ids = set() 

# =========================================================
# ✨ 任務修改：將提問冷卻時間縮短為 30 秒
# =========================================================
COOL_DOWN_TIME = 30  
# =========================================================

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg_id = event.message.id
    user_id = event.source.user_id
    user_msg = event.message.text.strip()
    
    print(f"\n[LINE] 收到訊息: {user_msg} (ID: {msg_id})")

    # 1. 防止重複請求
    if msg_id in processed_msg_ids:
        return
    processed_msg_ids.add(msg_id)

    # 2. 測試指令
    if user_msg == "測試":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 伺服器運作中！"))
        return

    # 3. 檢查訊息中是否有現成的 4 位數股票代號
    stock_match = re.search(r'\d{4}', user_msg)
    
    # 【對話接力功能】如果用戶只回覆肯定的引導詞，表示要沿用上一輪的股票代號
    lead_words = ["好", "要", "想看", "新聞", "好的", "可以", "繼續", "分析"]
    is_lead_word = any(word in user_msg for word in lead_words)
    
    final_query_msg = user_msg  # 最後要丟給 AI 的字串
    
    # 如果使用者沒輸入數字，但是講了「好啊」之類的引導詞
    if not stock_match and is_lead_word:
        import db_helper
        # 去資料庫撈出這個人最近 5 次對話中最後問的是哪一檔
        remembered_id = db_helper.get_user_last_stock(user_id)
        if remembered_id:
            # 自動把代號補在前面，變成（例如：「3189 好啊」）
            final_query_msg = f"{remembered_id} {user_msg}"
            # 重新建立 stock_match，這樣就能順利通過下方的股票檢查
            stock_match = re.search(r'\d{4}', final_query_msg)
            print(f"[記憶觸發] 用戶輸入『{user_msg}』，系統自動綁定上一次查詢的代號: {remembered_id}")

    # 4. 判斷是否為有效股票代號指令並執行分析
    if stock_match:
        current_time = time.time()
        last_time = user_last_request_time.get(user_id, 0)
        
        # 檢查冷卻時間 (目前已改為 30 秒)
        if current_time - last_time < COOL_DOWN_TIME:
            remaining = int(COOL_DOWN_TIME - (current_time - last_time))
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⏳ 助理正在幫您整理大數據中，請稍候 {remaining} 秒後再查詢。"))
            return

        user_last_request_time[user_id] = current_time
        
        # 立刻回覆使用者，防止 Webhook 超時掛掉
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text="🔍 好的，私人助理已收到指令，正在為您整理數據中，請稍候約 10 秒...")
        )

        # 建立非同步分析包裹器，將 user_id 傳進去存對話紀錄
        def async_ai_analysis_wrapper(uid, msg):
            try:
                print(f"[AI] 背景任務啟動，正在處理: {msg}")
                reply_text = get_ai_analysis(msg, uid)  # 將 uid 傳入 Test_AI
                line_bot_api.push_message(uid, TextSendMessage(text=reply_text))
                print(f"[LINE] 助理報告已成功推送到用戶: {uid}")
            except Exception as e:
                print(f"[LINE] 背景執行錯誤: {e}")
                line_bot_api.push_message(uid, TextSendMessage(text="❌ 報告主人，助理在後台整理資料時不小心跌倒了，請再試一次。"))

        # 開啟執行緒 (Thread) 在背景執行
        thread = threading.Thread(target=async_ai_analysis_wrapper, args=(user_id, final_query_msg))
        thread.start()
        
    else:
        # 如果訊息中完全沒有 4 位數字，且不是引導詞
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text="💡 提示：請輸入包含 4 位數台股代號的指令（例如：3189 多少錢），讓助理為您服務喔！")
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)