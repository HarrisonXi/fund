这是一个爬取东财-天天基金网数据制作基金数据表的脚本

爬取所有符合条件的基金生成表格`result.csv`：

```
python3 fund.py
```

爬取单个基金输出关键内容，示例：

```
python fund.py 000979
>>>> 输出 >>>>
代码：000979
名称：景顺长城沪港深精选股票A
类型：股票型
运行时长：9.76年
经理：[<fundManager(鲍无可, 10.56)>]
规模：62.6亿
股票比：83.75%
前十持仓占比: 48.66%
最大持仓行业: 港股
最大行业占比: 39.66%
散户比：45.01%
3年总分红：0.00%
3年总收益：35.21%
半年平均：5.53%
半年夏普：0.62
最大回撤：14.71%
6期收益：-2.98, 8.82, 13.21, -0.78, 19.6, -4.68
```

python 3.11测试通过。
