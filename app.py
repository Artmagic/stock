import requests
import datetime as dt
import time
import pandas as pd
import numpy as np
import akshare as ak

from flask import Flask

# from apscheduler.schedulers.blocking import BlockingScheduler
# 大盘实时数据
# 小熊api https://api.doctorxiong.club/v1/stock/board

app = Flask(__name__)


@app.route('/get_board')
def get_board():
    get_board_url = 'https://api.doctorxiong.club/v1/stock/board?token=W9hJ3pzvKU'
    get_hot_stock_url = 'https://api.doctorxiong.club/v1/stock/hot?token=W9hJ3pzvKU'

    board = requests.get(get_board_url)
    hot_stock = requests.get(get_hot_stock_url)

    board_list = board.json()['data']
    hot_stock_list = hot_stock.json()['data']

    board_message = '大盘实时数据：' + '\n'
    for board_item in board_list:
        board_item['changePercent'] = board_item['changePercent'] + '%'
        board_item['turnover'] = str('%.2f' % (int(board_item['turnover']) / 10000)) + '亿'
        message = board_item['name'] + '（' + board_item['changePercent'] + '）' + '：' \
                  + board_item['price'] + '，' + "成交金额：" + board_item['turnover'] + '\n'
        board_message = board_message + message

    hot_stock_message = '个股成交量排行：' + '\n'
    for hot_stock_item in hot_stock_list:
        hot_stock_item['changePercent'] = hot_stock_item['changePercent'] + '%'
        hot_stock_item['turnover'] = str('%.2f' % (int(hot_stock_item['turnover']) / 10000)) + '亿'
        message = hot_stock_item['name'] + '（' + hot_stock_item['changePercent'] + '）' + '：' \
                  + hot_stock_item['price'] + '，' + "成交金额：" + hot_stock_item['turnover'] + '\n'
        hot_stock_message = hot_stock_message + message
        content = board_message + '\n' + hot_stock_message
    return content
# 北向资金


@app.route('/get_realtime_money_flow')
def get_realtime_money_flow():
    current_time = time.strftime("%-H:%M", time.localtime())

    realtime_flow_url = 'http://push2.eastmoney.com/api/qt/kamt.rtmin/get?fields1=f1,f3&fields2=f51,f52,f54,f56'
    ret = requests.get(realtime_flow_url)

    if not ret.ok:
        raise Exception('请求实时资金流向失败！')

    data = ret.json()['data']

    _date = dt.datetime(dt.datetime.today().year, *map(int, data['s2nDate'].split('-')))

    df = pd.DataFrame(map(lambda v: v.split(','), data['s2n']), columns=['time', 'hk2sh', 'hk2sz', 's2n']).\
        set_index('time').replace('-', np.nan).dropna().astype(float)

    nouth_message = '北向资金实时流入：' + '\n' + '总流入：' + str('%.2f' % (df.loc[current_time, 's2n'] / 10000)) + '亿，' + '流向沪市：' \
                    + str('%.2f' % (df.loc[current_time, 'hk2sh'] / 10000)) + '亿，' + '\n' + '流向深市：' + str('%.2f' % (df.loc[current_time, 'hk2sz'] / 10000)) + '亿'
    return nouth_message


# 个股资金实时流入前10
@app.route('/get_stock_individual_fund_flow_rank')
def get_stock_individual_fund_flow_rank():
    stock_individual_fund_flow_rank_df = ak.stock_individual_fund_flow_rank(indicator="今日").head(10)

    stock_individual_fund_flow_rank_message = '个股实时资金流入排行：' + '\n\n'
    for index, row in stock_individual_fund_flow_rank_df.iterrows():
        message = row["名称"] + '（' + str(row["涨跌幅"]) + '%）' + '：' \
                  + '净流入-净额:' + str('%.2f' % (row["主力净流入-净额"]/100000000)) + '亿，' + '\n'
        stock_individual_fund_flow_rank_message = stock_individual_fund_flow_rank_message + message
    return stock_individual_fund_flow_rank_message

# 行业资金实时流入前10


@app.route('/get_stock_sector_fund_flow_rank')
def get_stock_sector_fund_flow_rank():
    stock_sector_fund_flow_rank_df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流").head(20)
    print(stock_sector_fund_flow_rank_df)

    stock_sector_fund_flow_rank_df_message = '行业板块实时资金流入排行：' + '\n\n'

    for index, row in stock_sector_fund_flow_rank_df.iterrows():
        message = row["名称"] + '（' + str(row["今日涨跌幅"]) + '%）' + '：' \
                  + '净流入:' + str('%.2f' % (row["今日主力净流入-净额"]/100000000)) + '亿，' \
                  + '（' + "流入最大股：" + str(row["今日主力净流入最大股"]) + '）' + '\n\n'
        stock_sector_fund_flow_rank_df_message = stock_sector_fund_flow_rank_df_message + message
    return get_stock_sector_fund_flow_rank


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8088)