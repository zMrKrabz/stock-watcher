from ticket import Ticket
from typing import Callable, Awaitable, List, TypedDict
import unittest
from time import time
from alpaca_v1 import Alpaca_V1
from tdameritrade_api import TdAmeritradeAPI
from api import API
from custom_logger import get_logger

logger = get_logger(__name__)


class PriceTicket(TypedDict):
    _id: str
    price: float
    symbol: str
    channelID: int
    authorID: int
    timeout: int
    margin: float


class Price(Ticket):
    """
    Used for discord bot to monitor price targets
    """
    def __init__(self, symbol: str, prices: List[PriceTicket]):
        """
        symbol - stock symbol
        prices - target prices to watch out for
        """
        self.symbol = symbol
        self.prices = prices

    def __str__(self):
        data = []
        for p in self.prices:
            data.append(f"{p['_id']}: {self.symbol} to hit {p['price']} with margin {p['margin']}")

        return '\n'.join(data)

    async def monitor(self, api: API, callback: Callable[[str, int, int, str, int], Awaitable[None]]) -> None:
        """
        api - API to fetch data
        callback - function to call if price hit
        """
        current_time = time()
        current_price = await api.get_price(self.symbol, t=current_time)

        for p in self.prices:
            if (p['price'] + p['margin']) > current_price['p'] > (p['price'] - p['margin']):
                logger.info(f"{self.symbol} near {p['price']} currently trading at {current_price['p']}. TS: {current_price['t']}. Sys: {current_time}")
                await callback(f"{self.symbol} near {p['price']} currently trading at {current_price['p']}. TS: {current_price['t']}. Sys: {current_time}",
                               p['channelID'], p['authorID'], p['_id'], self.timeout())
            else:
                logger.info(f"{self.symbol} currently trading at {current_price['p']}, watching for it to go to {p['price']} within {p['margin']}. TS: {current_price['t']}. Sys: {current_time}")

    def timeout(self):
        """
        returns 24 hours from now
        """
        return 3600 * 24


class Test(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api = TdAmeritradeAPI()

    async def test_monitor(self):
        p = Price('AAPL', prices=[PriceTicket(symbol='AAPL', channelID=1, authorID=2, price=234, margin=0.1)])

        async def message(m: str) -> None:
            print(m, p.channelID, p.author)

        await p.monitor(self.api, message)

    async def asyncTearDown(self):
        # await self.api.session.close()
        pass


if __name__ == "__main__":
    unittest.main()