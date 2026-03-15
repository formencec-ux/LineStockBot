import os
import time
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from Test_AI import get_ai_analysis 

app = Flask(__name__)

# 【修正】：這裡括號內必須是變數名稱，讓程式去 Render 的設定裡撈資料
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 用來記錄每個使用者的最後請求時間
user_last_request_time = {}
COOL_DOWN_TIME = 180  # 3 分鐘冷卻

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
    current_time = time.time()
    
    # 檢查是否在 3 分鐘冷卻期內
    last_time = user_last_request_time.get(user_id, 0)
    if current_time - last_time < COOL_DOWN_TIME:
        remaining_time = int(COOL_DOWN_TIME - (current_time - last_time))
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚠️ 請休息一下！機器人每 3 分鐘才能查詢一次，請在 {remaining_time} 秒後再試。")
        )
        return

    # 執行查詢並記錄時間
    user_last_request_time[user_id] = current_time
    
    try:
        reply_text = get_ai_analysis(event.message.text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 目前 AI 請求過多，請 5 分鐘後再嘗試。")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ 系統發生錯誤，請稍後再試。")
            )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)