import aiohttp
import asyncio
import urllib
import time
import os
from datetime import datetime, timedelta
from talib import EMA
import numpy as np
import pandas as pd
import pandas_ta as ta
import unittest
from db import TicketDB

apiKey = os.environ["APCA_API_KEY_ID"]
privateKey = os.environ["APCA_API_PRIVATE_KEY"]
headers = {"APCA-API-KEY-ID": apiKey, "APCA-API-SECRET-KEY": privateKey}

"""
Functions related to simply alerting price of a ticker
"""
# Returns latest ask and bid of a stock
async def getPriceOfTicker(symbol, s):
    resp = await s.get(
        f"https://data.alpaca.markets/v1/last_quote/stocks/{symbol}", headers=headers
    )
    data = await resp.json()
    return {"ask": data["last"]["askprice"], "bid": data["last"]["bidprice"]}


# Returns boolean of if the current price is within target price bounds
def evalPriceSignal(currentPrice: float, targetPrice: float, margin: float):
    return (targetPrice + margin > currentPrice) and (
        targetPrice - margin < currentPrice
    )


def convertLimit(timespan: str, limit=1):
    """
    Converts desired limit (ex. 50 hours) into minute format
    """
    if timespan == "minute":
        return limit
    if timespan == "hour":
        return limit * 60
    if timespan == "day":
        return limit * 60 * 24
    if timespan == "week":
        return limit * 60 * 24 * 7
    if timespan == "month":
        return limit * 60 * 24 * 7 * 4
    if timespan == "quarter":
        return limit * 60 * 24 * 7 * 4 * 4
    if timespan == "year":
        return limit * 60 * 24 * 7 * 4 * 4 * 4


# Get all candles over a certain interval
# Returns array of candles
# Documentation: https://alpaca.markets/docs/api-documentation/api-v2/market-data/alpaca-data-api-v1/bars/
async def getCandles(s, timeframe, symbol, limit=100):
    query = {"symbols": symbol, "limit": limit}
    queryString = urllib.parse.urlencode(query)
    resp = await s.get(
        f"https://data.alpaca.markets/v1/bars/{timeframe}?{queryString}",
        headers=headers,
    )

    data = await resp.json()
    """
    Results array of
    {'t': 1614977940, 'o': 121.57, 'h': 121.72, 'l': 121.22, 'c': 121.22, 'v': 14272}
    """
    candles = data[symbol]
    df = pd.DataFrame(candles, columns=["t", "o", "h", "l", "c", "v"])
    df["Datetime"] = pd.to_datetime(df["t"], unit="s")
    df = df.set_index("Datetime")
    df = df[df["c"] != 0]

    return df


def convertTimespan(timespan: str, multiplier=1):
    # timespan - minute, hour, day
    # multiplier - how many timespans, ex. 4 Days
    # returns dataframe resample formatted rule
    if timespan == "minute":
        return str(multiplier) + "T"

    if timespan == "hour":
        return str(multiplier) + "H"

    if timespan == "day":
        return str(multiplier) + "D"


def aggregateCandles(candles, timespan: str, multiplier=1, toDict=True):
    # candles - candles from getCandles as dataframe
    # timespan - minute, hour, day
    # multiplier - how many timespans, ex. 4 Days
    # returns candles aggregated, with OHLCVT format
    rule = convertTimespan(timespan, multiplier)
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


"""
Code to handle EMA related functions
"""

# candles - pandas dataframe of items
# returns ema array
def getEMA(candles, timeperiod: int):
    candles = candles.loc[:, 'c'].values
    data = EMA(candles, timeperiod=timeperiod)
    return data[-timeperiod:]


# timespan - One of minute, 1Min, 5Min, 15Min, day or 1D.
# timeperiod - How many candles to use
# returns boolean if ema should be alerted
async def alertEMA(s, symbol: str, timespan: str, timeperiod: int):
    timeframe = timespan
    # Changes hour into 15M candles
    if (timespan == 'hour'): 
        timeframe = '15Min'

    candles = await getCandles(s, timeframe, symbol, limit=(2*4 * timeperiod))

    candles = aggregateCandles(candles, timespan, toDict=False)
    data = getEMA(candles, timeperiod)
    return evalEMA(candles["c"].iloc[-1], data[-1])


# Evaluates and sees if ema is within 2% of target price level
def evalEMA(currentPrice: float, ema: float):
    return (currentPrice <= ema * 1.001) and (currentPrice >= ema * 0.999)


# Returns message if ticket was hit, else return message to send
async def handlePriceLevelTicket(t, s):
    current = await getPriceOfTicker(t["symbol"], s)
    alertPrice = evalPriceSignal(current["ask"], t["price"], t["margin"])
    if alertPrice:
        message = f"{t['symbol']} hit signal of {t['price']} around {t['margin']}. Currently trading for {current['ask']}. <@{t['author']}>"
        return message
    return False


# Alerts EMA type tickets
# Returns boolean value of if the ticket went off or not
async def handleEmaTicket(t, s):
    emaAlert = await alertEMA(s, t["symbol"], t["timespan"], t["timeperiod"])
    if emaAlert:
        message = f"{t['symbol']} hit EMA {t['time_period']} level on the {t['timespan']} candle. <@{t['author']}\n"
        return message
    return False


# Polls all tickets and if ticket is at signal, timeouts ticket, then sends message
async def pollTickets(tickets: list, db: TicketDB, bot):
    async with aiohttp.ClientSession() as s:
        for t in tickets:
            if int(time.time()) < t["timeout"]:
                continue

            try:
                if t["type"] == "price_level":
                    message = await handlePriceLevelTicket(t, s)
                    t["timespan"] = "day"
                elif t["type"] == "ema":
                    message = await handleEmaTicket(t, s)

                if message:
                    timeout = int(time.time()) + convertLimit(t["timespan"], 3) * 60
                    db.timeoutTicket(t["id"], timeout)
                    channel = await bot.get_channel(t["channelID"])
                    await channel.send(message)
                else:
                    timeout = int(time.time()) + convertLimit(t["timespan"], 1) * 60
                    db.timeoutTicket(t["id"], timeout)

            except Exception as e:
                print(f"Errored on {t}")
                print(e)
                channel = await bot.get_channel(t['channelID'])
                await channel.send(f"Error occurred with {t}")
                db.deleteTicket(t["id"])


class TestSignalEval(unittest.TestCase):
    def test_price_range_high(self):
        signal = evalPriceSignal(96, 100, 5)
        self.assertTrue(signal)

    def test_price_range_below(self):
        signal = evalPriceSignal(101, 100, 5)
        self.assertTrue(signal)

    def test_price_range_too_high(self):
        signal = evalPriceSignal(106, 100, 5)
        self.assertFalse(signal)

    def test_price_range_too_low(self):
        signal = evalPriceSignal(90, 100, 5)
        self.assertFalse(signal)


class TestAPICalls(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session = aiohttp.ClientSession()
        self.symbol = "AAPL"

    # async def test_get_candles(self):
    #     candles = await getCandles(self.session, "minute", self.symbol)
    #     print({"candles": candles[-1]})

    # # Tests if EMA is good for 50 minute candles
    # async def test_getEMA(self):
    #     candles = await getCandles(self.session, "minute", self.symbol, 100)
    #     ema = await getEMA(candles, 50)
    #     print({"ema_length": len(ema)})
    #     print({"ema": ema[-1]})

    async def test_alertEMA(self):
        timeperiod = 50
        ema = await alertEMA(self.session, self.symbol, "hour", 50)
        print({'emaAlert': ema})

    # async def test_get_price(self):
    #     price = await getPriceOfTicker("AAPL", self.session)
    #     print({"price": price})

    # async def test_aggregate(self):
    #     candles = await getCandles(self.session, "15Min", self.symbol, 40)
    #     hourCandles = aggregateCandles(candles, "hour", 1)
    #     self.assertEqual(hourCandles[2]['t'] - hourCandles[1]['t'], 3600)

    async def asyncTearDown(self):
        await self.session.close()


if __name__ == "__main__":
    unittest.main()