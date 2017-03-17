from multiprocessing import Pool
import time
import datetime


def f(x):
    time.sleep(2)
    return x*x

if __name__ == '__main__':
    pool = Pool(processes=10)
    t1 = datetime.datetime.now()

    r = pool.map(f, range(10))
    t2 = datetime.datetime.now()
    pool.close()
    pool.join()
    print(r)
    print(t2-t1)
    # t3 = datetime.datetime.now()
    # r = list(map(f, range(5)))
    # t4 = datetime.datetime.now()
    # print(t4-t3)
    # print(r)
