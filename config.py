# coding:utf-8
import os

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "template_path": os.path.join(os.path.dirname(__file__), "template"),
    "cookie_secret": "0vULIGRVT8CAgloJXNeF1FQDF6RSTk5OjDfrMFxiP4Q=",
    "xsrf_cookies": True,
    "debug": True,
}

mysql_options = dict(
    host="172.20.10.6",
    database="ihome",
    user="root",
    password="mysql"
)

redis_options = dict(
    host="172.20.10.6",
    port=6379
)

# log_file = os.path.join(os.path.dirname(__file__),"logs/log")
log_lever = "debug"
session_expires = 68400 # session_id的有效期，单位秒
password_key = "laowangdemo" # 混淆秘钥
image_domain = 'http://ozyfrfdcg.bkt.clouddn.com/'