import sys

from KalturaClient import *
import logging

logging.basicConfig(level = logging.DEBUG,
    format = '%(asctime)s %(levelname)s %(message)s',
    stream = sys.stdout)

PARTNER_ID =int(os.environ.get("KALTURA_PARTNER_ID"))
ADMIN_SECRET = os.environ.get("KALTURA_ADMIN_SECRET")
SERVICE_URL = "http://www.kaltura.com"
USER_NAME = os.environ.get("KALTURA_USER_NAME")

class KalturaLogger(IKalturaLogger):
    def log(self, msg):
        logging.info(msg)

def GetConfig():
    config = KalturaConfiguration(PARTNER_ID)
    config.serviceUrl = SERVICE_URL
    config.setLogger(KalturaLogger())
    return config

class KalturaService(object):

    @classmethod
    def get_instance(cls):
        return KalturaService()

    def __init__(self):
        self.client = KalturaClient(GetConfig())

    def upload(self, media_file, name, tags):

        ks = self.client.generateSession(ADMIN_SECRET, USER_NAME, KalturaSessionType.ADMIN, PARTNER_ID, 120, "")
        self.client.setKs(ks)
        service = KalturaMediaService(client= self.client)
        uploadTokenId = service.upload(file(media_file, 'rb'))

        mediaEntry = KalturaMediaEntry()
        mediaEntry.setName(name)
        mediaEntry.setTags(tags)
        mediaEntry.setMediaType(KalturaMediaType(KalturaMediaType.VIDEO))
        return service.addFromUploadedFile(mediaEntry, uploadTokenId)
