import os
import time
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
COOL_DOWN_TIME = 120  # 先縮短到 2 分鐘方便測試

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
    
    # 這是給你看的偵錯訊息
    print(f"\n[LINE] 收到訊息: {user_msg} (ID: {msg_id})")

    if msg_id in processed_msg_ids:
        print("[LINE] 重複請求，略過")
        return
    processed_msg_ids.add(msg_id)

    if user_msg == "測試":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 伺服器運作中！"))
        return

    # 冷卻檢查
    current_time = time.time()
    last_time = user_last_request_time.get(user_id, 0)
    if current_time - last_time < COOL_DOWN_TIME:
        remaining = int(COOL_DOWN_TIME - (current_time - last_time))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⏳ 冷卻中，剩餘 {remaining} 秒"))
        return

    user_last_request_time[user_id] = current_time
    
    try:
        print(f"[LINE] 開始呼叫 AI 分析...")
        reply_text = get_ai_analysis(user_msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        print("[LINE] 回覆已成功送出")
    except Exception as e:
        print(f"[LINE] 發生致命錯誤: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 系統暫時無法回應，請確認代號是否正確。"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)