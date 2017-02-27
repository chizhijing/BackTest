import pandas as pd
import datetime


def tick_prepare(file_name='i1701-DCE.csv',
                 file_path='F:\\FuturesFiles\\tick_data\\',
                 w_path='F:\\FuturesFiles\\tick_data_prepare\\'):
    """
    将原始tick数据的时间标准化,ask,bid价格标准化,并保存至指定文件夹
    :return:
    """
    t_data = pd.read_csv(file_path+file_name, dtype={'Date': str, 'Time': str})
    t_data_copy = t_data.copy()
    t_data_copy['time_adjust'] = [time if len(time) == 9 else ((9 - len(time)) * str(0) + time) for time in
                                  t_data_copy['Time']]
    t_data_copy['date_time'] = [d + t for d, t in zip(t_data_copy['Date'], t_data_copy['time_adjust'])]

    t_data_copy['date_time'] = [datetime.datetime.strptime(str_time, '%Y%m%d%H%M%S%f') for str_time in
                                t_data_copy['date_time']]
    t_data_copy['AskPrice'] /= 10000
    t_data_copy['BidPrice'] /= 10000
    t_data_copy = t_data_copy.drop(['Date', 'Time', 'time_adjust'], axis=1)
    t_data_copy.to_csv(w_path + file_name)


def tick_merge(tick_data_list, flag_list=None):
    data_concat = pd.concat(tick_data_list, keys=flag_list)
    data_concat.index.set_names(['symbol_name', 'date_time'], inplace=True)
    data_concat = data_concat.sort_index(level='date_time')
    # data_concat.to_csv('test.csv')
    return data_concat


def get_tick_data(tick_path='F:\\FuturesFiles\\tick_data_prepare\\',
                  file_name=('i1701-DCE.csv', 'rb1701-SHF.csv')):
    data1 = pd.read_csv(tick_path + tick_file1, index_col='date_time',
                        usecols=['date_time', 'Price', 'AskPrice', 'BidPrice', 'AskVolume', 'BidVolume'])
    data2 = pd.read_csv(tick_prepare_path + tick_file2, index_col='date_time',
                        usecols=['date_time', 'Price', 'AskPrice', 'BidPrice', 'AskVolume', 'BidVolume'])
    data_merge = tick_merge([data1, data2], flag_list=file_name)
    return data_merge

if __name__ == '__main__':
    tick_origin_path = 'F:\\FuturesFiles\\tick_data\\'
    tick_prepare_path = 'F:\\FuturesFiles\\tick_data_prepare\\'
    tick_file1 = 'i1701-DCE.csv'
    tick_file2 = 'rb1701-SHF.csv'

    # tick数据的预处理
    # tick_prepare(tick_file1, file_path=tick_origin_path, w_path=tick_prepare_path)
    # tick_prepare(tick_file2, file_path=tick_origin_path, w_path=tick_prepare_path)

    # tick数据合并
    data = get_tick_data()
    data.to_csv('i1701_rb1701.csv')


