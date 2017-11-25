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
减少不必要的数据库查询操作
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