# coding:utf-8

import logging
from utils.response_code import RET
from .BaseHandler import BaseHandler
from utils.session import Session
from hashlib import sha256
import config

"""
改进:
保存的session信息如果包括除用户名外数据,必然要再查询数据库,
存储登陆和注册都涉及到session信息的存储,代码冗余，
考虑精简代码或者在session信息中值存储用户名看是否可行
BUG:
1.浏览器第一次打开_xsrf信息未发送，表单提交受阻，再次刷新正常提交
2.发送手机验证码后应删除redis中的验证码信息,避免无用数据占用内存
3.注册成功应删除删除redis中的手机验证码缓存,避免无用数据占用内存
"""

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
        s1 = sha256()
        s1.update(password+config.password_key)
        password = s1.hexdigest()

        # 验证成功存入数据库
        try :
            self.db.execute("insert into ih_user_profile(up_name,up_mobile,up_passwd) "
                            "values(%(up_name)s, %(up_mobile)s, %(up_passwd)s)",
                            up_name= str(mobile),up_mobile= mobile,up_passwd= password)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库错误"))
        
        # 查询用户名对应用户数据
        try:
            use_data = self.db.get("select up_user_id,up_name,up_mobile from ih_user_profile where up_mobile = %(mobile)s",
                                       mobile=mobile)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

        # 登陆成功,保存session,
        self.session = Session(self)
        # 在session中加入up_user_id方便查找-
        self.session.data = dict(up_user_id=use_data['up_user_id'],up_name=use_data['up_name'],up_mobile=use_data['up_mobile'])
        self.session.save()

        # session保存成功返回数据
        self.write(dict(errcode=RET.OK))


class LoginHandler(BaseHandler):

    def post(self):
        mobile = self.json_dict.get('mobile')
        use_pwd = self.json_dict.get('password')

        if not all((mobile,use_pwd)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="账号/密码错误"))

        # 查询用户名对应用户数据
        try:
            use_data = self.db.get("select up_user_id,up_name,up_mobile,up_passwd from ih_user_profile where up_mobile = %(mobile)s",
                                       mobile=mobile)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

        # use_data为空
        if not use_data:
            return self.write(dict(errcode=RET.USERERR, errmsg="用户不存在"))

        print use_pwd

        # 用户传入密码加密
        s1 = sha256()
        s1.update(use_pwd+config.password_key)
        use_pwd = s1.hexdigest()
        print use_data


        # 密码不等
        if use_pwd != use_data['up_passwd']:
            return self.write(dict(errcode=RET.PWDERR, errmsg="密码错误"))


        # 登陆成功,保存session
        self.session = Session(self)
        # 在session中加入up_user_id方便查找-
        self.session.data = dict(up_user_id=use_data['up_user_id'],up_name=use_data['up_name'],up_mobile=use_data['up_mobile'])
        self.session.save()

        # 告知前端登陆成功
        self.write(dict(errcode=RET.OK))



