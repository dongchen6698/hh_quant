import requests
import json


class BroadCastToWeChat:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url
        self.msg_header = {"Content-Type": "application/json"}

    def send_msg(self, messge):
        messages = {"msgType": "text", "text": {"content": messge}}
        messages = json.dumps(messages)
        info = requests.post(url=self.webhook_url, headers=self.msg_header, data=messages)
        print(info)


if __name__ == "__main__":
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e407684d-2ef6-43ca-9312-9a527f778ff4"
    bctw = BroadCastToWeChat(webhook_url=webhook_url)
    bctw.send_msg("Hello!")
