import os
import time
import threading  # 新增：用於異步處理，避免 Line 逾時
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from Test_AI import get_ai_analysis 

app = Flask(__name__)

# 讀取金鑰
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 狀態記錄
user_last_request_time = {}
processed_msg_ids = set() 
COOL_DOWN_TIME = 120  # 冷卻時間維持 2 分鐘

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def async_ai_analysis(user_id, user_msg):
    """
    異步執行函數：在背景執行 AI 分析並使用 push_message 回傳
    """
    try:
        print(f"[AI] 背景任務啟動，正在分析: {user_msg}")
        reply_text = get_ai_analysis(user_msg)
        
        # 使用 push_message 將詳細報告送回給使用者
        line_bot_api.push_message(user_id, TextSendMessage(text=reply_text))
        print(f"[LINE] 分析報告已推送至用戶: {user_id}")
    except Exception as e:
        print(f"[LINE] 背景執行錯誤: {e}")
        line_bot_api.push_message(user_id, TextSendMessage(text="❌ 分析過程中發生錯誤，請檢查代號是否正確。"))

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

    # 3. 冷卻檢查
    current_time = time.time()
    last_time = user_last_request_time.get(user_id, 0)
    if current_time - last_time < COOL_DOWN_TIME:
        remaining = int(COOL_DOWN_TIME - (current_time - last_time))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⏳ 助理正在整理數據中，請稍候 {remaining} 秒後再查詢。"))
        return

    # 4. 判斷是否為股票代號並執行分析
    if user_msg.isdigit() and len(user_msg) >= 4:
        user_last_request_time[user_id] = current_time
        
        # 先立刻回覆使用者，避免 Line Webhook 逾時
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text=f"🔍 已收到代號 {user_msg}，資深分析助理正在進行多維度掃描，報告約需 10-15 秒，請稍候...")
        )

        # 開啟新執行緒 (Thread) 在背景跑 AI 分析，不卡住 Server
        thread = threading.Thread(target=async_ai_analysis, args=(user_id, user_msg))
        thread.start()
    else:
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text="💡 請輸入 4 位數台股代號（例如：2330），我將為您產出全方位分析報告。")
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000)) # Render 預設使用 10000
    app.run(host="0.0.0.0", port=port)