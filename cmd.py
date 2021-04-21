"""
Command line interface for bot
"""
from alpaca_v1 import Alpaca_V1 as API
import ema
from datetime import datetime
from time import strftime
import asyncio

async def save():
    api = API()
    symbol = input("Symbol: ")
    timeframe = input("Timeframe (minute, hour, day, week, month): ")
    multiplier = int(input("Multiplier: "))
    limit = int(input("Limit: "))
    candles = await api.get_bars(symbol, timeframe, multiplier, limit)

    add_ema = input("Add EMA? (Y/n)")

    if (add_ema == 'Y'):
        periods = int(input("Periods: "))
        ema.get(candles, periods)

    candles = candles.drop(columns=["t"])
    now = datetime.now().strftime("%Y-%m-%d")
    candles.to_csv(f'{symbol}_{multiplier}{timeframe}_{now}.csv')

asyncio.run(save())