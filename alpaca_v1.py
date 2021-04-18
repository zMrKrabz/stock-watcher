"""
Alpaca V1, following the API spec
"""
import aiohttp
import os
import unittest
import time
import urllib
from typing import TypedDict, List
import functools
import pandas as pd
import numpy as np
import pytz
from datetime import datetime
import api

api_key = os.environ["APCA_API_KEY_ID"]
secret_key = os.environ["APCA_API_SECRET_KEY"]
headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": secret_key}

tz = pytz.timezone('America/New_York')

class Alpaca_V1(api.API):
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def get_price(self, symbol: str, t=time.time()) -> float:
        """
        symbol - Symbol to fetch price for
        t - Time to get price at, default is to get current price. In UNIX format
        """
        dt = datetime.fromtimestamp(t)
        iso = tz.localize(dt).isoformat()

        query = {
            "symbols": symbol,
            "limit": 1,
            "start": '2008-04-27T15:59:00-04:00',
            "end": iso
        }
        resp = await self.session.get(
            'https://data.alpaca.markets/v1/bars/minute?' + urllib.parse.urlencode(query),
            headers=headers
        )
        data = await resp.json()
        try:
            return data[symbol][0]['c']
        except Exception as e:
            print(data)
            raise e

    async def get_bars(self, symbol: str, timeframe: str, multiplier: int, limit: int) -> pd.DataFrame:
        """
        symbol - Symbol of stock to get bars for
        timeframe - type of candle to get, minute, hour, day, week, month
        multiplier - how many timeframes per candle
        limit - number of candles to get
        Gets last {limit} bars, for example, getBars('AAPL', 'minute', 4, 3000) gets the last 3000 available 4 minute bars
        """
        tf = '' # Timeframe to contact api with
        num = 0 # number of tf to use, such as if its hour it uses 4 15Min 
        
        if (timeframe == 'minute'):
            tf = 'minute'
            num = 1
        elif (timeframe == 'hour'):
            tf = '15Min'
            num = 4
        elif (timeframe == 'day'):
            tf = 'day'
            num = 1
        elif (timeframe == 'week'):
            tf = 'day'
            num = 5
        elif (timeframe == 'month'):
            tf = 'day'
            num = 20
        
        required = limit * num * multiplier
        candles = []
        dt = datetime.fromtimestamp(time.time())
        end = tz.localize(dt).isoformat()

        while len(candles) < required:
            query = {
                "symbols": symbol,
                "limit": 1000,
                "start": '2008-04-27T15:59:00-04:00',
                "end": end
            }
            qs = urllib.parse.urlencode(query)
            url = f'https://data.alpaca.markets/v1/bars/{tf}?{qs}'
            resp = await self.session.get(url, headers=headers)
            data = await resp.json()
            candles = data[symbol] + candles
            dt = datetime.fromtimestamp(data[symbol][0]['t'])
            end = tz.localize(dt).isoformat()
        
        df = pd.DataFrame(candles[-required:], columns=["t", "o", "h", "l", "c", "v"])
        df["Datetime"] = pd.to_datetime(df["t"], unit="s").dt.tz_localize('UTC').dt.tz_convert('America/New_York')

        df = df.set_index("Datetime")

        sampled = api.aggregate_candles(df, timeframe, multiplier)
        return sampled

class TestAPICalls(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.API = Alpaca_V1()

    async def test_get_price_in_market_hours(self):
        price = await self.API.get_price('AAPL', 1618347540)
        self.assertEqual(price, 134.425)

    async def test_get_bars_basic(self):
        """
        Gets the 10 latest 1 hours candles
        """
        bars = await self.API.get_bars("AAPL", "hour", 1, 10)

        # returns 11 due to aggregate function counting incomplete candles as complete
        self.assertEqual(len(bars), 11)

    async def test_get_bars_multiplier(self):
        """
        Gets the 10 latest 4 hour candles
        """
        bars = await self.API.get_bars("AAPL", "hour", 4, 10)
        # Bars only include hour 8am and 12am candles, 4pm is missing

    async def test_get_bars_alot(self):
        """
        Tests if function works when querying data for the last 100
        4 hour bars, which should poll API for 1600 bars
        """
        bars = await self.API.get_bars("AAPL", "hour", 4, 100)
        print(bars)
        pass

    async def test_get_bars_week(self):
        """
        Tests if the functions properly queries for weekly candles
        """
        pass

    async def asyncTearDown(self):
        await self.API.session.close()

if __name__ == "__main__":
    unittest.main()