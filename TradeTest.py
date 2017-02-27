# -*- coding: utf-8 -*-
import pandas as pd
from BackTest.Symbol import *
from BackTest.Function import *
from BackTest.Strategy import *
from BackTest.Position import *
import copy


class TradeTest(object):
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

    def run(self):
        for index, row in self.data.iterrows():
            # 涨跌停或异常数据不进行交易
            if row.AskPrice == 0 or row.BidPrice == 0:
                continue

            # 运行策略
            for s in self.strategy:
                s.on_tick(row, position=self.position)

                # 记录回测过程中的账户随时间的变化情况，保存为字典组成的列表
                self.account_dict.append(dict(copy.deepcopy(self.position.account.__dict__),
                                              **{'time': row.date_time}))

    def result_analysis(self):

        res_account = pd.DataFrame(self.account_dict)
        capital = res_account[['balance', 'equity']]
        capital.plot(title='Capital vs time')
        return res_account


@fn_timer
def test():
    # 读取数据
    data = pd.read_csv('F:\\Project\\czjPython\\Data\\FutureData\\Tick_i1701_rb1701.csv', nrows=10000)
    # data = pd.read_csv('merge_i_rb_1701_tick_to_minute.csv', nrows=10000)
    print(data.head())

    # 创建策略: 设置品种， 策略参数， 策略
    test_symbol_paris = SymbolPairs(('i1701-DCE', 'rb1701-SHF'))
    p_arbitrage1 = Parameters({'tau_cointergration': 100, 'delta_sigma': 2, 'take_profit': 30})
    p_arbitrage2 = Parameters({'tau_cointergration': 200, 'delta_sigma': 2, 'take_profit': 40})
    p_arbitrage3 = Parameters({'tau_cointergration': 150, 'delta_sigma': 2, 'take_profit': 50})
    p_arbitrage4 = Parameters({'tau_cointergration': 400, 'delta_sigma': 2, 'take_profit': 40})

    s1 = StrategyArbitrage(strategy_id=1, parameter=p_arbitrage1, symbol=test_symbol_paris)
    s2 = StrategyArbitrage(strategy_id=2, parameter=p_arbitrage2, symbol=test_symbol_paris)
    s3 = StrategyArbitrage(strategy_id=3, parameter=p_arbitrage3, symbol=test_symbol_paris)
    s4 = StrategyArbitrage(strategy_id=4, parameter=p_arbitrage4, symbol=test_symbol_paris)

    # 创建仓位信息
    my_account = Account(initial_capital=100000)
    my_orders = OrderList(orders=[])
    my_position = Position(order_set=my_orders, account=my_account)

    # 创建回测
    bt = TradeTest(data=data, strategy=[s1, s2, s3, s4], position=my_position)
    print('start back-test:')
    bt.run()
    print('strategies run success!')
    res = bt.result_analysis()


if __name__ == "__main__":
    test()