import sys, json
import pandas as pd
from common import request, readCache, writeCache, hasValue
from io import StringIO
from fundClass import fund
from fundHistory import day2int
from datetime import date
from dateutil.relativedelta import relativedelta
from fundHold import calcIndustry

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

def fundList():
    cache = readCache('fundList.csv', cacheHours=30*24)
    if cache is not None:
        df = pd.read_csv(StringIO(cache), dtype={'code': str})
    else:
        print('requesting fund list')
        r = request('http://fund.eastmoney.com/js/fundcode_search.js')
        array = json.loads(r[8:-1])
        df = pd.DataFrame(array)
        df['code'] = df[0]
        df['name'] = df[2]
        df['type'] = df[3]
        df = df.drop(columns = [0,1,2,3,4])
        writeCache('fundList.csv', df)
    return df.reset_index(drop=True)

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
        if fund.age < 3.5:
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
        # 3年亏损不能超过20%
        if fund.history.yearReturns(3) <= -20:
            return False
        # 可以成功输出文本
        if not hasValue(str(fund)):
            return False
    except ValueError as e:
        if e.args[0] in ['no data']:
            return False
        else:
            raise e
    else:
        return True

if __name__ == '__main__':
    df = fundList()
    if len(sys.argv) == 1:
        csv = '代码,名称,类型,运行时长,经理,从业时长,规模,股票比,前十持仓占比,最大持仓行业,最大行业占比,散户比,3年总分红,3年总收益,半年平均,半年夏普,最大回撤,H1,H2,H3,H4,H5,H6\n'
        for index, row in df.iterrows():
            if pd.isna(row.type) or '混合型' not in row.type and '股票型' not in row.type and 'FOF' not in row.type:
                continue
            print(f'analyzing {row.code}', end='\r')
            aFund = fund(row.code, row['name'], row.type)
            if filterFund(aFund):
                csv = csv + str(aFund) + '\n'
        with open('result.csv', 'w', encoding='utf-8') as f:
            f.write('\ufeff')
            f.write(csv)
    else:
        code = sys.argv[1]
        row = df[df['code'] == code].iloc[0]
        aFund = fund(row.code, row['name'], row.type)
        print('代码：{}'.format(aFund.code))
        print('名称：{}'.format(aFund.name))
        print('类型：{}'.format(aFund.type))
        print('运行时长：{:.2f}年'.format(aFund.age))
        print('经理：{}'.format(aFund.managers))
        print('规模：{}亿'.format(aFund.scale))
        print('股票比：{}%'.format(aFund.stockPercent))
        if '混合型' in row.type or '股票型' in row.type:
            (totalPercent, topIndustryPercent, topIndustry) = calcIndustry(code)
        else:
            (totalPercent, topIndustryPercent, topIndustry) = (0, 0, 'N/A')
        print(f'前十持仓占比: {totalPercent}%')
        print(f'最大持仓行业: {topIndustry}')
        print(f'最大行业占比: {topIndustryPercent}%')
        print('散户比：{}%'.format(aFund.retailPercent))
        print('3年总分红：{:.2f}%'.format(aFund.history.bonus(3)))
        print('3年总收益：{:.2f}%'.format(aFund.history.yearReturns(3)))
        print('半年平均：{:.2f}%'.format(aFund.history.mean()))
        print('半年夏普：{:.2f}'.format(aFund.history.sharpe()))
        print('最大回撤：{:.2f}%'.format(aFund.history.drawdown().max))
        print('6期收益：{}'.format(', '.join(str(x) for x in aFund.history.halfReturnsList(6))))
