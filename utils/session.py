# coding:utf-8

import uuid
import json
import logging
import config


class Session(object):
    """Session信息类"""
    def __init__(self, request_handler):
        """
        初始化session类,设置session数据,
        可通过self.data访问session数据,若无data数据，则self.data = {}
        :param request_handler: RequestHandler类或者子类的实例
        """
        self.request_handler = request_handler
        self.session_id = self.request_handler.get_secure_cookie("session_id")
        # cookie中无session_id
        if not self.session_id:
            # 给用户设置一个session_id
            self.session_id = uuid.uuid4().get_hex()
            # 初始化session数据为空
            self.data = {}
        else:
            # cookie中有session_id，查询数据库中对应的数据
            try:
                data = self.request_handler.redis.get("session_%s" % self.session_id)
            except Exception as e:
                logging.error(e)
                data = {}
            if not data:
                self.data = {}
            else:
                # 将redis中的session数据反序列化取出
                self.data = json.loads(data)

    def save(self):
        """将更新后的self.data序列化,存入redis数据库中"""
        json_data = json.dumps(self.data)
        try:
            self.request_handler.redis.setex("session_%s" % self.session_id, config.session_expires, json_data)
        except Exception as e:
            logging.error(e)
            raise Exception("save session fail")
        else:
            self.request_handler.set_secure_cookie("session_id", self.session_id)

    def clear(self):
        """清除用户session信息"""
        # 清除用户浏览器上的session_id
        self.request_handler.clear_cookie("session_id")
        try:
            # 清除redis中的session数据
            self.request_handler.redis.delete("session_%s" % self.session_id)
        except Exception as e:
            logging.error(e)

