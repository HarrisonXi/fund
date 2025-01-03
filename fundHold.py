import re
import pandas as pd
from common import request

tableRegex = re.compile(r"(<table class='w782 comm tzxq'>.+?</table>)")
tbodyRegex = re.compile(r'<tbody>.+</tbody>')
trRegex = re.compile(r'<tr>.+?</tr>')
codeRegex = re.compile(r"<td><a href='//quote.eastmoney.com/[^']+'>(\d{5,6})</a></td>")
nameRegex = re.compile(r"<td class='tol'><a href='//quote.eastmoney.com/[^']+'>([^<]+)</a></td>")
percentRegex = re.compile(r"<td class='tor'>([0-9\.]+)%</td>")

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

class fundHold:
    def __init__(self, str):
        self.code = codeRegex.search(str)[1]
        self.name = nameRegex.search(str)[1]
        self.percent = float(percentRegex.search(str)[1])

__thshy = None
def getIndustry(code: str) -> str:
    global __thshy
    if __thshy is None:
        __thshy = pd.read_csv('thshy_member.csv', dtype={'code': str})
    if len(code) < 6:
        return '港股'
    industry = __thshy[__thshy.code == code]
    if industry.shape[0] > 0:
        return industry.iloc[0]['thshy']
    return '未知'

def requestHolds(code: str):
    cachePath = f'f{code}_i.txt'
    text = request(f'http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={code}&topline=10&year=&month=', cachePath=cachePath, cacheHours=30*24)
    match = tableRegex.findall(text)[0]
    match = tbodyRegex.search(match)[0]
    matches = trRegex.findall(match)
    result = []
    for match in matches:
        try:
            result.append(fundHold(match))
        except:
            pass
    return result

def calcIndustry(code: str, silent: bool = True):
    holds = requestHolds(code)
    industryDict = {}
    totalPercent = 0
    topIndustryPercent = 0
    topIndustry = None
    for hold in holds:
        totalPercent += hold.percent
        industry = getIndustry(hold.code)
        if silent == False:
            print(f'{hold.name}, {industry}, {hold.percent}%')
        if industry in industryDict:
            industryDict[industry] += hold.percent
        else:
            industryDict[industry] = hold.percent
        if industryDict[industry] > topIndustryPercent:
            topIndustryPercent = industryDict[industry]
            topIndustry = industry
    ratio = 100.0 / totalPercent
    totalPercent = round(totalPercent, 2)
    topIndustryPercent = round(topIndustryPercent * ratio, 2)
    return (totalPercent, topIndustryPercent, topIndustry)

if __name__ == '__main__':
    (totalPercent, topIndustryPercent, topIndustry) = calcIndustry('005827', silent=False)
    print('========')
    print(f'前十持仓占比: {totalPercent}%')
    print(f'最大持仓行业: {topIndustry}')
    print(f'最大行业占比: {topIndustryPercent}%')
