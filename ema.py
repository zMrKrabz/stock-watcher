import api
from alpaca_v1 import Alpaca_V1 as API
import talib
import unittest
import pandas as pd
from typing import Callable, Awaitable
from ticket import Ticket
import time
from custom_logger import get_logger

logger = get_logger(__name__)

def get(candles: pd.DataFrame, periods: int):
    """
    candles - python dataframe of candles to use to calculate EMA
    periods - How many candles to use for EMA calculation

    Adds EMA column to candles dataframe
    """
    c = candles['c'].iloc[:]
    ema = talib.EMA(c, periods)
    candles[f"{periods}EMA"] = ema


def candles_to_seconds(timeframe: str, multiplier: int) -> int:
    """
    timeframe - minute, hour, day, week, month
    multiplier - how many timeframes
    returns candle in seconds
    """
    if timeframe == 'minute':
        return multiplier * 60
    if timeframe == 'hour':
        return multiplier * 3600
    if timeframe == 'day':
        return multiplier * 3600 * 24
    if timeframe == 'week':
        return multiplier * 3600 * 24 * 7
    if timeframe == 'month':
        return multiplier * 3600 * 24 * 30

class EMA(Ticket):
    def __init__(self, symbol: str, timeframe: str, periods: int, channelID: int, author: int, _id: str, multiplier=1, margin=0.001):
        """
        symbol - of the stock
        timeframe - which candle to use, minute, hour, day, week, month
        periods - how many candles to use to calculate EMA
        channelID - which discord channel send the alert
        author - authorID of the discord command author
        id - str ID
        multiplier - how many timeframes to use, ex put 4 for 4 hour candles
        margin - how far the ema and price of stock can be
        """
        super().__init__(channelID, author, _id)
        self.symbol = symbol
        self.timeframe = timeframe
        self.multiplier = multiplier
        self.periods = periods
        self.margin = margin

    def __str__(self):
        return f"{self._id}: {self.symbol} to hit {self.periods}EMA on the {self.multiplier}{self.timeframe} candle"

    async def monitor(self, api: api.API, callback: Callable[[str], Awaitable[None]]) -> Awaitable[None]:
        """
        callback - async function to call if the ticket should be alerted

        Sees if the current EMA ticket should be alerted
        """
        current_time = time.time()
        candles = await api.get_bars(
            self.symbol,
            self.timeframe,
            self.multiplier,
            limit=self.periods,
            t=current_time
        )
        get(candles, self.periods)

        current = candles.tail(1)
        high_price = current['h'].values[0]
        low_price = current['l'].values[0]
        ema = current[f"{self.periods}EMA"].values[0]

        if (ema < high_price * (1 + self.margin)) and (ema < low_price * (1 - self.margin)):
            logger.info(f"{self.symbol} @ EMA {ema}. TS: {current.iloc[-1]['t']}. Sys: {current_time}")
            await callback(str(self))
        else:
            logger.info(f"{self.symbol} EMA is {ema}. Price is {current.iloc[-1]['c']}. TS: {current.iloc[-1]['t']}. Sys: {current_time}")

        return

    def timeout(self):
        """
        returns 2 candle bar delay
        """
        return 2 * candles_to_seconds(self.timeframe, self.multiplier)

class Test(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api = API()

    async def test_monitor(self):
        ticket = EMA(symbol='AAPL', timeframe='hour', periods=50, multiplier=1, channelID=123, author=456, _id=0)

        async def message(m: str) -> Awaitable[None]:
            print(m, ticket.channelID, ticket.author)

        await ticket.monitor(self.api, message)
        # Technically this does work because the error printed means that print isn't async

    async def test_get(self):
        candles = await self.api.get_bars('AAPL', timeframe='hour', multiplier=1, limit=100)
        get(candles, 50)
        # print(candles)

    async def test_timeout(self):
        ticket = EMA(symbol='AAPL', timeframe='week', periods=50, multiplier=4, channelID=123, author=456, _id=0)
        timeout = ticket.timeout()
        self.assertEqual(timeout, 2419200 * 2)

    async def asyncTearDown(self):
        await self.api.session.close()


if __name__ == '__main__':
    unittest.main()