import aiohttp
import asyncio
import urllib
import time
import os
from datetime import datetime, timedelta
from discord import Webhook, AsyncWebhookAdapter
from talib import EMA
import numpy as np

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
    return (currentPrice > ((1 - margin) * targetPrice)) and (
        currentPrice < ((1 + margin) * targetPrice)
    )


# Get all candles over a certain interval
# Returns array of last close price
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
    data["results"].reverse()
    candles = [float(d["c"]) for d in data["results"]]
    return np.asarray(candles, dtype=np.float)


"""
Code to handle EMA related functions
"""

# timespan - minute | hour | day | week | month | quarter | year
# timeperiod - How many candles to use
# returns boolean if ema should be alerted
async def alertEMA(s, symbol, timespan, timeperiod):
    candles = await getCandles(s, symbol, 1, timespan, timeperiod)
    data = EMA(candles, timeperiod=timeperiod)
    ema = data[-1]
    return evalEMA(candles[-1], ema)


# Evaluates and sees if ema is within 2% of target price level
def evalEMA(currentPrice, ema):
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
        message = f"{t['symbol']} hit EMA level on the {t['interval']}.\n"
        await sendWebhook(message)
        return True
    return False


# Polls all tickers and if ticker is at signal, delete ticker then send discord webhook
async def pollTickers(tickets):
    async with aiohttp.ClientSession() as s:
        notAlertedTickets = []
        for t in tickets:
            alerted = False
            if t["type"] == "price_level":
                alerted = await handlePriceLevelTicket(t, s)
            elif t["type"] == "ema":
                alerted = await handleEmaTicket(t, s)

            if alerted == False:
                notAlertedTickets.append(t)

        return notAlertedTickets


async def test():
    global apiKey
    async with aiohttp.ClientSession() as s:
        t = {"type": "ema", "symbol": "AAPL", "timespan": "day", "time_period": 50}
        r = await handleEmaTicket(t, s)
        print(r)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
