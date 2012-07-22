import json
import os
import tornado.web
from kaltura_service import KalturaService
import uuid

class MediaHandler(tornado.web.RequestHandler):

    CHANNEL_TAG_MARKER = "_channel"

    def post(self):
        service = KalturaService.get_instance()
        result = {}
        for name, files in self.request.files.items():
            for datafile in files:
                try:
                    self.ensure('/tmp')
                    name = 'tmp/file_{0}'.format(uuid.uuid1().hex)
                    with open(name, 'wb') as f:
                        f.write(datafile["body"])
                    media_entry = service.upload(name, self.get_argument("name"), "%s:%s" % (MediaHandler.CHANNEL_TAG_MARKER, self.get_argument("channel")))
                    result[name] = { 'id' : media_entry.id }
                    os.remove(name)
                except Exception as e:
                    result[name] = { 'error' : e.message }
        self.write(json.dumps(result))

    def ensure(self, path):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
