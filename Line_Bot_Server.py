import os
import time
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from Test_AI import get_ai_analysis 

app = Flask(__name__)

# 從 Render 的 Environment 讀取正確的變數名稱
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 用來記錄每個使用者的最後請求時間
user_last_request_time = {}
# 【修改處】：冷卻時間延長至 300 秒 (5 分鐘)
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
    current_time = time.time()
    
    # 檢查是否在冷卻期內
    last_time = user_last_request_time.get(user_id, 0)
    if current_time - last_time < COOL_DOWN_TIME:
        remaining_time = int(COOL_DOWN_TIME - (current_time - last_time))
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚠️ 查詢太頻繁囉！為了維持 AI 穩定，請在 {remaining_time} 秒後再試。")
        )
        return

    # 記錄本次請求時間並執行
    user_last_request_time[user_id] = current_time
    
    try:
        reply_text = get_ai_analysis(event.message.text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print(f"LINE 回覆發生錯誤: {str(e)}")
        # 發生錯誤時重設時間，讓使用者不用白等 5 分鐘
        user_last_request_time[user_id] = 0 
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 系統繁忙或發生錯誤，請稍候片刻再試。")
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)