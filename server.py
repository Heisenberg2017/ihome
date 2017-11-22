# coding:utf-8

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import os
import tornado
import config
import redis
import torndb

from handlers import Passport
from urls import handler
from tornado.options import options, define
from tornado.web import RequestHandler

define("port", type=int, default=8000, help="run server on the given port")


class Application(tornado.web.Application):
    """"""
    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.db = torndb.Connection(**config.mysql_options)
        self.redis = redis.StrictRedis(**config.redis_options)


def main():
    options.logging = config.log_lever
    # options.log_file_prefix = config.log_file
    tornado.options.parse_command_line()
    app = Application(
            # [(r"", IndexHandler),]
            handler,**config.settings
        )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    # http_server.bind(8000)
    # http_server.start(0)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()