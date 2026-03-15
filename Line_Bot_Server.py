from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from Test_AI import get_ai_analysis 

app = Flask(__name__)

# 填入你的 LINE Channel Access Token 和 Secret
line_bot_api = LineBotApi('BteSrdaIB+E1biC82fx+pYO6aGuox4vj6BA4clTIWQehonm2aJYgrXynYWL+OLxCGVRB6yu0+FBXBZOVXMa6Bwm1LzZTqf++0QuHDuz9J1YOthtMzwhoLPxfhF21qoQaz5JRPyI0b6SryOp7wY6ihQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('6a7107c2f4721cd0bf3f2207ebdd22ca')

@app.route("/callback", methods=['POST'])
def callback():
    # 獲取簽名與內容
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    print("收到 LINE 的請求！") # 這行能幫助你除錯
    
    try:
        # 處理事件
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ 簽名錯誤")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 獲取使用者訊息
    user_msg = event.message.text
    print(f"收到訊息: {user_msg}")
    
    # 呼叫 Test_AI 分析
    reply_text = get_ai_analysis(user_msg)
    
    # 回覆 LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(port=5000)