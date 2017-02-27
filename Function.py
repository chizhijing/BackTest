# -*- coding: utf-8 -*-
from functools import wraps
import datetime


def fn_timer(function):
    """
    计时装饰器
    :param function:
    :return:
    """
    @wraps(function)
    def function_timer(*args, **kwargs):
        begin_time = datetime.datetime.now()
        result = function(*args, **kwargs)
        print()
        end_time = datetime.datetime.now()
        print("Total time running %s: %s seconds" % (function.__name__, str((end_time-begin_time))))
        return result
    return function_timer
