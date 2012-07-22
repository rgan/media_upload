#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import tornado.ioloop
import tornado.web
import tornado.autoreload
from handlers.media_handler import MediaHandler
from handlers.notification_handler import NotificationHandler

class Application(tornado.web.Application):
    def __init__(self):

        handlers = [
            (r"/media", MediaHandler),
            (r"/notify", NotificationHandler)
        ]

        settings = {"static_path": os.path.join(os.path.dirname(__file__), "static")}
        tornado.web.Application.__init__(self, handlers, **settings)


def main():

    app = Application()
    app.listen(os.environ.get("PORT", 5000))

    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
