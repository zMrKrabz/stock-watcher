from ticket import Ticket
from api import API
from typing import Callable, Awaitable
import unittest
from time import time

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
        if (current_price < (self.price + self.margin)  and current_price > (self.price - self.margin)):
            await callback(f"{self.symbol} near {self.price} currently trading at {current_price}")

    def timeout(self):
        """
        returns 2 days from now
        """
        return 24 * 3600 * 2 

class Test(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api = API()

    async def test_monitor(self):
        p = Price('AAPL', 132, 1, 2, '', 5.0)

        async def message(m: str) -> Awaitable[None]:
            print(m, p.channelID, p.author)

        await p.monitor(self.api, message)

    async def asyncTearDown(self):
        await self.api.session.close()


if __name__ == "__main__":
    unittest.main()