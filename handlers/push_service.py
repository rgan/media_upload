import json
import os
from Pubnub import Pubnub

PUBLISH_KEY=os.environ.get("PUBLISH_KEY")
SUBSCRIBE_KEY=os.environ.get("SUBSCRIBE_KEY")
SECRET_KEY=os.environ.get("SECRET_KEY")

class PushService(object):

    @classmethod
    def push(cls, channel, message_dict):
        pubnub = Pubnub(PUBLISH_KEY, SUBSCRIBE_KEY, SECRET_KEY, False )
        info = pubnub.publish({
            'channel' : channel,
            'message' : json.dumps(message_dict)
        })
        return info

