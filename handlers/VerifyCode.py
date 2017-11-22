# coding:utf-8
import logging
import constants
from .BaseHandler import BaseHandler
from utils.captcha.captcha import captcha
from libs.yuntongxun import SendTemplateSMS
import random
from utils.response_code import RET


class ImageCodeHandler(BaseHandler):
    """"""
    def get(self):
        code_id = self.get_argument("cur")
        pre_code_id = self.get_argument("pre")
        if pre_code_id:
            try:
                self.redis.delete("image_code_%s" % pre_code_id)
            except Exception as e:
                logging.error(e)

        # name 图片验证码名称
        # test 图片验证码文本
        # image 图片验证码二进制数据
        name, text, image = captcha.generate_captcha()
        try:
            self.redis.setex("image_code_%s" % code_id, constants.IMAGE_CODE_EXPIRES_SECONDS, text)

        except Exception as e:
            logging.error(e)
            self.write("")
        self.set_header("Content-Type", "image/jpg")
        self.write(image)


class PhoneCodeHandler(BaseHandler):
    """"""
    def post(self):
        # 获取的字典数据
        print self.json_dict
        # 获取参数
        mobile_code = ''
        mobile = self.json_dict['mobile']
        piccode = self.json_dict['piccode']
        piccode_id = self.json_dict['piccode_id']
        # 判断图片验证码
        print mobile
        print piccode
        piccode_redis = self.redis.get("image_code_%s" % piccode_id)

        if piccode_redis:
            # 图片验证码正确
            if piccode.upper() == piccode_redis.upper():

                # 判断电话号码是否已注册
                # if 0:
                #     self.write(dict(errcode=4004, errmsg="手机号已注册"))

                # 生成随机4位验证码数字
                for i in range(4):
                    mobile_code += str(random.randint(1,9))
                print mobile_code
                # 发送短信
                # SendTemplateSMS.ccp.sendTemplateSMS(mobile, [mobile_code, 5], 1)
                # 短信成功发，送将手机号对应的验证码存入redis中，有效时间5分钟
                self.redis.setex("mobile_code_%s" % mobile, constants.MOBILE_CODE_EXPIRES_SECONDS, mobile_code)
                self.write(dict(errcode=0))

            # 图片验证码错误
            else:
                # 失败：返回错误信息
                self.write(dict(errcode=RET.DATAERR, errmsg="验证码错误"))
        else:
            self.write(dict(errcode=RET.NODATA,errmsg="验证码已过期"))
