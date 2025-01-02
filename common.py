import requests
import os, sys
import pandas as pd
from datetime import datetime, timedelta

def readCache(cachePath, cacheHours = 8) -> str:
    if not cachePath:
        return None
    cachePath = os.path.join('cache', cachePath)
    if os.path.isfile(cachePath) and cacheHours > 0:
        cacheTime = timedelta(hours = cacheHours)
        mtime = datetime.fromtimestamp(os.path.getmtime(cachePath))
        now = datetime.now()
        # cache在有效期内，直接使用
        if now - mtime < cacheTime:
            with open(cachePath, 'r', encoding = 'utf-8') as f:
                return f.read()
    return None

def writeCache(cachePath, content):
    if not cachePath:
        return
    cachePath = os.path.join('cache', cachePath)
    if type(content) is str:
        with open(cachePath, 'w', encoding = 'utf-8') as f:
            f.write(content)
    elif type(content) is pd.DataFrame:
        content.to_csv(cachePath, index = False)

def request(url, times = 3, headers = None, cachePath = None, cacheHours = 8) -> str:
    cache = readCache(cachePath, cacheHours)
    if cache:
        return cache
    for i in range(times):
        try:
            response = requests.get(url, timeout = 3, headers = headers)
        except:
            pass
        else:
            writeCache(cachePath, response.text)
            return response.text
    return None

def subText(text, pre, suf, minLength = 1):
    start = text.find(pre)
    if start == -1:
        return None
    start = start + len(pre)
    end = text.find(suf, start)
    if end - start < minLength:
        return None
    return text[start:end]