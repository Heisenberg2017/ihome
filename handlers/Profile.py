# coding:utf-8

import logging
from .BaseHandler import BaseHandler
from utils.qiniu_storage import storage
from utils.session import Session
from utils.response_code import RET
from utils.commons import required_login
import config


class ProfileHandler(BaseHandler):
    # errcode name mobile avatar
    @required_login
    def get(self):
        # data数据应由数据库查询得到
        user_data = self.session.data
        data = {'name':user_data.get('up_name'),'mobile':user_data.get('up_mobile'),'avatar':config.image_domain+user_data.get('up_avatar')}
        self.write({'errcode': RET.OK, 'data':data})


class AvatarHandler(BaseHandler):
    """"""
    @required_login
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
        try:
            self.db.execute("update ih_user_profile set up_avatar = %(avatar_url)s where up_user_id = %(up_user_id)s", avatar_url=key, up_user_id=self.session.data.get('up_user_id'))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

        # 更新session
        self.session.data['up_avatar'] = key
        self.session.save()

        data = config.image_domain+self.session.data.get('up_avatar')
        self.write(dict(errcode=RET.OK, data=data))


class RenameHandler(BaseHandler):
    @required_login
    def post(self):
        print self.json_dict
        # 获取用户名
        new_name = self.json_dict.get('name')
        # 取出session中的用户id

        print self.session.data.get('up_user_id')
        # 更新数据库
        try:
            self.db.execute("update ih_user_profile set up_name = %(up_name)s where up_user_id = %(up_user_id)s", up_name = new_name, up_user_id=self.session.data.get('up_user_id'))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))



        # 更新session
        self.session.data['up_name'] = new_name
        self.session.save()

        # 返回处理信息
        self.write(dict(errcode=RET.OK))


class AuthHandler(BaseHandler):
    @required_login
    def get(self):
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

    @required_login
    def post(self):
        print self.json_dict
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
