# -*- coding: utf-8 -*-
import numpy as np
from collections import deque
from collections import Counter


class Order:
    ORDER_TYPE_BUY = 1
    ORDER_TYPE_SELL = -1

    def __init__(self, open_time, open_price, symbol, order_type, lots=1, strategy_id=1):
        # 订单开仓时候赋值
        self.symbol = symbol  # 订单对应的品种
        self.open_time = open_time  # 订单时间
        self.open_price = open_price  # 订单开仓价格
        self.close_price = None   # 平仓价格
        self.close_time = None    # 平仓时间
        self.strategy_id = strategy_id  # 订单对应的策略id
        self.type = order_type  # 订单类型
        self.lots = lots  # 订单手数

        # 持仓过程或平仓时候赋值
        self.tons = lots * self.symbol.invest_level * self.symbol.tons_per_lots  # 订单对应的吨数
        self.commission = [0, 0]      # 存放开平仓手续费
        self.margin = deque(maxlen=2)  # 存放订单所需保证金队列:上一时刻和当前时刻
        self.cal_order_commission('OpenPrice')  # 订单手续费
        self.cal_order_margin('OpenPrice')      # 保证金开始时以开仓价计算

        self.profit = 0   # 订单获利
        self.is_closed = False  # 当确定订单平仓时，设置True

    def cal_order_margin(self, margin_type='ClosePrice'):
        """
        根据开仓/平仓价格计算订单保证金：（与实际情况稍微不同，实际情况可能以成交价进行）
        :param margin_type:'ClosePrice', 'OpenPrice';
        :return:
        """
        if margin_type == 'ClosePrice':
            order_margin = self.tons * self.close_price * self.symbol.leverage
            self.margin.append(order_margin)
            return

        if margin_type == 'OpenPrice':
            order_margin = self.tons * self.open_price * self.symbol.leverage
            self.margin.append(order_margin)
            return

    def cal_order_commission(self, commission_type='ClosePrice'):
        """
        根据开仓/平仓价格计算手续费
        :param commission_type:'ClosePrice','OpenPrice'
        :return:
        """
        if commission_type == 'OpenPrice':
            commission = self.tons * self.open_price * self.symbol.commission_ratio
            self.commission[0] = commission

        if commission_type == 'ClosePrice':
            commission = self.tons * self.close_price * self.symbol.commission_ratio
            self.commission[1] = commission
            # return commission

    def cal_order_profit(self):
        # 订单获利计算，扣除了开/平仓手续费
        # self.order_profit = sum(self.order_tons * points_win) - sum(self.order_commission)

        # 订单获利计算，只扣除平仓价格--方便账户更新时候计算(开仓时账户已经扣除了手续费)
        # 计算点差
        point_change = self.open_price - self.close_price
        if self.type == Order.ORDER_TYPE_SELL:
            self.profit = self.tons * point_change - self.commission[1]
        else:
            self.profit = self.tons * (-point_change) - self.commission[1]

    def cal_hold_time(self):
        return self.close_time - self.open_time

    def update(self, close_price, close_time):
        """
        根据平仓价格/平仓时间进行，订单信息的更新
            订单平仓价格，平仓时间，平仓获利
        :param close_price:
        :param close_time:
        :return:
        """
        # 设置平仓价格
        self.close_price = np.array(close_price)
        self.close_time = close_time

        # 计算手续费
        self.cal_order_commission()

        # 计算获利
        self.cal_order_profit()

        # 计算保证金
        self.cal_order_margin()


class OrderPairs(object):
    """
    订单类 --> 配对订单类
    """
    ORDER_TYPE_BUY = 1
    ORDER_TYPE_SELL = -1

    def __init__(self, open_time, open_prices, symbols, order_type, lots=1, strategy_id=1):
        # 订单开仓时候赋值
        self.symbol = symbols  # 订单对应的品种SymbolPairs
        self.open_time = open_time  # 订单时间
        self.open_price = np.array(open_prices)  # 订单开仓价格
        self.close_price = None   # 平仓价格
        self.close_time = None    # 平仓时间
        self.strategy_id = strategy_id  # 订单对应的策略id
        self.type = order_type  # 订单类型
        self.lots = lots  # 订单手数：是SymbolPairs投资比例的倍数

        # 持仓过程或平仓时候赋值
        self.tons = lots * np.array(self.symbol.invest_level) * np.array(self.symbol.tons_per_lots)  # 订单对应的吨数
        self.commission = [0, 0]      # 存放开平仓手续费
        self.margin = deque(maxlen=2)  # 存放订单所需保证金队列:上一时刻和当前时刻
        self.cal_order_commission('OpenPrice')  # 订单手续费
        self.cal_order_margin('OpenPrice')      # 保证金开始时以开仓价计算

        self.profit = 0   # 订单获利
        self.is_closed = False  # 当确定订单平仓时，设置True

    def cal_order_margin(self, margin_type='ClosePrice'):
        """
        根据开仓/平仓价格计算订单保证金：（与实际情况稍微不同，实际情况可能以成交价进行）
        :param margin_type:'ClosePrice', 'OpenPrice';
        :return:
        """
        if margin_type == 'ClosePrice':
            order_margin = np.array(self.tons) * \
                                np.array(self.close_price) * \
                                np.array(self.symbol.leverage)
            self.margin.append(sum(order_margin))
            return

        if margin_type == 'OpenPrice':
            order_margin = np.array(self.tons) * \
                                np.array(self.open_price) * \
                                np.array(self.symbol.leverage)
            self.margin.append(sum(order_margin))
            return

    def cal_order_commission(self, commission_type='ClosePrice'):
        """
        根据开仓/平仓价格计算手续费
        :param commission_type:'ClosePrice','OpenPrice'
        :return:
        """
        if commission_type == 'OpenPrice':
            commission = sum(np.array(self.tons)
                             * np.array(self.open_price)
                             * np.array(self.symbol.commission_ratio))
            self.commission[0] = commission

        if commission_type == 'ClosePrice':
            commission = sum(np.array(self.tons)
                             * np.array(self.close_price)
                             * np.array(self.symbol.commission_ratio))
            self.commission[1] = commission
            # return commission

    def cal_order_profit(self):
        # 订单获利计算，扣除了开/平仓手续费
        # self.order_profit = sum(self.order_tons * points_win) - sum(self.order_commission)

        # 订单获利计算，只扣除平仓价格--方便账户更新时候计算(开仓时账户已经扣除了手续费)
        # 计算点差
        point_change = self.open_price - self.close_price
        if self.type == OrderPairs.ORDER_TYPE_SELL:
            point_win = np.array([point_change[0], - point_change[1]])
        else:
            point_win = np.array([-point_change[0], point_change[1]])

        self.profit = sum(self.tons * point_win) - self.commission[1]

    def update(self, close_price, close_time):
        """
        根据平仓价格/平仓时间进行，订单信息的更新
            订单平仓价格，平仓时间，平仓获利
        :param close_price:
        :param close_time:
        :return:
        """
        # 设置平仓价格
        self.close_price = np.array(close_price)
        self.close_time = close_time

        # 计算手续费
        self.cal_order_commission()

        # 计算获利
        self.cal_order_profit()

        # 计算保证金
        self.cal_order_margin()


class OrderList:
    """
    持仓列表
    """
    def __init__(self, orders):
        self.orders = list(orders)

    def add(self, new_order):
        self.orders.append(new_order)

    def remove(self, del_order):
        self.orders.remove(del_order)

    def is_empty(self, strategy_id='all'):
        """
        判断仓位是否为空
        :param strategy_id:'all', [1,2,3]
        :return:
        """
        if strategy_id == 'all':
            return True if len(self.orders) == 0 else False
        else:
            return True if len(self.get_orders(strategy_id)) == 0 else False

    def get_orders(self, strategy_id):
        """
        返回给定对应策略id的订单列表
        :param strategy_id:
        :return:
        """
        orders = []
        for order in self.orders:
            if type(strategy_id) == list:   # 计算多个策略的订单持仓
                if order.strategy_id in strategy_id:
                    orders.append(order)
            else:   # 计算单个策略的订单持仓
                if order.strategy_id == strategy_id:
                    orders.append(order)
        return orders
