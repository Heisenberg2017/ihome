# coding:utf-8
import json
from tornado.web import RequestHandler, StaticFileHandler


class BaseHandler(RequestHandler):
    """handler基类"""

    @property
    def db(self):
        return self.application.db

    @property
    def redis(self):
        return self.application.redis

    def prepare(self):
        if self.request.headers.get("Content-Type","").startswith("application/json"):
            self.json_dict = json.loads(self.request.body)
        else:
            self.json_dict = {}

    def write_error(self, status_code, **kwargs):
        pass

    def set_default_handlers(self):
        pass

    def initialize(self):
        pass

    def on_finish(self):
        pass


class StaticFileBaseHandler(StaticFileHandler):
    """自定义静态文件处理类, 在用户获取html页面的时候设置_xsrf的cookie"""
    def __init__(self, *args, **kwargs):
        super(StaticFileBaseHandler, self).__init__(*args, **kwargs)
        self.xsrf_token