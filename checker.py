import aiohttp
import asyncio
import urllib
import time
import os
from datetime import datetime, timedelta
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


def calculateTimePeriod(interval, time_period):
    fromTime = (datetime.now()).timestamp()

    if interval == "1":
        fromTime -= timedelta(minutes=1).total_seconds() * (time_period + 100)
    elif interval == "5":
        fromTime -= timedelta(minutes=5).total_seconds() * (time_period + 100)
    elif interval == "15":
        fromTime -= timedelta(minutes=15).total_seconds() * (time_period + 100)
    elif interval == "60":
        fromTime -= timedelta(minutes=60).total_seconds() * (time_period + 100)
    elif interval == "D":
        fromTime -= timedelta(days=1).total_seconds() * ((time_period / 5) * 7 + 9)
    elif interval == "W":
        fromTime -= timedelta(weeks=1).total_seconds() * (time_period + 100)
    elif interval == "M":
        fromTime -= timedelta(weeks=4).total_seconds() * (time_period + 100)

    toTime = time.time()
    return {"fromTime": int(fromTime), "toTime": int(toTime)}


async def alertEMA(symbol, interval, time_period, apiKey, s):
    periods = calculateTimePeriod(interval, time_period)
    headers = {"X-Finnhub-Token": apiKey}
    params = {
        "symbol": symbol,
        "resolution": interval,
        "indicator": "EMA",
        "timeperiod": time_period,
        "from": periods["fromTime"],
        "to": periods["toTime"],
        "seriestype": "c",
    }
    paramsString = urllib.parse.urlencode(params)
    resp = await s.get(
        "https://finnhub.io/api/v1/indicator?" + paramsString, headers=headers
    )
    data = await resp.json()

    if data["s"] == "ok":
        currentPrice = data["c"][-1]
        emaLevel = data["ema"][-1]
        return evalEMA(currentPrice, emaLevel)
    else:
        print(data)


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
            f"{t['symbol']} hit EMA level on the {intervalTranslator[t['interval']]}.\n"
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


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pollTickers([]))
    # print(calculateTimePeriod("D", 100))
