import os, sys
import re
import numpy as np
import pandas as pd
from common import request
from datetime import date
from io import StringIO

tableRegex = re.compile("(<table class='w782 comm tzxq( t2)?'>.+?</table>)")
tbodyRegex = re.compile('<tbody>.+</tbody>')
trRegex = re.compile('<tr>.+?</tr>')
codeRegex = re.compile(r"<td><a href='//quote.eastmoney.com/[^']+'>(\d{5,6})</a></td>")
nameRegex = re.compile(r"<td class='tol'><a href='//quote.eastmoney.com/[^']+'>([^<]+)</a></td>")
percentRegex = re.compile(r"<td class='tor'>([0-9\.]+)%</td>")

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

class fundHold:
    def __init__(self, str):
        self.code = codeRegex.search(str)[1]
        self.name = nameRegex.search(str)[1]
        self.percent = percentRegex.search(str)[1]

__swsindex = None
def getIndustry(code):
    global __swsindex
    if not isinstance(__swsindex, pd.DataFrame):
        __swsindex = pd.read_csv('swsindex.csv')
    code = int(code)
    industry = __swsindex[__swsindex.code == code]
    if len(industry.index) > 0:
        industry = industry.iloc[0]
        return industry['first'] + '-' + industry['second']
    return '未知行业'

def requestHolds(code, year = None, month = None, index = 0):
    if year == None:
        year = date.today().year
    if month == None:
        month = int((date.today().month - 1) / 3) * 3
        if month == 0:
            month == 12
            year = year -1
    cachePath = 'f{}hold-{}.txt'.format(code, year)
    url = 'http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={}&topline=20&year={}&month={}'.format(code, year, month)
    response = request(url, cachePath = cachePath, cacheHours = 24 * 7)
    match = tableRegex.findall(response)[index][0]
    match = tbodyRegex.search(match)[0]
    matches = trRegex.findall(match)
    result = []
    for match in matches:
        try:
            result.append(fundHold(match))
        except:
            pass
    return result

def calcIndustry(code, year = None, month = None, index = 0, silent = True):
    csv = 'code,name,percent,industry\n'
    holds = requestHolds(code, year, month, index)
    industryDict = {}
    index = 0
    top10percent = 0
    for hold in holds:
        # 前十持仓需要统计持仓集中度
        if index < 10:
            top10percent += float(hold.percent)
        index += 1
        if len(hold.code) == 6:
            # 沪深股票计算具体的行业
            industry = getIndustry(hold.code)
            if industry in industryDict:
                industryDict[industry] += float(hold.percent)
            else:
                industryDict[industry] = float(hold.percent)
            csv += '{},{},{},{}\n'.format(hold.code, hold.name, hold.percent, industry)
        else:
            # 港股股票暂时无法区分行业，直接统一算港股
            csv += 'HK.{},{},{},{}\n'.format(hold.code, hold.name, hold.percent, '港股')
    df = pd.read_csv(StringIO(csv), dtype={'code': str})
    ratio = 100.0 / df['percent'].sum()
    groups = df.groupby(['industry'])
    csv = 'industry,percent\n'
    for name, group in groups:
        csv = csv + '{},{:.2f}\n'.format(name, group['percent'].sum() * ratio)
    dfIndustry = pd.read_csv(StringIO(csv))
    dfIndustry = dfIndustry[dfIndustry['percent'] >= 1]
    dfIndustry = dfIndustry.sort_values(by='percent', ascending=False)
    df = df.append({'name': 'top10', 'percent': round(top10percent, 2)}, ignore_index = True)
    if not silent:
        print(df)
        print(dfIndustry)
    return (df, dfIndustry)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        if len(sys.argv) >= 3:
            year = int(sys.argv[2])
        else:
            year = None
        if len(sys.argv) >= 4:
            month = int(sys.argv[3])
        else:
            month = None
        if len(sys.argv) >= 5:
            index = int(sys.argv[4])
        else:
            index = 0
        calcIndustry(sys.argv[1], year, month, index, silent = False)
    else:
        calcIndustry('005827', silent = False)
