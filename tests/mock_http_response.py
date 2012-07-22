class MockHttpResponse():
    def __init__(self, code, write_buffer, headers):
        self.body = "".join(write_buffer)
        self.headers = headers
        self.status_code = code

    def get_header(self, name):
        return self.headers[name]

