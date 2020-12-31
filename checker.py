import aiohttp
import asyncio
import urllib
import time
import os
from discord import Webhook, AsyncWebhookAdapter

apiKey = os.environ["API_KEY"]
webhookURL = os.environ["WEBHOOK_URL"]


async def getPriceOfTicker(symbol, apiKey, s):
    headers = {"X-Finnhub-Token": apiKey}
    params = {"symbol": symbol}
    paramsString = urllib.parse.urlencode(params)
    resp = await s.get(
        "https://finnhub.io/api/v1/quote?" + paramsString, headers=headers
    )
    data = await resp.json()
    return data["c"]


async def alertEMA(symbol, interval, time_period, apiKey, s):
    headers = {"X-Finnhub-Token": apiKey}
    params = {
        "symbol": symbol,
        "resolution": interval,
        "indicator": "EMA",
        "timeperiod": time_period,
        "from": 1583098857,
        "to": int(time.time()),
    }
    paramsString = urllib.parse.urlencode(params)
    resp = await s.get(
        "https://finnhub.io/api/v1/indicator?" + paramsString, headers=headers
    )
    data = await resp.json()
    currentPrice = data["c"][-1]
    emaLevel = data["ema"][-1]
    return evalEMA(currentPrice, emaLevel)


def evalPriceSignal(price, signal, signalPrice):
    if signal == "ABOVE":
        return (price == signalPrice) or (price > signalPrice)
    elif signal == "BELOW":
        return (price == signalPrice) or (price < signalPrice)


def evalEMA(currentPrice, ema):
    return (currentPrice <= ema * 1.05) and (currentPrice >= ema * 0.95)


async def sendWebhook(message):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhookURL, adapter=AsyncWebhookAdapter(session))
        await webhook.send(message)


# Returns boolean value of if the ticket went off or not
async def handlePriceLevelTicket(t, s):
    currentPrice = await getPriceOfTicker(t["symbol"], apiKey, s)
    alertPrice = evalPriceSignal(currentPrice, t["signal"], t["price"])
    if alertPrice:
        message = (
            f"{t['symbol']} hit signal of {t['signal']} {t['price']} at {currentPrice}"
        )
        await sendWebhook(message)
        return True
    return False


# Alerts EMA type tickets
# Returns boolean value of if the ticket went off or not
async def handleEmaTicket(t, s):
    intervalTranslator = {
        "1": "1 Minute",
        "5": "5 Minutes",
        "15": "15 Minutes",
        "30": "30 Minutes",
        "60": "60 Minutes",
        "D": "Daily",
        "W": "Weekly",
        "M": "Monthly",
        "Y": "Yearly",
    }
    emaAlert = await alertEMA(t["symbol"], "D", 10, apiKey, s)
    if emaAlert:
        message = (
            f"{t['symbol']} hit EMA level on the {intervalTranslator[t['interval']]}"
        )
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
