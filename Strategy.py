# -*- coding: utf-8 -*-
from scipy.stats import linregress
from dateutil.parser import parse
from BackTest.Position import *
from BackTest.Order import *
import numpy as np


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
            self.time = parse(data.date_time)
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
            self.time = parse(data.date_time)
            self.bid2_volume = data.BidVolume
            self.price2.append(data.Price)

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
        time_trade1 = parse('9:05:00').time() < self.time.time() < parse('10:14:30').time()
        time_trade2 = parse('10:31:00').time() < self.time.time() < parse('11:29:30').time()
        time_trade3 = parse('13:31:00').time() < self.time.time() < parse('15:29:30').time()
        time_trade4 = parse('21:00:30').time() < self.time.time() < parse('23:29:30').time()
        bool_time_trade = time_trade1 or time_trade2 or time_trade3 or time_trade4
        if not bool_time_trade:
            return False

        # 涨跌停不允许交易,涨跌停的数据需要进一步考证:当前基于ask_volume，bid_volume的价格为0进行判断
        if self.ask1_volume == 0 or self.ask2_volume == 0 or self.bid1_volume == 0 or self.bid2_volume == 0:
            print('涨跌停:', self.time)
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
        # 仓位为空,无需平仓
        if self.position.order_set.is_empty():
            return False

        # 获取平仓订单集合
        for order in self.position.order_set.orders:  # 遍历当前策略的仓位的所有订单
            if order.strategy_id != self.id:    # 订单不对应当前策略，跳过
                continue
            # 买单平仓条件
            if order.type == OrderPairs.ORDER_TYPE_BUY:
                order.update(close_price=[self.bid1, self.ask2], close_time=self.time)  # 订单更新

                # 获利-手续费 超过给定阈值:进行平仓
                if order.profit > self.parameter.take_profit:
                    self.position.account.update(profit_increased=order.profit,
                                                 margin_increased=-order.margin[0],   # 上一个tick下的保证金
                                                 event_type=Account.EVENT_TYPE_CLOSE)     # 账户资金更新
                    self.position.order_set.remove(order)     # 仓位的订单移除
                    print('close_buy at strategy:', self.id, self.time, (self.bid1, self.ask2), order.profit)
                else:
                    self.position.account.update(profit_increased=order.profit,
                                                 margin_increased=order.margin[1]-order.margin[0],  # 当前tick和上次tick的保证金差
                                                 event_type=Account.EVENT_TYPE_TICK_CHANGE)
                continue

            # 卖单
            if order.type == OrderPairs.ORDER_TYPE_SELL:
                order.update(close_price=[self.ask1, self.bid2], close_time=self.time)    # 更新订单信息

                # 满足卖单平仓条件,进行平仓
                if order.profit > self.parameter.take_profit:
                    self.position.account.update(profit_increased=order.profit,
                                                 margin_increased=-order.margin[0],   # 平仓时，将上一次tick下的保证金释放
                                                 event_type=Account.EVENT_TYPE_CLOSE)
                    self.position.order_set.remove(order)
                    print('close_sell at strategy:', self.id, self.time, tuple(order.close_price), order.profit)
                else:
                    self.position.account.update(profit_increased=order.profit,
                                                 margin_increased=order.margin[1]-order.margin[0],
                                                 event_type=Account.EVENT_TYPE_TICK_CHANGE)
                continue
        return True

    def check_open_condition(self):
        # 当前策略持仓， 不进行开仓
        if not self.position.order_set.is_empty(strategy_id=self.id):
            return False

        # 存在套利机会则进行开仓
        if self.res_flag == self.BUY_SIGNAL:
            print('open_buy_order at strategy:', self.id, self.time, (self.ask1, self.bid2))
            open_order = OrderPairs(open_prices=(self.ask1, self.bid2),
                                    open_time=self.time,
                                    symbols=self.symbol,
                                    lots=1,
                                    strategy_id=self.id,
                                    order_type=OrderPairs.ORDER_TYPE_BUY)   # 开多头订单

            self.position.account.update(profit_increased=-open_order.commission[0],
                                         margin_increased=open_order.margin[0],
                                         event_type=Account.EVENT_TYPE_OPEN)
            self.position.order_set.add(open_order)

        if self.res_flag == self.SELL_SIGNAL:
            print('open_sell_order at strategy:', self.id, self.time, (self.bid1, self.ask2))
            open_order = OrderPairs(open_prices=(self.bid1, self.ask2),
                                    open_time=self.time,
                                    symbols=self.symbol,
                                    lots=1,
                                    strategy_id=self.id,
                                    order_type=OrderPairs.ORDER_TYPE_SELL)  # 开空头订单
            self.position.account.update(profit_increased=-open_order.commission[0],
                                         margin_increased=open_order.margin[0],
                                         event_type=Account.EVENT_TYPE_OPEN)
            self.position.order_set.add(open_order)
        return True











