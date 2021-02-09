import aiohttp
import asyncio
import urllib
import time
import os
from datetime import datetime, timedelta
from discord import Webhook, AsyncWebhookAdapter
from talib import EMA
import numpy as np
import unittest
from db import TicketDB

apiKey = os.environ["APCA_API_KEY_ID"]
webhookURL = os.environ["WEBHOOK_URL"]

"""
Functions related to simply alerting price of a ticker
"""
# Returns latest ask and bid of a stock
async def getPriceOfTicker(symbol, apiKey, s):
    params = {"apiKey": apiKey}
    paramString = urllib.parse.urlencode(params)
    resp = await s.get(
        f"https://api.polygon.io/v1/last_quote/stocks/{symbol}?" + paramString
    )
    data = await resp.json()
    return {"ask": data["last"]["askprice"], "bid": data["last"]["bidprice"]}


# Returns boolean of if the current price is within target price bounds
def evalPriceSignal(currentPrice: float, targetPrice: float, margin: float):
    return (targetPrice + margin > currentPrice) and (
        targetPrice - margin < currentPrice
    )


# Get all candles over a certain interval
# Returns array of candles
async def getCandles(s, symbol, multiplier, timespan, limit):
    params = {"apiKey": apiKey, "sort": "desc", "limit": limit, "unadjusted": "true"}
    paramString = urllib.parse.urlencode(params)
    start = "2000-10-14"
    end = datetime.now().strftime("%Y-%m-%d")
    resp = await s.get(
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start}/{end}?"
        + paramString
    )
    data = await resp.json()
    print(data)
    data["results"].reverse()

    """
    Results array of 
    {'v': 155217709.0, 'vw': 142.6006, 'o': 143.07, 'c': 142.92, 'h': 145.09, 'l': 136.54, 't': 1611550800000}
    """
    return data["results"]


"""
Code to handle EMA related functions
"""

# timespan - minute | hour | day | week | month | quarter | year
# timeperiod - How many candles to use
# returns boolean if ema should be alerted
async def alertEMA(s, symbol, timespan, timeperiod):
    candles = await getCandles(s, symbol, 1, timespan, timeperiod)
    df = np.asarray([float(d["c"]) for d in candles])
    data = EMA(df, timeperiod=timeperiod)
    ema = data[-1]
    return evalEMA(candles[-1]["c"], ema)


# Evaluates and sees if ema is within 2% of target price level
def evalEMA(currentPrice: float, ema: float):
    return (currentPrice <= ema * 1.02) and (currentPrice >= ema * 0.98)


# Sends webhook text and message
async def sendWebhook(message):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhookURL, adapter=AsyncWebhookAdapter(session))
        await webhook.send(message)


# Returns boolean value of if the ticket went off or not
async def handlePriceLevelTicket(t, s):
    current = await getPriceOfTicker(t["symbol"], apiKey, s)
    alertPrice = evalPriceSignal(current["ask"], t["price"], t["margin"])
    if alertPrice:
        message = f"{t['symbol']} hit signal of {t['price']} around {t['margin']}. Currently trading for {current['ask']}"
        await sendWebhook(message)
        return True
    return False


# Alerts EMA type tickets
# Returns boolean value of if the ticket went off or not
async def handleEmaTicket(t, s):
    emaAlert = await alertEMA(s, t["symbol"], t["timespan"], t["time_period"])
    if emaAlert:
        message = f"{t['symbol']} hit EMA level on the {t['timespan']} candle.\n"
        await sendWebhook(message)
        return True
    return False


# Polls all tickers and if ticker is at signal, delete ticker then send discord webhook
async def pollTickers(tickets: list, db: TicketDB):
    async with aiohttp.ClientSession() as s:
        for t in tickets:
            alerted = False
            if t["type"] == "price_level":
                alerted = await handlePriceLevelTicket(t, s)
            elif t["type"] == "ema":
                alerted = await handleEmaTicket(t, s)

            if alerted:
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

    async def test_get_candles(self):
        candles = await getCandles(self.session, "AAPL", 1, "day", 10)
        print(candles)

    async def asyncTearDown(self):
        await self.session.close()


if __name__ == "__main__":
    unittest.main()