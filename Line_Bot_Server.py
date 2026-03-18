import os
import time
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from Test_AI import get_ai_analysis 

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

user_last_request_time = {}
processed_msg_ids = set() # 新增：用來記錄已處理過的訊息 ID
COOL_DOWN_TIME = 300  

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
    user_id = event.source.user_id
    msg_id = event.message.id # 取得訊息唯一標記
    user_msg = event.message.text.strip()
    current_time = time.time()

    # 防護一：如果是 LINE 自動重發的重複訊息，直接無視
    if msg_id in processed_msg_ids:
        return
    processed_msg_ids.add(msg_id)

    if user_msg == "測試":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 連線 OK！"))
        return

    # 防護二：冷卻檢查
    last_time = user_last_request_time.get(user_id, 0)
    if current_time - last_time < COOL_DOWN_TIME:
        remaining = int(COOL_DOWN_TIME - (current_time - last_time))
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚠️ 請在 {remaining} 秒後再查詢下一支。")
        )
        return

    user_last_request_time[user_id] = current_time
    
    try:
        # 執行 AI 分析
        reply_text = get_ai_analysis(user_msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    except Exception as e:
        user_last_request_time[user_id] = 0
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 處理逾時，請稍後重試。"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)