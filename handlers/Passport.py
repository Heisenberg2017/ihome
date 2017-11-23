# coding:utf-8

import logging
from utils.response_code import RET
from .BaseHandler import BaseHandler
from utils.session import Session
from hashlib import sha1


class RegisterHandler(BaseHandler):
    def post(self):
        # 输出获取的注册信息
        print self.json_dict
        mobile = self.json_dict.get('mobile')
        phone_code = self.json_dict.get('phonecode')
        password = self.json_dict.get('password')
        image_code = self.json_dict.get('imagecode')
        password2 = self.json_dict.get('password2')

        if not all((mobile, phone_code, password, password2)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="填写信息不完整"))

        if password != password2:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="两次输入密码不相同"))

        try:
            mobile_code = self.redis.get("sms_code_%s" % mobile)
        except Exception as e:
            logging(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据出错"))

        if not mobile_code:
            return self.write(dict(errcode=RET.NODATA, errmsg="验证码过期"))

        # 验证手机号对应短信验证码是否正确
        if mobile_code != phone_code:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="验证码错误"))

        # 密码sha加密
        s1 = sha1()
        s1.update(password)
        password = s1.hexdigest()

        # 验证成功存入数据库
        try :
            self.db.execute("insert into ih_user_profile(up_name,up_mobile,up_passwd) "
                            "values(%(up_name)s, %(up_mobile)s, %(up_passwd)s)",
                            up_name= str(mobile),up_mobile= mobile,up_passwd= password)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库错误"))

        # 存入数据库成功，保存session
        self.session = Session(self)
        # 在session中加入up_user_id方便查找-
        self.session.data = dict(user_name = mobile)
        self.session.save()

        # session保存成功返回数据
        self.write(dict(errcode=RET.OK))


class LoginHandler(BaseHandler):

    def post(self):
        mobile = self.json_dict.get('mobile')
        use_pwd = self.json_dict.get('password')

        if not all((mobile,use_pwd)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="账号/密码错误"))

        # 查询用户名对应密码
        try:
            pwd_exist = self.db.get("select up_passwd from ih_user_profile where up_mobile = %(mobile)s",
                                       mobile=mobile)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

        # 密码不存在
        if not pwd_exist:
            return self.write(dict(errcode=RET.USERERR, errmsg="用户不存在"))

        # 用户传入密码加密
        s1 = sha1()
        s1.update(use_pwd)
        use_pwd = s1.hexdigest()

        # 密码不等
        print use_pwd
        print pwd_exist
        if use_pwd != pwd_exist['up_passwd']:
            return self.write(dict(errcode=RET.PWDERR, errmsg="密码错误"))

        data_type = self.db.get("select * from ih_user_profile where up_mobile = %(mobile)s",
                                       mobile=mobile)
        print data_type
        # 登陆成功session-
        # 登陆成功
        self.write(dict(errcode=RET.OK))



