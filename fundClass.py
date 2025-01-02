import json
from common import request, subText
from datetime import datetime, date
from fundHistory import fundHistory

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
        self.__code = code
        self.__name = name
        self.type = type

    def __str__(self) -> str:
        if len(self.managers) > 1:
            managerStr = '{}等,{}'.format(self.managers[0].name, self.managers[0].year)
        else:
            managerStr = '{},{}'.format(self.managers[0].name, self.managers[0].year)
        return '{},{},{},{},{},{},{},{},{},{},{},{},{},{}'.format(
            self.__code,
            self.__name,
            self.type,
            self.year,
            managerStr,
            self.scale, # 规模
            self.stockPercent, # 股票比例
            self.retailPercent, # 散户比例
            round(self.history.bonus(3), 2), # 3年总分红
            round(self.history.yearReturns(3), 2), # 3年总收益
            round(self.history.mean(), 2), # 3年内平均每半年收益
            round(self.history.sharpe(), 2), # 夏普比例
            round(self.history.drawdown().max, 2), # 最大回撤
            ','.join(str(round(x, 2)) for x in self.history.halfReturnsList(6)) # 6期半年收益展开
        )

    def __repr__(self) -> str:
        return '<fund({}, {})>'.format(self.__code, self.__name)

    __cachedText = None
    @property
    def __text(self):
        if not self.__cachedText:
            cachePath = 'f{}.txt'.format(self.__code)
            time = datetime.now().strftime('%Y%m%d%H%M%S')
            self.__cachedText = request('http://fund.eastmoney.com/pingzhongdata/{}.js?v={}'.format(self.__code, time), cachePath = cachePath)
        return self.__cachedText
    
    @property
    def name(self):
        return self.__name

    @property
    def code(self):
        return self.__code

    __stocks = None
    @property
    def stocks(self):
        if not self.__stocks:
            str = subText(self.__text, '/*基金持仓股票代码*/var stockCodes=', ';')
            if str:
                self.__stocks = json.loads(str)
        return self.__stocks

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
    def scale(self):
        if not self.__scale:
            str = subText(self.__text, '/*规模变动 mom-较上期环比*/var Data_fluctuationScale = ', ';')
            if str:
                dict = json.loads(str)['series'][-1]
                self.__scale = dict['y']
            else:
                self.__scale = 0
        return self.__scale

    __retailPercent = None
    @property
    def retailPercent(self):
        if not self.__retailPercent:
            str = subText(self.__text, '/*持有人结构*/var Data_holderStructure =', ';')
            if str:
                dict = json.loads(str)['series'][1]
                self.__retailPercent = dict['data'][-1]
        return self.__retailPercent

    __stockPercent = None
    @property
    def stockPercent(self):
        if not self.__stockPercent:
            str = subText(self.__text, '/*资产配置*/var Data_assetAllocation = ', ';')
            if str:
                dict = json.loads(str)['series'][0]
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

    __year = None
    @property
    def year(self):
        if not self.__year:
            str = subText(self.__text, '/*单位净值走势 equityReturn-净值回报 unitMoney-每份派送金*/var Data_netWorthTrend = ', ';', 128)
            if str:
                ts = json.loads(str)[0]['x'] / 1000
                day = date.fromtimestamp(ts)
                delta = date.today() - day
                self.__year = round(delta.days / 365, 2)
            else:
                self.__year = 0
        return self.__year

    __history = None
    @property
    def history(self):
        if not self.__history:
            str = subText(self.__text, '/*单位净值走势 equityReturn-净值回报 unitMoney-每份派送金*/var Data_netWorthTrend = ', ';', 1024)
            if str:
                self.__history = fundHistory(self.__code, str)
        return self.__history

if __name__ == '__main__':
    aFund = fund('161725', '招行白酒ETF')
    print('代码：{}'.format(aFund.code))
    print('名称：{}'.format(aFund.name))
    print('持仓：{}'.format(aFund.stocks))
    print('回报（3月，半年，1年）：{}'.format(aFund.returns))
    print('规模：{}亿'.format(aFund.scale))
    print('散户比：{}%'.format(aFund.retailPercent))
    print('股票比：{}%'.format(aFund.stockPercent))
    print('经理：{}'.format(aFund.managers))
    print('时长：{}年'.format(aFund.year))
    print('3年回报：{:.2f}%'.format(aFund.history.yearReturns(3)))