# coding:utf-8

import os
from handlers import Passport,VerifyCode
from handlers.BaseHandler import StaticFileBaseHandler as StaticFileHandler

handler = [
    (r"/api/register",Passport.RegisterHandler),
    (r"/api/piccode",VerifyCode.ImageCodeHandler),
    (r"/api/smscode",VerifyCode.PhoneCodeHandler),
    (r"/(.*)", StaticFileHandler,dict(path=os.path.join(os.path.dirname(__file__), "html"), default_filename="index.html"))
]
