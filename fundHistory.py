import json
import pandas as pd
import numpy as np
from common import subText, readCache, request, writeCache, day2int, int2day, ts2day
from fundDrawdown import fundDrawdown
from datetime import date
from dateutil.relativedelta import relativedelta
from io import StringIO

# 把分红和拆分处理成比率，红利再投资，用于计算累计收益
def ratioForm(x) -> float:
    t = x['unitMoney']
    if len(t) > 0:
        st = subText(t, '分红：每份派现金', '元')
        if st:
            return float(st) / float(x['y']) + 1
        st = subText(t, '拆分：每份基金份额折算', '份')
        if st:
            return float(st)
        st = subText(t, '每份基金份额分拆', '份')
        if st:
            return float(st)
        raise Exception(t)
    return 1.0

# 只处理分红，无视拆分，用于计算累计分红率用
def bonusFrom(x) -> float:
    t = x['unitMoney']
    if len(t) > 0:
        st = subText(t, '分红：每份派现金', '元')
        if st:
            return float(st) / float(x['y'])
        st = subText(t, '拆分：每份基金份额折算', '份')
        if st:
            return 0.0
        st = subText(t, '每份基金份额分拆', '份')
        if st:
            return 0.0
        raise Exception(t)
    return 0.0

class fundHistory:
    
    # {"x":1433692800000,"y":1.038,"equityReturn":2.5692,"unitMoney":""}
    def __init__(self, code, str):
        cachePath = f'f{code}.csv'
        cache = readCache(cachePath)
        if cache is not None:
            df = pd.read_csv(StringIO(cache), dtype={'date': int})
        else:
            array = json.loads(str)
            df = pd.DataFrame(array)
            df['date'] = df.apply(lambda x: ts2day(x['x'] / 1000), axis=1)
            df['tValue'] = df['y']
            df['tRatio'] = df.apply(ratioForm, axis = 1)
            df['tBonus'] = df.apply(bonusFrom, axis = 1)
            df['ratio'] = df['tRatio'].cumprod()
            df['bonus'] = df['tBonus'].cumsum()
            df['value'] = df.apply(lambda x: x['tValue'] * x['ratio'], axis = 1)
            df = df.drop(columns = ['x', 'y', 'equityReturn', 'unitMoney', 'tValue', 'tRatio', 'tBonus'])
            writeCache(cachePath, df)
        self.__df = df.reset_index(drop=True)
    
    @property
    def age(self) -> float:
        df = self.__df
        day = int2day(df.date.iloc[0])
        delta = date.today() - day
        return delta.days / 365.0

    @property
    def lastDay(self) -> int:
        df = self.__df
        return df.date.iloc[-1]

    # 年度累计分红
    # y: 统计y年的分红
    def bonus(self, y = 1) -> float:
        df = self.__df
        day = int2day(df.date.iloc[-1])
        day -= relativedelta(years = y)
        dInt = day2int(day)
        start = df[df.date <= dInt].iloc[-1].bonus
        end = df.iloc[-1].bonus
        return (end - start) * 100

    # 年度回报
    # y: 统计y年的回报
    def yearReturns(self, y = 1) -> float:
        df = self.__df
        day = int2day(df.date.iloc[-1])
        day -= relativedelta(years = y)
        dInt = day2int(day)
        start = df[df.date <= dInt].iloc[-1].value
        end = df.iloc[-1].value
        return (end / start - 1) * 100

    # 月度回报
    # m: 统计m月的回报
    def monthReturns(self, m = 1) -> float:
        df = self.__df
        day = int2day(df.date.iloc[-1])
        day -= relativedelta(months = m)
        dInt = day2int(day)
        start = df[df.date <= dInt].iloc[-1].value
        end = df.iloc[-1].value
        return (end / start - 1) * 100

    # 近期季度回报列表
    # count: 统计几个季度
    def seasonReturnsList(self, count = 4):
        df = self.__df
        day = int2day(df.date.iloc[-1])
        result = []
        for i in range(count):
            end = df.iloc[-1].value
            startDay = day - relativedelta(months = 3)
            dInt = day2int(startDay)
            df = df[df.date <= dInt]
            start = df.iloc[-1].value
            result.insert(0, round((end / start - 1) * 100, 2))
            day = startDay
        return result
    
    # 近期半年回报列表
    # count: 统计几个半年
    def halfReturnsList(self, count = 4):
        df = self.__df
        day = int2day(df.date.iloc[-1])
        result = []
        for i in range(count):
            end = df.iloc[-1].value
            startDay = day - relativedelta(months = 6)
            dInt = day2int(startDay)
            df = df[df.date <= dInt]
            start = df.iloc[-1].value
            result.insert(0, round((end / start - 1) * 100, 2))
            day = startDay
        return result

    # 近期年度回报列表
    # count: 统计几个年度
    def yearReturnList(self, count = 3):
        df = self.__df
        day = int2day(df.date.iloc[-1])
        result = []
        for i in range(count):
            end = df.iloc[-1].value
            startDay = day - relativedelta(years = 1)
            dInt = day2int(startDay)
            df = df[df.date <= dInt]
            start = df.iloc[-1].value
            result.insert(0, round((end / start - 1) * 100, 2))
            day = startDay
        return result
    
    # 近期收益平均数
    # count: 统计几个半年，默认并建议3年
    def mean(self, count = 6) -> float:
        returns = self.halfReturnsList(count)
        return np.mean(returns)

    # 近期夏普比率
    # count: 统计几个半年，默认并建议3年
    def sharpe(self, count = 6) -> float:
        returns = self.halfReturnsList(count)
        return np.mean(returns) / np.std(returns)
    
    # 近期最大回撤
    # count: 统计几个半年，默认并建议3年
    def drawdown(self, count = 6) -> fundDrawdown:
        df = self.__df
        day = int2day(df.date.iloc[-1])
        day -= relativedelta(months = count * 6)
        dInt = day2int(day)
        df = df[df.date >= dInt]
        return fundDrawdown(df)

if __name__ == '__main__':
    text = request('http://fund.eastmoney.com/pingzhongdata/100032.js', cachePath='f100032.txt')
    str = subText(text, '/*单位净值走势 equityReturn-净值回报 unitMoney-每份派送金*/var Data_netWorthTrend = ', ';', 1024)
    history = fundHistory('100032', str)
    print('时长：{:.2f}年'.format(history.age))
    print('分红：{:.2f}%'.format(history.bonus()))
    print('3月：{:.2f}%'.format(history.monthReturns(3)))
    print('半年：{:.2f}%'.format(history.monthReturns(6)))
    print('1年：{:.2f}%'.format(history.yearReturns(1)))
    print('3年：{:.2f}%'.format(history.yearReturns(3)))
    print('季度：{}'.format(history.seasonReturnsList(4)))
    print('半年：{}'.format(history.halfReturnsList(6)))
    print('年度：{}'.format(history.yearReturnList(3)))
    print('夏普：{:.2f}'.format(history.sharpe()))
    drawdown = history.drawdown()
    print('最大回撤：{:.2f}'.format(drawdown.max))
    print('回撤95分位：{:.2f}'.format(drawdown.quantile95))
    print('回撤9分位：{:.2f}'.format(drawdown.quantile9))
