import os
import time
import threading
import re  # 新增：用於提取文字中的股票代號
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
        line_bot_api.push_message(user_id, TextSendMessage(text="❌ 分析過程中發生錯誤，請稍後再試。"))

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

    # 3. 提取訊息中的 4 位數股票代號
    stock_match = re.search(r'\d{4}', user_msg)

    # 4. 判斷邏輯修改
    if stock_match:
        # 檢查冷卻時間
        current_time = time.time()
        last_time = user_last_request_time.get(user_id, 0)
        
        if current_time - last_time < COOL_DOWN_TIME:
            remaining = int(COOL_DOWN_TIME - (current_time - last_time))
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⏳ 助理正在整理數據中，請稍候 {remaining} 秒後再查詢。"))
            return

        user_last_request_time[user_id] = current_time
        
        # 先立刻回覆使用者
        found_id = stock_match.group()
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text=f"🔍 已偵測到代號 {found_id}，分析助理正在思考您的問題，請稍候約 10-15 秒...")
        )

        # 啟動異步處理
        thread = threading.Thread(target=async_ai_analysis, args=(user_id, user_msg))
        thread.start()
    else:
        # 如果訊息中完全沒有 4 位數字，才顯示提示
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text="💡 請輸入包含 4 位數台股代號的訊息（例如：2330 股價如何），我將為您進行精準分析。")
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)