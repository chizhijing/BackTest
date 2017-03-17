from deap import base, tools, creator, algorithms
import math
import random
import numpy
from Function import fn_timer
import multiprocessing


# 求解xsin(x)最大值
def my_evaluate(individual):
    # print(individual[0] * math.sin(individual[0]))
    return math.sin(individual[0]) / (individual[0]**2+1),


def my_mate(ind1, ind2):
    x1 = (ind1[0] + ind2[0])/2
    x2 = ind1[0] - ind2[0]
    ind1[0], ind2[0] = x1, x2
    return ind1, ind2


def init_value():
    return random.random()*20-10,


@fn_timer
def initial_deap():
    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()
    toolbox.register('individual', tools.initIterate, creator.Individual, init_value)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)

    toolbox.register('evaluate', my_evaluate)
    toolbox.register('mate', my_mate)
    toolbox.register('mutate', tools.mutFlipBit, indpb=0.5)
    toolbox.register('select', tools.selTournament, tournsize=3)
    #
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    pool = multiprocessing.Pool()
    toolbox.register('map', pool.map)
    return toolbox


    # pop, log = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=100,
    #                                stats=stats, halloffame=hof, verbose=True)
    # print(hof)


def test_deap(toolbox):
    pop = toolbox.population(n=10)
    hof = tools.HallOfFame(2)
    for g in range(10):
        # 选择
        offspring = toolbox.select(pop, len(pop))
        # 复制
        offspring = [toolbox.clone(ind) for ind in offspring]
        # 交叉
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.5:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        # 变异
        for mutant in offspring:
            if random.random() < 0.2:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        # 估计新个体的适应度
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        pop[:] = offspring

if __name__ == '__main__':
    tx = initial_deap()
    test_deap(tx)
