# -*- coding: utf-8 -*-
class Symbol(object):
    """
    品种类
    """
    def __init__(self, symbol='rb1701-SHF'):
        self.symbol_name = symbol
        self.MinLots = 1  # 最小手数
        self.MaxLots = 100  # 最大手数
        self.leverage = 0.2  # 保证金比例
        self.commission_ratio = 0.00025  # 手续费
        self.invest_level = 1  # 固定比例投资比例或手数
        self.tons_per_lots = 20  # 每手对应的吨数，价格序列对应的是一吨的
        self.slip_point = 1


class SymbolPairs(object):
    """
    配对品种类
    """
    def __init__(self, symbol=('i1701-DCE', 'rb1701-SHF')):
        self.symbol_name = symbol
        self.MinLots = (1, 1)  # 最小手数
        self.MaxLots = (100, 100)  # 最大手数
        self.leverage = (0.2, 0.2)  # 保证金比例
        self.commission_ratio = (0.0003, 0.0001)  # 手续费
        self.invest_level = (1, 2)  # 固定比例投资比例或手数，在cal_order_list中使用
        self.tons_per_lots = (100, 20)  # 每手对应的吨数，价格序列对应的是一吨的

