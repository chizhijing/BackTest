# -*- coding: utf-8 -*-
from scipy.stats import linregress
from dateutil.parser import parse
import datetime
from Position import *
from Order import *
import numpy as np
import talib


class Parameters(object):
    """
    策略参数
    """
    def __init__(self, parameter_dict):
        """设置参数"""
        for key in parameter_dict:
            setattr(self, key, parameter_dict[key])


class Strategy(object):
    """策略类:
        策略编号
        策略参数
    """
    pass


class StrategyArbitrage(object):
    """配对交易策略类:
        策略编号
        策略参数
    """
    BUY_SIGNAL = 1  # 套利买单信号
    SELL_SIGNAL = -1    # 套利卖单信号
    NO_ARBITRAGE_SIGNAL = 0    # 无套利信号

    TIME_TRADE1 = [parse('9:05:00').time(), parse('10:14:30').time()]
    TIME_TRADE2 = [parse('10:31:00').time(), parse('11:29:30').time()]
    TIME_TRADE3 = [parse('13:31:00').time(), parse('15:29:30').time()]
    TIME_TRADE4 = [parse('21:00:30').time(), parse('23:29:30').time()]

    DELTA_TIME = datetime.timedelta(hours=100)

    def __init__(self, strategy_id, parameter, symbol):
        """
        :param strategy_id: 策略标识
        :param parameter: 策略参数
        :param symbol:策略对应的品种
        """
        # 初始化策略信息
        self.id = strategy_id
        self.parameter = parameter
        self.symbol = symbol

        # 策略运行时的中间参数
        self.time = ''
        self.price1 = deque(maxlen=parameter.tau_cointergration)
        self.price2 = deque(maxlen=parameter.tau_cointergration)
        self.ask1 = 0
        self.ask1_volume = 0
        self.bid1 = 0
        self.bid1_volume = 0
        self.ask2 = 0
        self.ask2_volume = 0
        self.bid2 = 0
        self.bid2_volume = 0

        self.res_flag = self.NO_ARBITRAGE_SIGNAL  # 判断套利是否存在的指标
        self.position = Position()

    def update_data(self, data):
        """
        更新缓存数据
        :param data:
        :return:
        """
        if data.symbol_name == self.symbol.symbol_name[0]:
            self.ask1 = data.AskPrice
            self.ask1_volume = data.AskVolume
            self.bid1 = data.BidPrice
            self.bid1_volume = data.BidVolume
            self.price1.append(data.Price)

        else:
            self.price2.append(data.Price)
            self.ask2 = data.AskPrice
            self.ask2_volume = data.AskVolume
            self.bid2 = data.BidPrice
            self.bid2_volume = data.BidVolume
            self.price2.append(data.Price)
        self.time = data.date_time

    def cal_indicator(self):
        """
        计算指标
        :return:
        """
        price1 = np.array(self.price1)
        price2 = np.array(self.price2)
        model = linregress(price2, price1)
        sigma = np.std(price1 - price2 * model.slope - model.intercept)
        res1 = self.ask1 - self.bid2*model.slope - model.intercept
        res2 = self.bid1 - self.ask2*model.slope - model.intercept
        self.res_flag = self.BUY_SIGNAL if res1 < -self.parameter.delta_sigma * sigma else \
            self.SELL_SIGNAL if res2 > self.parameter.delta_sigma * sigma else self.NO_ARBITRAGE_SIGNAL

    def on_tick(self, data, position=None):
        """
        根据新来的数据运行策略
        :return:
        """
        # 数据更新
        self.update_data(data)
        self.position = position

        # 判断当前是否允许进行策略交易
        if not self.allow_transaction():
            return

        # 计算指标参数
        self.cal_indicator()

        # 平仓
        self.check_close_condition()

        # 开仓
        self.check_open_condition()

    def allow_transaction(self):
        # 不满足策略要求周期，不允许交易
        if len(self.price1) < self.parameter.tau_cointergration or len(
                self.price2) < self.parameter.tau_cointergration:
            return False

        # 不在共同交易时间内的不允许交易，可根据需要更改
        # time_trade1 = parse('9:05:00').time() < self.time.time() < parse('10:14:30').time()
        # time_trade2 = parse('10:31:00').time() < self.time.time() < parse('11:29:30').time()
        # time_trade3 = parse('13:31:00').time() < self.time.time() < parse('15:29:30').time()
        # time_trade4 = parse('21:00:30').time() < self.time.time() < parse('23:29:30').time()
        time_trade1 = self.TIME_TRADE1[0] < self.time.time() < self.TIME_TRADE1[1]
        time_trade2 = self.TIME_TRADE2[0] < self.time.time() < self.TIME_TRADE2[1]
        time_trade3 = self.TIME_TRADE3[0] < self.time.time() < self.TIME_TRADE3[1]
        time_trade4 = self.TIME_TRADE4[0] < self.time.time() < self.TIME_TRADE4[1]
        bool_time_trade = time_trade1 or time_trade2 or time_trade3 or time_trade4
        if not bool_time_trade:
            return False

        return True

    def check_close_condition(self):
        """
        检测是否需要平仓，如果需要平仓进行平仓相关操作：
            平仓条件检测
            仓位信息改变
                订单列表变化
            账户信息改变
                余额变化
                保证金变化
        :return:
        """
        # 仓位中属于当前的订单列表
        orders = self.position.order_set.get_orders(self.id)

        # 当前策略仓位为空,无需平仓
        if len(orders) == 0:
            return

        # 遍历当前仓位的属于该策略的所有订单
        for order in orders:
            # 更新订单信息
            if order.type == OrderPairs.ORDER_TYPE_BUY:
                order.update(close_price=[self.bid1, self.ask2], close_time=self.time)
            elif order.type == OrderPairs.ORDER_TYPE_SELL:
                order.update(close_price=[self.ask1, self.bid2], close_time=self.time)
            else:
                continue
            # 判断是否满足订单平仓条件，满足条件则进行平仓
            if self.close_condition(order):
                self.close_order(order)
                print('close order at strategy:', self.id, self.time, order.close_price, order.profit)
                print('equity:', self.position.account.equity)
            else:
                self.position.account.update(profit_increased=order.profit,
                                             margin_increased=order.margin[1]-order.margin[0],  # 当前tick和上次tick的保证金差
                                             event_type=Account.EVENT_TYPE_TICK_CHANGE)
            continue
        return

    def close_condition(self, order):
        # 盈利达到一定程度，平仓
        if order.profit > self.parameter.take_profit:
            return True
        if order.close_time - order.open_time > self.DELTA_TIME:
            return True
        return False

    def close_order(self, order):
        # 账户资金更新
        self.position.account.update(profit_increased=order.profit,
                                     margin_increased=-order.margin[0],  # 上一个tick下的保证金
                                     event_type=Account.EVENT_TYPE_CLOSE)  # 账户资金更新
        # 持仓列表更新
        self.position.order_set.remove(order)  # 仓位的订单移除

    def check_open_condition(self):
        if self.open_condition():
            if self.res_flag == self.BUY_SIGNAL:
                order = OrderPairs(open_prices=(self.ask1, self.bid2),
                                   open_time=self.time,
                                   symbols=self.symbol,
                                   lots=1,
                                   strategy_id=self.id,
                                   order_type=OrderPairs.ORDER_TYPE_BUY)   # 开多头订单
            elif self.res_flag == self.SELL_SIGNAL:
                order = OrderPairs(open_prices=(self.bid1, self.ask2),
                                   open_time=self.time,
                                   symbols=self.symbol,
                                   lots=1,
                                   strategy_id=self.id,
                                   order_type=OrderPairs.ORDER_TYPE_SELL)  # 开空头订单
            self.open_order(order)

    def open_condition(self):
        # 当前策略持仓， 不进行开仓
        if not self.position.order_set.is_empty(strategy_id=self.id):
            return False
        # 不存在套利则不开仓
        if self.res_flag == self.NO_ARBITRAGE_SIGNAL:
            return False
        return True

    def open_order(self, order):
        self.position.account.update(profit_increased=-order.commission[0],
                                     margin_increased=order.margin[0],
                                     event_type=Account.EVENT_TYPE_OPEN)
        self.position.order_set.add(order)
        print('open_order at strategy:', self.id, self.time, order.open_price)
        print('equity:', self.position.account.equity)


class StrategyBoll:
    """
    布林带寻找趋势突破
    """
    OPEN_BUY_SIGNAL = 0
    OPEN_SELL_SIGNAL = 1
    CLOSE_BUY_SIGNAL = 2
    CLOSE_SELL_SIGNAL = 3

    def __init__(self, strategy_id, parameter, symbol):
        """

        :param strategy_id:
        :param parameter:
        :param symbol:
        """
        # 初始化策略信息
        self.id = strategy_id
        self.parameter = parameter
        self.symbol = symbol
        # 策略运行中保存
        self.time = ''
        self.price = deque(maxlen=parameter.tau)
        self.flag = None
        self.position = Position()

    def update_data(self, data):
        self.price.append(data.Price)
        self.time = data.date_time

    def cal_indicator(self):
        mean = np.mean(np.array(self.price))
        sigma = np.std(np.array(self.price))
        # print(self.price)
        if self.price[-1] > mean + self.parameter.delta*sigma:  # 突破上轨,买信号
            self.flag = self.OPEN_BUY_SIGNAL
        elif self.price[-1] < mean - self.parameter.delta*sigma:   # 突破下轨，卖信号
            self.flag = self.OPEN_SELL_SIGNAL
        elif self.price[-1] < mean:     # 下穿中轨，平买信号
            self.flag = self.CLOSE_BUY_SIGNAL
        else:   # 上穿中轨，平卖信号
            self.flag = self.CLOSE_SELL_SIGNAL

    def allow_transaction(self):
        return len(self.price) >= self.parameter.tau

    def close_condition(self, order):
        if order.profit > self.parameter.take_profit:
            return True
        # if order.profit < -500:
        #     return True
        if order.cal_hold_time() > datetime.timedelta(days=self.parameter.stop_days):
            return True
        # if order.type == Order.ORDER_TYPE_BUY and \
        #         (self.flag == self.OPEN_SELL_SIGNAL or self.flag == self.CLOSE_BUY_SIGNAL):
        #     return True
        # if order.type == Order.ORDER_TYPE_SELL and \
        #         (self.flag == self.OPEN_BUY_SIGNAL or self.flag == self.CLOSE_SELL_SIGNAL):
        #     return True
        return False

    def close_order(self, order):
        self.position.account.update(profit_increased=order.profit,
                                     margin_increased=-order.margin[0],  # 上一个tick下的保证金
                                     event_type=Account.EVENT_TYPE_CLOSE)  # 账户资金更新
        # 持仓列表更新
        self.position.order_set.remove(order)  # 仓位的订单移除

    def check_close_condition(self):
        orders = self.position.order_set.get_orders(self.id)

        if len(orders) == 0:
            return

        for order in orders:
            if order.type == Order.ORDER_TYPE_BUY:
                order.update(close_price=self.price[-1]-self.symbol.slip_point, close_time=self.time)
            else:
                order.update(close_price=self.price[-1]+self.symbol.slip_point, close_time=self.time)
        if self.close_condition(order):
            self.close_order(order)
            # print('close order at strategy:', self.id, self.time, order.close_price, order.profit)
            # print('equity:', self.position.account.equity)
        else:
            self.position.account.update(profit_increased=order.profit,
                                         margin_increased=order.margin[1]-order.margin[0],  # 当前tick和上次tick的保证金差
                                         event_type=Account.EVENT_TYPE_TICK_CHANGE)

    def check_open_condition(self):
        if self.open_condition():
            if self.flag == self.OPEN_BUY_SIGNAL:
                order = Order(open_time=self.time,
                              open_price=self.price[-1]+self.symbol.slip_point,
                              symbol=self.symbol,
                              order_type=Order.ORDER_TYPE_BUY,
                              lots=1,
                              strategy_id=self.id)
            else:
                order = Order(open_time=self.time,
                              open_price=self.price[-1]-self.symbol.slip_point,
                              symbol=self.symbol,
                              order_type=Order.ORDER_TYPE_SELL,
                              lots=1,
                              strategy_id=self.id)
            self.open_order(order)

    def open_condition(self):
        if not self.position.order_set.is_empty(strategy_id=self.id):
            return False
        if self.flag == self.OPEN_BUY_SIGNAL or self.flag == self.OPEN_SELL_SIGNAL:
            return True
        return False

    def open_order(self, order):
        self.position.account.update(profit_increased=-order.commission[0],
                                     margin_increased=order.margin[0],
                                     event_type=Account.EVENT_TYPE_OPEN)
        self.position.order_set.add(order)
        # print('open_order at strategy:', self.id, self.time, order.open_price)
        # print('equity:', self.position.account.equity)

    def on_tick(self, data, position=None):
        self.update_data(data)
        self.position = position

        if not self.allow_transaction():
            return

        self.cal_indicator()

        self.check_close_condition()

        self.check_open_condition()










