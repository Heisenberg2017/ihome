# coding:utf-8

import logging
from .BaseHandler import BaseHandler


class RegisterHandler(BaseHandler):
    def post(self):
        # 输出获取的注册信息
        print self.json_dict
        mobile = self.json_dict['mobile']
        phone_code = self.json_dict['phonecode']
        password = self.json_dict['password']
        image_code = self.json_dict['imagecode']
        password2 = self.json_dict['password2']
        mobile_code = self.redis.get("image_code_%s" % mobile)
        # 验证手机号对应短信验证码是否正确
        if mobile_code:
            # 验证码正确
            if mobile_code == phone_code:
                # 电话号码是否唯一
                pass
            # 验证码错误
            else:
                pass
        # 缓存中没有数据
        else:
            pass


