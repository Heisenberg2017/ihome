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
    host="127.0.0.1",
    database="ihome",
    user="root",
    password="newpass"
)

redis_options = dict(
    host="127.0.0.1",
    port=6379
)

# log_file = os.path.join(os.path.dirname(__file__),"logs/log")
log_lever = "debug"
session_expires = 68400 # session_id的有效期，单位秒