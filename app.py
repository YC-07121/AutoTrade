# app.py

from flask import Flask, request, abort, render_template
app = Flask(__name__)


from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

line_bot_api = LineBotApi(
    'C2ho/dgCl2vJNiKobbqSV2OvujgU9LoT0P2EEU0VDk3aVv402XMTPRrdfsy8LOniSJo6PyvY3pKg1INTxwiLZcCwzT1/rx2jvvPRw4YhcaabIyGBX8HhgnaaY5of0/IZzw56NZkHzpobXT+D2fzemQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('cb78f49836c94c88f36a8ffb3a263ee7')

ngrok="https://87f1-2001-b400-e28d-a56d-60bd-6c8f-ff1c-9c0a.ngrok-free.app"


import random




@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    getMessage = event.message
    usr_id = event.source.user_id
    # profile = line_bot_api.get_profile(UserId) #取得更詳細的使用者資訊 https://ithelp.ithome.com.tw/articles/10282156

    if event.type == 'message':  # 訊息觸發
        if getMessage.type == 'text':  # 訊息為文字
            message = getMessage.text.lower()
            if message == 'qr': 
                qr_template=TemplateSendMessage(
                        alt_text = '已開啟功能選單', #替代文字
                        template = ButtonsTemplate(
                            title = '功能選單',
                            text = '選擇要開啟的功能', #文字
                            actions=[
                                URITemplateAction(
                                    label='QR code scaner',
                                    # uri= ngrok+"/scanner.php?id="+usr_id
                                    uri= ngrok+"/scanner"
                                )
                            ]
                        )
                    )
                line_bot_api.reply_message(event.reply_token, qr_template)
                """
            elif message == 'ans':
                a=[5,6,7]
                b=[1,2,3]
                c=[1,2]
                d=[1,2]
                e=[0,9]
                f=[7,8,9]
                ans=""

                for aa in a:
                    for bb in b:
                        for cc in c:
                            for dd in d:
                                for ee in e:
                                    for ff in f:
                                        ans=ans+str(aa)+str(bb)+str(cc)+str(dd)+str(ee)+str(ff)+"\n"
          
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=ans)) 
            elif message == 'name':
                a=["雪","玉","靈","夜","闇","昊","霜","天","辰","宇","合","子","雲","流","葉","塵","安","卿","季"]
                b=["流辰","昊天","玉辰","雲塵","靈辰","靈闇","子雲"]
                
                ans=""
                for i in range(1,10):
                    c=random.randint(0,1)
                    if c:
                        random.shuffle(a)
                        ans=ans+a[0]+a[1]+a[2]+'\n'+a[3]+a[4]+a[5]+'\n'
                    else:
                        random.shuffle(a)
                        random.shuffle(b)
                        ans=ans+a[0]+b[0]+'\n'+b[0]+a[0]+'\n'

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=ans))
                """

            elif message == 'id':
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=usr_id))
            else :
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=event.message.text))
                
    elif event.type == 'follow':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text))
    elif event.type == 'join':            
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

@app.route("/scanner", methods=['GET'])
def scanner(event):
    usr_id = event.source.user_id
    return render_template('scanner.html?id='+usr_id)

if __name__ == "__main__":
    app.run()