import json
from common import request, subText
from datetime import datetime
from fundHistory import fundHistory
from fundHold import calcIndustry

def workYear(workTime):
    s = workTime.replace('天','')
    a = s.split('年又')
    try:
        if len(a) > 1:
            y = int(a[0]) + float(a[1])/366
        else:
            y = float(s)/366
    except:
        y = 0
    return round(y, 2)

class fundManager:

    def __init__(self, name, year):
        self.name = name
        self.year = year

    def __str__(self) -> str:
        return '{}({}年)'.format(self.name, self.year)

    def __repr__(self) -> str:
        return '<fundManager({}, {})>'.format(self.name, self.year)

class fund:

    def __init__(self, code, name, type = ''):
        self.code = code
        self.name = name
        self.type = type

    def __str__(self) -> str:
        if len(self.managers) > 1:
            managerStr = '{}等,{}'.format(self.managers[0].name, self.managers[0].year)
        else:
            managerStr = '{},{}'.format(self.managers[0].name, self.managers[0].year)
        if '混合型' in self.type or '股票型' in self.type:
            (totalPercent, topIndustryPercent, topIndustry) = calcIndustry(self.code)
        else:
            (totalPercent, topIndustryPercent, topIndustry) = (0, 0, 'N/A')
        return '{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}'.format(
            self.code,
            self.name,
            self.type,
            round(self.age, 2),
            managerStr,
            self.scale, # 规模
            self.stockPercent, # 股票比例
            round(totalPercent, 2), # 前十持仓占比
            topIndustry, # 最大持仓行业
            round(topIndustryPercent, 2), # 最大行业占比
            self.retailPercent, # 散户比例
            round(self.history.bonus(3), 2), # 3年总分红
            round(self.history.yearReturns(3), 2), # 3年总收益
            round(self.history.mean(), 2), # 3年内平均每半年收益
            round(self.history.sharpe(), 2), # 夏普比例
            round(self.history.drawdown().max, 2), # 最大回撤
            ','.join(str(x) for x in self.history.halfReturnsList(6)) # 6期半年收益展开
        )

    def __repr__(self) -> str:
        return '<fund({}, {})>'.format(self.name, self.code)

    __cachedText = None
    @property
    def __text(self) -> str:
        if not self.__cachedText:
            cachePath = f'f{self.code}.txt'
            time = datetime.now().strftime('%Y%m%d%H%M%S')
            self.__cachedText = request(f'http://fund.eastmoney.com/pingzhongdata/{self.code}.js?v={time}', cachePath=cachePath)
            if self.__cachedText is None:
                raise ValueError('no data')
        return self.__cachedText

    __returns = None
    @property
    def returns(self):
        if not self.__returns:
            str1y = subText(self.__text, '/*近一年收益率*/var syl_1n="', '";')
            str6m = subText(self.__text, '/*近6月收益率*/var syl_6y="', '";')
            str3m = subText(self.__text, '/*近三月收益率*/var syl_3y="', '";')
            if str1y and str3m and str6m:
                self.__returns = [float(str3m), float(str6m), float(str1y)]
        return self.__returns

    __scale = None
    @property
    def scale(self) -> float:
        if not self.__scale:
            str = subText(self.__text, '/*规模变动 mom-较上期环比*/var Data_fluctuationScale = ', ';')
            if str:
                series = json.loads(str)['series']
                if series is not None and len(series) > 0:
                    dict = series[-1]
                    self.__scale = dict['y']
            if self.__scale is None:
                raise ValueError('no data')
        return self.__scale

    __retailPercent = None
    @property
    def retailPercent(self) -> float:
        if not self.__retailPercent:
            self.__retailPercent = 0
            str = subText(self.__text, '/*持有人结构*/var Data_holderStructure =', ';')
            if str:
                series = json.loads(str)['series']
                if series is not None and len(series) > 1:
                    dict = series[1]
                    if dict['data'] is not None and len(dict['data']) > 0:
                        self.__retailPercent = dict['data'][-1]
        return self.__retailPercent

    __stockPercent = None
    @property
    def stockPercent(self) -> float:
        if not self.__stockPercent:
            self.__stockPercent = 0
            str = subText(self.__text, '/*资产配置*/var Data_assetAllocation = ', ';')
            if str:
                series = json.loads(str)['series']
                if series is not None and len(series) > 0:
                    dict = series[0]
                    if dict['data'] is not None and len(dict['data']) > 0:
                        self.__stockPercent = dict['data'][-1]
        return self.__stockPercent

    __managers = None
    @property
    def managers(self):
        if not self.__managers:
            str = subText(self.__text, '/*现任基金经理*/var Data_currentFundManager =', ';')
            if str:
                array = json.loads(str)
                self.__managers = []
                for item in array:
                    name = item['name']
                    year = workYear(item['workTime'])
                    self.__managers.append(fundManager(name, year))
        return self.__managers

    __age = None
    @property
    def age(self) -> float:
        if not self.__age:
            self.__age = self.history.age
        return self.__age

    __history = None
    @property
    def history(self) -> fundHistory:
        if not self.__history:
            str = subText(self.__text, '/*单位净值走势 equityReturn-净值回报 unitMoney-每份派送金*/var Data_netWorthTrend = ', ';', 1024)
            if str:
                self.__history = fundHistory(self.code, str)
            else:
                raise ValueError('no data')
        return self.__history

if __name__ == '__main__':
    aFund = fund('161725', '招行白酒ETF')
    print('代码：{}'.format(aFund.code))
    print('名称：{}'.format(aFund.name))
    print('回报（3月，半年，1年）：{}'.format(aFund.returns))
    print('规模：{}亿'.format(aFund.scale))
    print('散户比：{}%'.format(aFund.retailPercent))
    print('股票比：{}%'.format(aFund.stockPercent))
    print('经理：{}'.format(aFund.managers))
    print('时长：{:.2f}年'.format(aFund.age))
    print('3年回报：{:.2f}%'.format(aFund.history.yearReturns(3)))