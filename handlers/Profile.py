# coding:utf-8

import logging
from .BaseHandler import BaseHandler
from utils.qiniu_storage import storage
from utils.session import Session
from utils.response_code import RET
import config

"""
考虑在图片更新的名字更新时不作数据库查询
更新未出错证明已经存入数据库
session信息的更新直接使用self.session.get('XXX')='XXX'完成
减少不必要的数据库查询操作(注册,更换头像,改名的数据库查询操作均可免去)
判断用户提交json数据是否为空可放在prepare中判断
"""
class ProfileHandler(BaseHandler):
    # errcode name mobile avatar
    def get(self):
        self.session = Session(self)
        if not self.session.data:
            return self.write({'errcode':RET.SESSIONERR})
        # data数据应由数据库查询得到
        user_data = self.session.data
        data = {'name':user_data.get('up_name'),'mobile':user_data.get('up_mobile'),'avatar':config.image_domain+user_data.get('up_avatar')}
        self.write({'errcode': RET.OK, 'data':data})


class AvatarHandler(BaseHandler):
    """"""
    def post(self):
        try:
            image_data = self.request.files['avatar'][0]['body']
        except Exception as e:
            # 参数出错
            logging.error(e)
            return self.write("")
        try:
            key = storage(image_data)
        except Exception as e:
            logging.error(e)
            return self.write("")

        print key
        # 更新用户头像url到数据库内
        self.session = Session(self)
        try:
            self.db.execute("update ih_user_profile set up_avatar = %(avatar_url)s where up_user_id = %(up_user_id)s", avatar_url=key, up_user_id=self.session.data.get('up_user_id'))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))
        # 查询用户名对应用户数据
        try:
            use_data = self.db.get(
                "select up_user_id,up_name,up_mobile,up_passwd,up_avatar from ih_user_profile where up_user_id = %(up_user_id)s",
                up_user_id=self.session.data.get('up_user_id'))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))
        # 更新session
        self.session.data = dict(up_user_id=use_data['up_user_id'],up_name=use_data['up_name'],up_mobile=use_data['up_mobile'],up_avatar=use_data['up_avatar'])
        self.session.save()

        data = config.image_domain+self.session.data.get('up_avatar')
        self.write(dict(errcode=RET.OK, data=data))


class RenameHandler(BaseHandler):
    def post(self):
        print self.json_dict
        # 获取用户名
        new_name = self.json_dict.get('name')
        # 取出session中的用户id
        self.session = Session(self)

        if not self.session.data:
            return self.write({'errcode': RET.SESSIONERR})

        print self.session.data.get('up_user_id')
        # 更新数据库
        try:
            self.db.execute("update ih_user_profile set up_name = %(up_name)s where up_user_id = %(up_user_id)s", up_name = new_name, up_user_id=self.session.data.get('up_user_id'))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

        # 查询用户名对应用户数据
        try:
            use_data = self.db.get(
                "select up_user_id,up_name,up_mobile,up_passwd,up_avatar from ih_user_profile where up_user_id = %(up_user_id)s",
                up_user_id=self.session.data.get('up_user_id'))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

        # 更新session
        self.session.data = dict(up_user_id=use_data['up_user_id'],up_name=use_data['up_name'],up_mobile=use_data['up_mobile'],up_avatar=use_data['up_avatar'])
        self.session.save()

        # 返回处理信息
        self.write(dict(errcode=RET.OK))


class AuthHandler(BaseHandler):
    def get(self):
        # 获取session信息
        self.session = Session(self)
        if not self.session.data:
            return self.write(dict(errcode=RET.SESSIONERR))

        # 查询用户名对真实姓名,证件号
        try:
            use_data = self.db.get(
                "select up_real_name,up_id_card from ih_user_profile where up_user_id = %(up_user_id)s",
                up_user_id=self.session.data.get('up_user_id'))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

        if not use_data:
            return self.write('')
        data = {'id_card':use_data.get('up_real_name'),'real_name':use_data.get('up_id_card')}
        self.write({'errcode':RET.OK,'data':data})

    def post(self):
        print self.json_dict
        self.session = Session(self)
        # 获取姓名和证件号
        real_name = self.json_dict.get('real_name')
        id_card = self.json_dict.get('id_card')

        # 检查是该身份证号是否已实名认证过

        # 进行实名认证
        if not (real_name == u'老王' and id_card == '3505211'):
            return self.write('')

        # 认证通过,将信息存入数据库
        try:
            self.db.execute("update ih_user_profile set up_real_name = %(up_real_name)s,up_id_card = %(up_id_card)s where up_user_id = %(up_user_id)s",
                            up_real_name=real_name, up_id_card=id_card , up_user_id=self.session.data.get('up_user_id'))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))
        # 存入数据库成功
        self.write({'errcode':RET.OK})
