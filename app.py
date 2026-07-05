from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (Configuration, ApiClient, MessagingApi, ReplyMessageRequest, PushMessageRequest, TextMessage)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os

app = Flask(__name__)

configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
MY_LINE_USER_ID = os.environ.get('MY_LINE_USER_ID')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    
    # 📝 1. 回覆給客人的罐頭訊息
    reply_text = f"您好！感謝您的訊息。我們已收到您的提問：\n「{user_message}」\n\n專人將會盡快與您聯繫！"
    
    # 📝 2. 偷偷發給老闆（你）的通知訊息
    admin_notice = f"🔔 報告老闆！有新客人傳來訊息：\n「{user_message}」\n\n請記得有空時登入後台回覆喔！"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # 動作 A：回覆客人
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
        
        # 動作 B：如果環境變數有填 User ID，就私訊通知老闆
        if MY_LINE_USER_ID:
            line_bot_api.push_message(
                PushMessageRequest(
                    to=MY_LINE_USER_ID,
                    messages=[TextMessage(text=admin_notice)]
                )
            )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
