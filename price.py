from ticket import Ticket
from typing import Callable, Awaitable
import unittest
from time import time
from alpaca_v1 import Alpaca_V1 as API

class Price(Ticket):
    """
    Used for discord bot to monitor price targets
    """
    def __init__(self, symbol: str, price: float, channelID: int, author: int, _id: str, margin=1.0):
        """
        symbol - stock symbol
        price - target price to watch out for
        margin - $ of how far the current price and target price can be
        """
        super().__init__(channelID, author, _id)
        self.symbol = symbol
        self.price = price
        self.margin = margin

    def __str__(self):
        return f"{self._id}: {self.symbol} to hit {self.price} with margin {self.margin}"

    async def monitor(self, api: API, callback: Callable[[str], Awaitable[None]]) -> Awaitable[None]:
        """
        api - API to fetch data
        callback - function to call if price hit
        """
        current_price  = await api.get_price(self.symbol)
        if (current_price['l'] < (self.price + self.margin) and current_price['h'] > (self.price - self.margin)):
            await callback(f"{self.symbol} near {self.price} currently trading at {current_price['c']}")

    def timeout(self):
        """
        returns 2 hours from now
        """
        return 3600 * 2 

class Test(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api = API()

    async def test_monitor(self):
        p = Price('AAPL', price=132, channelID=1, author=2, _id='', margin=5.0)

        async def message(m: str) -> Awaitable[None]:
            print(m, p.channelID, p.author)

        await p.monitor(self.api, message)

    async def test_JPM(self):
        p = Price('JPM', price=149.0, channelID=1, author=2, _id='', margin=.4)

        async def message(m: str) -> Awaitable[None]:
            print(m, p.channelID, p.author)

        await p.monitor(self.api, message)

    async def asyncTearDown(self):
        await self.api.session.close()


if __name__ == "__main__":
    unittest.main()