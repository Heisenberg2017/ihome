# coding:utf-8
import functools
from utils.session import Session
from utils.response_code import RET


def required_login(fun):
    # 保证被装饰对象__name__不变
    @functools.wraps(fun)
    def wrapper(request_handle_obj, *args, **kwargs):
        # 调用get_current_user方法判断用户是否登陆
        if not request_handle_obj.get_current_user():
            request_handle_obj.write(dict(errcode=RET.SESSIONERR))
        else:
            fun(request_handle_obj, *args, **kwargs)
    return wrapper