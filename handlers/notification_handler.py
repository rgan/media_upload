import json
from Pubnub import Pubnub
import tornado.web
from handlers.media_handler import MediaHandler
from handlers.push_service import PushService

class NotificationHandler(tornado.web.RequestHandler):

    def post(self):
        print "Received notification:"
        #notification_id=985696321&notification_type=entry_add&puser_id=xxxx&partner_id=xxxx&entry_id=1_z69ulvxy&name=barsandtone&tags=&search_text=_KAL_NET_+_1058031_+_MEDIA_TYPE_1%7C++barsandtone&media_type=1&length_in_msecs=0&permissions=&thumbnail_url=http%3A%2F%2Fcdnbakmi.kaltura.com%2Fp%2F1058031%2Fsp%2F105803100%2Fthumbnail%2Fentry_id%2F1_z69ulvxy%2Fversion%2F0&kshow_id=1_6k3n83c2&roughcut_id=&group_id=&partner_data=&status=7&width=&height=&data_url=http%3A%2F%2Fcdnbakmi.kaltura.com%2Fp%2F1058031%2Fsp%2F105803100%2Fflvclipper%2Fentry_id%2F1_z69ulvxy%2Fversion%2F0&download_url=http%3A%2F%2Fcdnbakmi.kaltura.com%2Fp%2F1058031%2Fsp%2F105803100%2Fraw%2Fentry_id%2F1_z69ulvxy%2Fversion%2F0&download_size=0&media_date=&ks_data=&signed_fields=notification_id%2Cnotification_type%2Cpuser_id%2Cpartner_id%2Centry_id%2Cname%2Ctags%2Csearch_text%2Cmedia_type%2Clength_in_msecs%2Cpermissions%2Cthumbnail_url%2Ckshow_id%2Croughcut_id%2Cgroup_id%2Cpartner_data%2Cstatus%2Cwidth%2Cheight%2Cdata_url%2Cdownload_url%
        print self.request.body
        message_dict = {
              'entry_id' : self.get_argument('entry_id'),
              'download_url' : self.get_argument('download_url')
        }
        PushService.push(self.get_channel(self.get_argument('tags')), message_dict)

    def get_channel(self, tags):
        for tag in tags.split(","):
            if MediaHandler.CHANNEL_TAG_MARKER in tag:
                return tag[len(MediaHandler.CHANNEL_TAG_MARKER)+1:]
        return None