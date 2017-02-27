# -*- coding: utf-8 -*-


class Account(object):
    """
    账户类：资金信息
    """
    EVENT_TYPE_OPEN = 1     # 开仓事件
    EVENT_TYPE_CLOSE = -1   # 平仓事件
    EVENT_TYPE_TICK_CHANGE = 0  # tick数据变动事件

    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital  # 初始资金
        self.equity = initial_capital   # 账户净值 = 已用保证金+可用保证金 = 账户余额+浮动盈亏
        self.balance = initial_capital      # 账户余额
        self.margin_used = 0    # 已用保证金
        self.margin_free = initial_capital  # 可用保证金
        self.capital_ratio = 0  # 资金使用率

    def update(self, profit_increased, margin_increased, event_type=EVENT_TYPE_TICK_CHANGE):
        if event_type == Account.EVENT_TYPE_TICK_CHANGE:
            self.equity = self.balance + profit_increased  # 账户净值根据当前的tick变化进行计算(包含平仓手续费)
        if event_type == Account.EVENT_TYPE_OPEN:
            self.balance = self.balance + profit_increased
            self.equity = self.balance
        if event_type == Account.EVENT_TYPE_CLOSE:
            self.balance = self.balance + profit_increased
            self.equity = self.balance
        self.margin_used += margin_increased
        self.margin_free = self.equity - self.margin_used
        self.capital_ratio = self.margin_used/self.equity


class Position(object):
    """
    仓位类：
        当前持仓的买卖订单集合OrderList
        当前的账户资金情况Account
    """
    def __init__(self, order_set=set(), account=None):
        self.order_set = order_set
        self.account = account


if __name__ == '__main__':
    a = Account(initial_capital=10000)
    p = Position(order_set=set(), account=a)
    print(len(p.order_set))
    print(a.balance)
    print(dict(a.__dict__, **{'tt': 1}))






