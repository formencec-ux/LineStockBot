import os
import time
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from Test_AI import get_ai_analysis 

app = Flask(__name__)

# 從 Render 的 Environment 讀取設定
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 記錄每個使用者的最後請求時間 (Key: user_id, Value: timestamp)
user_last_request_time = {}
# 設定冷卻時間為 300 秒 (5 分鐘)
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
    user_msg = event.message.text.strip()
    current_time = time.time()
    
    print(f"--- 收到訊息: {user_msg} (來自: {user_id}) ---")

    # 1. 偵測模式：如果輸入「測試」，直接回覆，不計入冷卻
    if user_msg == "測試":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅ 伺服器連線正常！請嘗試輸入股票代號（例如 2330）。")
        )
        return

    # 2. 檢查冷卻時間
    last_time = user_last_request_time.get(user_id, 0)
    if current_time - last_time < COOL_DOWN_TIME:
        remaining = int(COOL_DOWN_TIME - (current_time - last_time))
        print(f"仍在冷卻中，剩餘 {remaining} 秒")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚠️ 查詢太頻繁囉！請在 {remaining} 秒後再嘗試查詢下一支股票。")
        )
        return

    # 3. 通過檢查，執行 AI 分析
    # 先更新時間，避免在 AI 跑的時候又有訊息塞進來
    user_last_request_time[user_id] = current_time
    
    try:
        reply_text = get_ai_analysis(user_msg)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print(f"❌ 系統錯誤: {e}")
        # 發生錯誤時重設時間，讓使用者不用白等
        user_last_request_time[user_id] = 0
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 系統暫時無法處理您的請求，請稍候片刻。")
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)