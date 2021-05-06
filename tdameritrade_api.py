import tdameritrade as td
import api
import os
import time
import unittest
import pandas as pd
from logger import getLogger


logger = getLogger(__name__)


class TdAmeritradeAPI(api.API):
    def __init__(self):
        client_id = os.getenv("TDAMERITRADE_CLIENT_ID")
        account_id = os.getenv("TDAMERITRADE_ACCOUNT_ID")
        refresh_token = os.getenv("TDAMERITRADE_REFRESH_TOKEN")
        self.client = td.TDClient(client_id=client_id, refresh_token=refresh_token, account_ids=[account_id])

    async def get_price(self, symbol: str, t=time.time()) -> api.Price:
        quote = self.client.quote(symbol)

        logger.info(quote)
        
        return api.Price(t=quote[symbol]['quoteTimeInLong'], p=quote[symbol]['askPrice'])
    
    async def get_bars(self, symbol: str, timeframe: str, multiplier=1, limit=1000) -> pd.DataFrame:
        frequency_type = ''  # Timeframe to contact api with
        num = 0  # number of frequency_type to use, such as if its hour it uses 4 15Min
        period_type = ''
        periods = 0

        if timeframe == 'minute':
            frequency_type = 'minute'
            num = 1
            period_type = 'day'

        elif timeframe == 'hour':
            frequency_type = 'minute'
            num = 60
            period_type = 'day'

        elif timeframe == 'day':
            frequency_type = 'daily'
            num = 1
            period_type = 'day'

        elif timeframe == 'week':
            frequency_type = 'weekly'
            num = 1
            period_type = 'week'

        elif timeframe == 'month':
            tf = 'monthly'
            num = 1
            period_type = 'month'

        required = multiplier * num * limit

        bars = []

        while len(bars) < required:
            candles = self.client.history(
                symbol=symbol,
                frequencyType='minute',
                frequency=15,
                periodType='day',
                period=1
            )
            bars = candles['candles'] + bars

        # print(len(bars))
        df = pd.DataFrame(bars)
        return df


class Test(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = TdAmeritradeAPI()

    async def test_price(self):
        q = await self.client.get_price("AAPL")
        print({ "AAPL": q })
        
    async def test_price(self):
        q = await self.client.get_price("BX")
        print({ "BX": q })
    # async def test_get_bars(self):
    #     bars = await self.client.get_bars("AAPL", timeframe="hour", multiplier=4, limit=1000)


if __name__ == '__main__':
    unittest.main()