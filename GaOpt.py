import pandas as pd
import numpy as np
import random
from Function import fn_timer
from Symbol import Symbol
from Strategy import Parameters, StrategyBoll, Account, OrderList
from Position import Position
from TradeTest import BarTradeTest
from deap import base, creator, tools, algorithms
import multiprocessing
from scoop import futures


def my_evaluate(data, symbol, individual):
    toolbox.register('map', pool.map)
    # print(individual)
    tau = individual[0]
    delta = individual[1]
    take_profit = individual[2]
    stop_days = individual[3]

    p1 = Parameters({'tau': tau, 'delta': delta, 'take_profit': take_profit, 'stop_days': stop_days})
    s = StrategyBoll(strategy_id=1, parameter=p1, symbol=symbol)
    my_position = Position(order_set=OrderList(orders=[]), account=Account(initial_capital=100000))
    bt = BarTradeTest(data=data, strategy=[s], position=my_position)
    bt.run()

    return bt.account_dict[-1].get('equity'),


def generate_parameters():
    tau = random.choice([60, 70, 80, 90, 100, 110, 120])
    sigma = random.choice([1.0, 1.5, 2.0, 2.5, 3.0])
    take_profit = random.choice(list(range(50, 10000, 50)))
    stop_days = random.randint(3, 14)
    return [tau, sigma, take_profit, stop_days]


def my_mut_function(individual, indpb):
    if random.random() < indpb:
        individual[0] = random.choice(list(range(60, 420, 30)))
    if random.random() < indpb:
        individual[1] = random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
    if random.random() < indpb:
        individual[2] = random.choice(list(range(50, 10000, 50)))
    if random.random() < indpb:
        individual[3] = random.randint(3, 14)
    return individual,


@fn_timer
def test():
    data = pd.read_csv('F:\\FuturesFiles\\test_data\\rb-SHF.csv', nrows=50000, parse_dates=[0])
    # data = data.iloc[:50000, :]
    data['Price'] = data['Close']
    data['symbol_name'] = 'RB-MainForce'
    data = data[['symbol_name', 'date_time', 'Price']]
    symbol = Symbol('RB-MainForce')

    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register('evaluate', my_evaluate, data, symbol)
    toolbox.register('mate', tools.cxOnePoint)
    toolbox.register('mutate', my_mut_function, indpb=0.2)
    toolbox.register('select', tools.selTournament, tournsize=3)

    toolbox.register('individual', tools.initIterate, creator.Individual, generate_parameters)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)


    # choose_num = 20
    # child_generate_num = 100
    pop = toolbox.population(20)

    CXPB, MUTPB, NGEN = 0.5, 0.2, 10

    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=CXPB, mutpb=MUTPB, ngen=NGEN,
                                   stats=stats, halloffame=hof, verbose=True)
    print(hof)
    return pop, log, hof


if __name__ == '__main__':
    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)
    pool = multiprocessing.Pool()
    toolbox = base.Toolbox()

    # toolbox.register('map', futures.map)
    data = pd.read_csv('F:\\FuturesFiles\\test_data\\rb-SHF.csv', nrows=5000, parse_dates=[0])
    # data = data.iloc[:50000, :]
    data['Price'] = data['Close']
    data['symbol_name'] = 'RB-MainForce'
    data = data[['symbol_name', 'date_time', 'Price']]
    symbol = Symbol('RB-MainForce')

    toolbox.register('evaluate', my_evaluate, data, symbol)

    toolbox.register('mate', tools.cxOnePoint)
    toolbox.register('mutate', my_mut_function, indpb=0.2)
    toolbox.register('select', tools.selTournament, tournsize=3)

    toolbox.register('individual', tools.initIterate, creator.Individual, generate_parameters)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)


    # choose_num = 20
    # child_generate_num = 100
    pop = toolbox.population(20)

    CXPB, MUTPB, NGEN = 0.5, 0.2, 10

    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=CXPB, mutpb=MUTPB, ngen=NGEN,
                                   stats=stats, halloffame=hof, verbose=True)

    print(hof)
