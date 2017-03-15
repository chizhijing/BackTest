import pandas as pd
from Symbol import Symbol
from Strategy import Parameters, StrategyBoll, Account, OrderList
from Position import Position
from TradeTest import BarTradeTest
from deap import base, creator, tools


def my_evaluate(individual):
    tau = individual[0]
    delta = individual[1]
    take_profit = individual[2]
    stop_days = individual[3]
    data = individual[4]
    symbol = individual[5]

    p1 = Parameters({'tau': tau, 'delta': delta, 'take_profit': take_profit, 'stop_days': stop_days})
    s = StrategyBoll(strategy_id=1, parameter=p1, symbol=symbol)
    my_position = Position(order_set=OrderList(orders=[]), account=Account(initial_capital=100000))
    bt = BarTradeTest(data=data, strategy=[s], position=my_position)
    print(bt.account_dict[-1].get('equity'))
    return bt.account_dict[-1].get('equity'),


def deap_run():
    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', set, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register('evaluate', my_evaluate)
    toolbox.register('mate', tools.cxTwoPoint)
    toolbox.register('mutate', tools.mutFlipBit)
    toolbox.register('select', tools.selTournament)

    toolbox.register('individual', )


def test():
    data = pd.read_csv('F:\\FuturesFiles\\test_data\\rb-SHF.csv', parse_dates=[0])
    data = data.iloc[:10000, :]
    data['Price'] = data['Close']
    data['symbol_name'] = 'RB-MainForce'
    data = data[['symbol_name', 'date_time', 'Price']]
    symbol = Symbol('RB-MainForce')
    deap_run()

if __name__ == '__main__':
    test()
