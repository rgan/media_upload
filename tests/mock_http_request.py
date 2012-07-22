class MockHttpRequest():

    def __init__(self):
        self.connection = None
        self._status_code = 200

    def supports_http_1_1(self):
        return True
