import unittest

from KalturaClientBase import KalturaObjectFactory
from KalturaCoreClient import KalturaMediaEntry
from kaltura_service import KalturaService

class KalturaServiceTest(unittest.TestCase):

    def xxxtest_should_upload_file(self):
        service = KalturaService()
        #print KalturaObjectFactory.objectFactories.get("KalturaMediaEntry")
        #self.assertTrue(KalturaObjectFactory.objectFactories.has_key('KalturaMediaEntry'))
        #print isinstance(KalturaObjectFactory.objectFactories['KalturaMediaEntry'](), KalturaMediaEntry)
        service.upload('tests/barsandtone.flv', "test", "")
