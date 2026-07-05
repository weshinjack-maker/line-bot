from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os
import requests
import urllib.parse

app = Flask(__name__)

configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

# 📣 你的專屬安卓手機訂閱頻道
NTFY_TOPIC = 'weshin_line_notify_99'

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

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # 動作 A：回覆客人 LINE
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
        
        # 動作 B：發送 ntfy 手機系統推播通知給老闆（Android）
        if NTFY_TOPIC:
            # 使用更安全的網址參數傳送中文，避免拉丁編碼錯誤
            message_content = f"客人說：{user_message}"
            encoded_message = urllib.parse.quote(message_content)
            encoded_title = urllib.parse.quote("LINE官方帳號新訊息")
            
            ntfy_url = f"https://ntfy.sh/{NTFY_TOPIC}/publish?message={encoded_message}&title={encoded_title}&tags=loudspeaker&priority=high"
            
            try:
                requests.get(ntfy_url)
            except Exception as e:
                print(f"ntfy 推播失敗: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
