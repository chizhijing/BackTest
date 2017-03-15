# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from Symbol import SymbolPairs, Symbol
from Function import *
from Strategy import Parameters, StrategyArbitrage, StrategyBoll, OrderList
from Position import Position, Account
import copy
import matplotlib.pyplot as plt
import dateutil.parser


class TickTradeTest(object):
    """
    回测类
    """
    def __init__(self, data, strategy, position):
        # 初始化赋值
        self.data = data   # 回测数据流
        self.strategy = strategy    # 回测策略
        self.position = position    # 初始仓位

        # 回测中赋值
        self.account_dict = []     # 回测中的账户情况

    @fn_timer
    def run(self):
        for index, row in self.data.iterrows():
            # 涨跌停或异常数据不进行交易
            if row.AskPrice == 0 or row.BidPrice == 0:
                print('异常数据')
                continue
            if row.AskVolume == 0 or row.BidVolume == 0:
                print('涨跌停')
                continue

            # 逐个数据运行策略
            for s in self.strategy:
                # 判断数据是否和当前策略相关，相关的话触发策略
                if row.symbol_name in s.symbol.symbol_name:
                    s.on_tick(row, position=self.position)

                # 记录回测过程中的账户随时间的变化情况，保存为字典组成的列表
            self.account_dict.append(dict(copy.deepcopy(self.position.account.__dict__), **{'time': row.date_time}))
        print('equity at last:', self.position.account.equity)

    def result_analysis(self):

        res_account = pd.DataFrame(self.account_dict).set_index('time')
        res_account.to_csv('account_res.csv')
        capital = res_account[['balance', 'equity']]
        capital.plot(title='Capital vs time')
        plt.show()
        return res_account


class BarTradeTest:
    def __init__(self, data, strategy, position):
        self.data = data
        self.strategy = strategy
        self.position = position

        self.account_dict = []

    def run(self):
        for index, row in self.data.iterrows():
            for s in self.strategy:
                if row.symbol_name == s.symbol.symbol_name:
                    s.on_tick(row, position=self.position)
            self.account_dict.append(dict(copy.deepcopy(self.position.account.__dict__), **{'time': row.date_time}))
        print('equity at last:', self.position.account.equity)

    def result_analysis(self):
        res_account = pd.DataFrame(self.account_dict).set_index('time')
        res_account.to_csv('account_res.csv')
        equity_array = np.array(res_account['equity'])
        res_account['max_draw_down'] = [(equity_array[i:].min()-equity_array[i])/equity_array[i] for i in range(len(equity_array)) ]
        capital = res_account[['balance', 'equity']]
        # capital.plot(title='Capital vs time')
        print(res_account['max_draw_down'])
        # plt.plot(res_account['max_draw_down'])
        plt.figure(1)
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212)
        # plt.figure(1)
        plt.sca(ax1)
        plt.plot(capital)
        plt.sca(ax2)
        plt.plot(res_account['max_draw_down'])
        plt.show()

        return res_account


@fn_timer
def test_arbitrage():
    # 读取数据
    data = pd.read_csv('F:\\Project\\czjPython\\Data\\FutureData\\Tick_i1701_rb1701.csv', nrows=100000, parse_dates=[1])
    # data = pd.read_csv('F:\\FuturesFiles\\tick_data_flow\\i1701-DCE_rb1701-SHF_i1702-DCE_rb1702-SHF.csv')
    print(data.head())
    print('data length:', len(data))

    # 创建策略: 设置品种， 策略参数， 策略
    test_symbol_paris = SymbolPairs(('i1701-DCE', 'rb1701-SHF'))
    p_arbitrage1 = Parameters({'tau_cointergration': 500, 'delta_sigma': 3, 'take_profit': 50})
    p_arbitrage2 = Parameters({'tau_cointergration': 400, 'delta_sigma': 3, 'take_profit': 50})
    p_arbitrage3 = Parameters({'tau_cointergration': 300, 'delta_sigma': 3, 'take_profit': 50})
    p_arbitrage4 = Parameters({'tau_cointergration': 200, 'delta_sigma': 3, 'take_profit': 50})

    s1 = StrategyArbitrage(strategy_id=1, parameter=p_arbitrage1, symbol=test_symbol_paris)
    s2 = StrategyArbitrage(strategy_id=2, parameter=p_arbitrage2, symbol=test_symbol_paris)
    s3 = StrategyArbitrage(strategy_id=3, parameter=p_arbitrage3, symbol=test_symbol_paris)
    s4 = StrategyArbitrage(strategy_id=4, parameter=p_arbitrage4, symbol=test_symbol_paris)

    # 创建仓位信息
    my_account = Account(initial_capital=100000)
    my_orders = OrderList(orders=[])
    my_position = Position(order_set=my_orders, account=my_account)

    # 创建回测
    bt = TickTradeTest(data=data, strategy=[s1, s2, s3, s4], position=my_position)
    print('start back-test:')
    bt.run()
    print('strategies run success!')
    res = bt.result_analysis()


@fn_timer
def test_trend():
    data = pd.read_csv('F:\\FuturesFiles\\test_data\\rb-SHF.csv', parse_dates=[0])
    data = data.iloc[:, :]
    data['Price'] = data['Close']
    data['symbol_name'] = 'RB-MainForce'
    data = data[['symbol_name', 'date_time', 'Price']]
    print(data.head())

    symbol = Symbol('RB-MainForce')
    p1 = Parameters({'tau': 120, 'delta': 2})
    s1 = StrategyBoll(strategy_id=1, parameter=p1, symbol=symbol)
    my_account = Account(initial_capital=100000)
    my_orders = OrderList(orders=[])
    my_position = Position(order_set=my_orders, account=my_account)

    bt = BarTradeTest(data=data, strategy=[s1], position=my_position)
    print('start back_test:')
    bt.run()
    print('strategies run success!')
    res = bt.result_analysis()

if __name__ == "__main__":
    # test_arbitrage()
    test_trend()