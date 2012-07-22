import unittest
from mock_http_request import MockHttpRequest
from mock_http_response import MockHttpResponse
from mockito import *

class HandlerTestCase(unittest.TestCase):

    def tearDown(self):
        unstub()

    def do_get(self, handler, *args):
        return self.do_method("get", handler, *args)

    def do_post(self, handler, *args):
        return self.do_method("post", handler, *args)

    def do_delete(self, handler, *args):
        return self.do_method("delete", handler, *args)

    def do_put(self, handler, *args):
        return self.do_method("put", handler, *args)

    def do_method(self, method, handler, *args):
        getattr(handler, method)(*args)
        return MockHttpResponse(handler.get_status(), handler._write_buffer, handler._headers)

    def instantiate_handler(self, handler_cls, **kwargs):
        app = mock()
        app.ui_methods = {}
        app.ui_modules = {}
        self.request = MockHttpRequest()
        return handler_cls(app, self.request, **kwargs)
