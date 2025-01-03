import requests
import os, time
import pandas as pd
from datetime import date, datetime, timedelta

def hasValue(value):
    if value is None:
        return False
    if type(value) == str and len(value) == 0:
        return False
    return True

def readCache(cachePath: str, cacheHours = 12) -> str:
    if not hasValue(cachePath):
        return None
    cachePath = os.path.join('cache', cachePath)
    if os.path.isfile(cachePath) and cacheHours > 0:
        cacheTime = timedelta(hours=cacheHours)
        mtime = datetime.fromtimestamp(os.path.getmtime(cachePath))
        now = datetime.now()
        # cache在有效期内，直接使用
        if now - mtime < cacheTime:
            with open(cachePath, 'r', encoding='utf-8') as f:
                return f.read()
    return None

def writeCache(cachePath, content):
    if not hasValue(cachePath):
        return
    cachePath = os.path.join('cache', cachePath)
    if type(content) is str:
        with open(cachePath, 'w', encoding='utf-8') as f:
            f.write(content)
    elif type(content) is pd.DataFrame:
        content.to_csv(cachePath, index=False)

def request(url, times = 3, timeout = 3, headers = None, cookies = None, cachePath = None, cacheHours = 12) -> str:
    cache = readCache(cachePath, cacheHours)
    if cache is not None:
        return cache
    for i in range(times):
        try:
            response = requests.get(url, timeout=timeout, headers=headers, cookies=cookies)
        except:
            time.sleep(1)
        else:
            if response.status_code == 200:
                writeCache(cachePath, response.text)
                return response.text
            else:
                continue
    return None

def ts2day(ts: float) -> int:
    day = date.fromtimestamp(ts)
    return day2int(day)

def int2day(i: int) -> date:
    return date(i // 10000, i // 100 % 100, i % 100)

def day2int(day: date) -> int:
    return day.year * 10000 + day.month * 100 + day.day

def subText(text, pre, suf, minLength = 1):
    start = text.find(pre)
    if start == -1:
        return None
    start = start + len(pre)
    end = text.find(suf, start)
    if end - start < minLength:
        return None
    return text[start:end]