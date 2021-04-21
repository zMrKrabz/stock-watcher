"""
API Spec
"""
import aiohttp
import os
import time
import urllib
from typing import TypedDict, List, Awaitable
import functools
import pandas as pd
import numpy as np
import pytz
from datetime import datetime

tz = pytz.timezone('America/New_York')

class Candle(TypedDict):
    t: int
    o: float
    h: float
    l: float
    c: float
    v: int

def convert_timeframe(timeframe: str, multiplier=1):
    # timeframe - minute, hour, day
    # multiplier - how many timeframes, ex. 4 Days
    # returns dataframe resample formatted rule
    if timeframe == "minute":
        return str(multiplier) + "T"

    if timeframe == "hour":
        return str(multiplier) + "H"

    if timeframe == "day":
        return str(multiplier) + "D"

    if timeframe == "week":
        return str(multiplier) + "W"

    if timeframe == "month":
        return str(multiplier) + "M"

def aggregate_candles(candles: pd.DataFrame, timeframe: str, multiplier=1, toDict=False) -> pd.DataFrame:
    # candles - candles from getCandles as dataframe
    # timeframe - minute, hour, day
    # multiplier - how many timeframes, ex. 4 Days
    # returns candles aggregated, with OHLCVT format
    rule = convert_timeframe(timeframe, multiplier)
    aggregated = candles.resample(rule).agg(
        {
            "t": "first",
            "o": "first",
            "h": "max",
            "l": "min",
            "c": "last",
            "v": "sum",
        }
    )
    aggregated = aggregated[aggregated["t"].notna()]

    if toDict:
        return aggregated.to_dict("records")
    return aggregated

class API:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def get_price(self, symbol: str, t=time.time()) -> Awaitable[Candle]:
        """
        symbol - Symbol to fetch price for
        t - Time to get price at, default is to get current price. In UNIX format

        return o,h,l,c,v of last bar
        """
        return

    async def get_bars(self, symbol: str, timeframe: str, multiplier: int, limit: int) -> pd.DataFrame:
        """
        symbol - Symbol of stock to get bars for
        timeframe - type of candle to get, minute, hour, day, week, month
        multiplier - how many timeframes per candle
        limit - number of candles to get
        Gets last {limit} bars, for example, getBars('AAPL', 'minute', 4, 3000) gets the last 3000 available 4 minute bars
        """
        return
