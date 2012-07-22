from handler_test_case import HandlerTestCase
from handlers.notification_handler import NotificationHandler
from handlers.push_service import PushService
from mockito import *

class NotificationHandlerTest(HandlerTestCase):

    def testShouldInvokePushService(self):
        handler = self.instantiate_handler(NotificationHandler)
        self.request.body=""
        self.request.arguments = { "tags" : ["_channel:test,foo,bar"],
                                 "entry_id" : ["1"],
                                 "download_url" : ["http://www.cnn.com"]}
        message_dict = {
            'entry_id' : "1",
            'download_url' : "http://www.cnn.com"
        }
        when(PushService).push("test", message_dict).thenReturn("ok")
        response = self.do_post(handler)
        verify(PushService).push("test", message_dict)
