# coding:utf-8

import uuid
import json
import logging
import config


class Session(object):
    """"""
    def __init__(self, request_handler):
        self.request_handler = request_handler
        self.session_id = self.request_handler.get_secure_cookie("session_id")

        if not self.session_id:
            # 用户首次访问
            self.session_id = uuid.uuid4().get_hex()
            self.data = {}
        else:
            try:
                data = self.request_handler.redis.get("session_%s" % self.session_id)
            except Exception as e:
                logging.error(e)
                self.data = {}
            if not data:
                self.data = {}
            else:
                self.data = json.loads(data)

    def save(self):
        json_data = json.dumps(self.data)
        try:
            self.request_handler.redis.setex("session_%s" % self.session_id, config.session_expires, json_data)
        except Exception as e:
            logging.error(e)
            raise Exception("save session fail")
        else:
            self.request_handler.set_secure_cookie("session_id", self.session_id)

    def clear(self):
        self.request_handler.clear_cookie("session_id")
        try:
            self.request_handler.redis.delete("session_%s" % self.session_id)
        except Exception as e:
            logging.error(e)

