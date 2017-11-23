# coding:utf-8
import logging
import constants
from .BaseHandler import BaseHandler
from utils.captcha.captcha import captcha
from libs.yuntongxun import SendTemplateSMS
import random
from utils.response_code import RET
import re


class ImageCodeHandler(BaseHandler):
    """"""
    def get(self):
        code_id = self.get_argument("cur","")
        pre_code_id = self.get_argument("pre","")
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
            return self.write("")

        self.set_header("Content-Type", "image/jpg")
        self.write(image)


class PhoneCodeHandler(BaseHandler):
    """"""
    def post(self):
        # 获取的字典数据
        print self.json_dict
        # 获取参数
        mobile = self.json_dict.get('mobile')
        piccode = self.json_dict.get('piccode')
        piccode_id = self.json_dict.get('piccode_id')

        if not all((mobile, piccode, piccode_id)):
            return self.write(dict(errcode=RET.PARAMERR,errmsg="参数错误"))
        # 判断图片验证码
        print mobile
        print piccode
        
        try:
            piccode_redis = self.redis.get("image_code_%s" % piccode_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询出错"))

        if not piccode_redis:
            return self.write(dict(errcode=RET.NODATA, errmsg="验证码过期"))
        

        # 图片验证码正确
        if piccode.upper() == piccode_redis.upper():

            # 判断号码是否正确
            if len(mobile)>11:
                return self.write(dict(errcode=RET.PARAMERR, errmsg="号码格式错误"))
            if not re.match(r"1\d{10}", mobile):
                return self.write(dict(errcode=RET.PARAMERR, errmsg="号码格式错误"))
            # 判断电话号码是否已注册
            try:
                mobile_exist = self.db.get("select up_mobile from ih_user_profile where up_mobile = %(mobile)s",mobile=mobile)
            except Exception as e:
                logging.error(e)
                return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

            if mobile_exist:
                return self.write(dict(errcode=RET.PARAMERR, errmsg="号码已注册"))

            # if 0:
            #     self.write(dict(errcode=4004, errmsg="手机号已注册"))

            # 生成随机4位验证码数字
            # sms_code = ''
            # for i in range(4):
            #     sms_code += str(random.randint(1,9))
            sms_code = "%04d" % random.randint(0, 9999)
            print sms_code

            # 送将手机号对应的验证码存入redis中，有效时间5分钟
            try:
                self.redis.setex("sms_code_%s" % mobile, constants.MOBILE_CODE_EXPIRES_SECONDS, sms_code)
            except Exception as e:
                logging.error(e)
                return self.write(dict(errcode=RET.DBERR, errmsg="生成验证码错误"))
            # 发送短信,后期需要改为异步
            # try:
            #     SendTemplateSMS.ccp.sendTemplateSMS(mobile, [sms_code, constants.MOBILE_CODE_EXPIRES_SECONDS/60], 1)
            # except Exception as e:
            #     logging.error(e)
            #     return self.write(dict(errcode=RET.THIRDERR, errmsg="发送失败"))

            # 短信验证码发送成功，删除redis中验证码缓存-

            self.write(dict(errcode=RET.OK,errmsg="OK"))

        # 图片验证码错误
        else:
            # 失败：返回错误信息
            self.write(dict(errcode=RET.DATAERR, errmsg="验证码错误"))
