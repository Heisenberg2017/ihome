# coding:utf-8

import os
from handlers import Passport,VerifyCode,Profile,House,Order
from handlers.BaseHandler import StaticFileBaseHandler as StaticFileHandler

handler = [
    # 用户管理模块接口
    (r"/api/login", Passport.LoginHandler),  # 登陆
    (r"/api/logout", Passport.LogoutHandler),  # 退出登陆
    (r"/api/register", Passport.RegisterHandler),  # 注册
    (r"/api/check_login", Passport.CheckLoginHandler),  # 登陆验证
    (r"/api/piccode", VerifyCode.ImageCodeHandler),  # 图片验证码
    (r"/api/smscode", VerifyCode.PhoneCodeHandler),  # 短信验证码
    (r"/api/profile", Profile.ProfileHandler),  # 用户中心
    (r"/api/profile/avatar", Profile.AvatarHandler),  # 设置(修改)头像
    (r"/api/profile/name", Profile.RenameHandler),  # 设置(修改)用户名
    (r"/api/profile/auth", Profile.AuthHandler),
    # 房屋管理模块接口
    (r"/api/house/index", House.IndexHandler),  # 房屋主页
    (r"/api/house/my", House.MyHousesHandler),  # 我的房屋信息
    (r"/api/house/area", House.AreaInfoHandler),  # 区域信息接口
    (r"/api/house/info", House.HouseInfoHandler),  # 房屋详细信息
    (r"/api/house/image", House.HouseImageHandler),  # 添加房屋图片
    (r"/api/house/list", House.SearchHandler),  # 搜索房屋,排序展示
    # 订单管理模块接口
    (r"/api/order", Order.OrderHandler),  # 订单处理
    (r"/api/order/my", Order.MyOrderHandler),  # 我的未完成订单
    (r"/api/order/accept", Order.AcceptOrderHandler),  # 下单与取消订单
    (r"/api/order/comment", Order.CommentOrderHandler),  # 评论
    (r"/api/order/reject", Order.RejectOrderHandler),  # 房东拒单
    (r"/(.*)", StaticFileHandler,dict(path=os.path.join(os.path.dirname(__file__), "html"), default_filename="index.html"))
]