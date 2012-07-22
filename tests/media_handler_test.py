import json
from KalturaCoreClient import KalturaMediaEntry
from handler_test_case import HandlerTestCase
from handlers.media_handler import MediaHandler
from kaltura_service import KalturaService
from mockito import *

class MediaHandlerTest(HandlerTestCase):

    def setUp(self):
        self.handler = self.instantiate_handler(MediaHandler)
        uploaded_file = {"name" : "file_name", "body" : "file contents"}
        self.request.files = { "file_name" : [uploaded_file] }
        self.request.arguments = { "channel" : ["test"], "name" : "test"}
        self.service = mock()
        when(KalturaService).get_instance().thenReturn(self.service)

    def testShouldUploadToService(self):
        media_entry = KalturaMediaEntry(id="1")
        when(self.service).upload(any(), any(), "_channel:test").thenReturn(media_entry)

        response = self.do_post(self.handler)
        verify(self.service).upload(any(), any(), "_channel:test")
        response_json = json.loads(response.body)
        self.assertEquals("1", response_json.values()[0]['id'])

    def testShouldReturnErrorIfUploadFails(self):
        when(self.service).upload(any(), any(), "_channel:test").thenRaise(Exception("Error"))
        response = self.do_post(self.handler)
        response_json = json.loads(response.body)
        self.assertEquals("Error", response_json.values()[0]['error'])

