import os, sys
import json
import numpy as np
import pandas as pd
from common import request
from fundClass import fund
from fundHistory import day2int
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

def requestFundList():
    print('requesting fund list')
    response = request('http://fund.eastmoney.com/js/fundcode_search.js')
    array = json.loads(response[8:-1])
    df = pd.DataFrame(array)
    df['code'] = df[0]
    df['name'] = df[2]
    df['type'] = df[3]
    df = df.drop(columns = [0,1,2,3,4])
    df.to_csv('fund.csv', index = False)
    return df

def fundList():
    if os.path.isfile('fund.csv'):
        mdate = date.fromtimestamp(os.path.getmtime('fund.csv'))
        today = date.today()
        # 一个月只请求一次列表
        if mdate.year == today.year and mdate.month == today.month:
            return pd.read_csv('fund.csv', dtype = {'code': str})
    return requestFundList()

__lastMonth = None
def lastMonth():
    global __lastMonth
    if __lastMonth == None:
        day = date.today()
        day -= relativedelta(months = 1)
        __lastMonth = day2int(day)
    return __lastMonth

def filterFund(fund):
    try:
        # 规模大于3亿
        if fund.scale < 3:
            return False
        # 成立时间大于3年半
        if fund.year < 3.5:
            return False
        # 经理中有人从业3年半以上
        hit = False
        for manager in fund.managers:
            if manager.year >= 3.5:
                hit = True
                break
        if not hit:
            return False
        # 验证下是否还在运营
        if fund.history.lastDay < lastMonth():
            return False
        # 夏普比率
        if fund.history.sharpe() < 0.3:
            return False
    except:
        return False
    else:
        return True

if __name__ == '__main__':
    df = fundList()
    if len(sys.argv) == 1:
        csv = '代码,名称,类型,成立,经理,从业,规模,股票比,散户比,总分红,总收益,平均,夏普,回撤,H1,H2,H3,H4,H5,H6\n'
        for index, row in df.iterrows():
            if pd.isnull(row.type) or '混合型' not in row.type and '股票型' not in row.type:
                continue
            print('analyzing {}'.format(row.code), end='\r')
            aFund = fund(row.code, row['name'], row.type)
            if filterFund(aFund):
                try:
                    fundStr = str(aFund)
                except:
                    pass
                else:
                    csv = csv + fundStr + '\n'
        with open('result.csv', 'w', encoding = 'utf-8') as f:
            f.write('\ufeff')
            f.write(csv)
    else:
        code = sys.argv[1]
        row = df[df['code'] == code].iloc[0]
        aFund = fund(row.code, row['name'])
        print('代码：{}'.format(aFund.code))
        print('名称：{}'.format(aFund.name))
        print('时长：{}年'.format(aFund.year))
        print('经理：{}'.format(aFund.managers))
        print('规模：{}亿'.format(aFund.scale))
        print('股票比：{}%'.format(aFund.stockPercent))
        print('散户比：{}%'.format(aFund.retailPercent))
        print('总分红：{:.2f}%'.format(aFund.history.bonus(3)))
        print('总收益：{:.2f}%'.format(aFund.history.yearReturns(3)))
        print('平均：{:.2f}%'.format(aFund.history.mean()))
        print('夏普：{:.2f}'.format(aFund.history.sharpe()))
        print('回撤：{:.2f}%'.format(aFund.history.drawdown().max))
        print('6期收益：{}'.format(', '.join(str(round(x, 2)) for x in aFund.history.halfReturnsList(6))))
