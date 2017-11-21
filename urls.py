# coding:utf-8

import os
from handlers import Passport
from handlers.BaseHandler import StaticFileBaseHandler as StaticFileHandler

handler = [

            (r"/(.*)", StaticFileHandler,
            dict(path=os.path.join(os.path.dirname(__file__), "html"), default_filename="index.html"))
           ]
