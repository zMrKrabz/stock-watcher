from uuid import uuid4
import time
from ema import EMA
from price import Price
from api import API
from abc import ABC
from typing import Callable, Awaitable, List
from ticket import Ticket

# Repository pattern
class DB(ABC):
    # @abstractmethod
    def add_price(self, symbol: str, price: float, channelID: int, author: int, margin=0.01) -> str:
        """
        symbol - stock symbol
        price
        channelID - discord channel ID to send alert to
        author - discordID of who created the command
        margin - how far away the current and target price can be

        returns ticketID
        Adds price ticket to database
        """
        return

    # @abstractmethod
    def add_ema(self, symbol: str, timeframe: str, periods: int, channelID: int, author: int, multiplier=1, margin=0.001) -> str:
        """
        symbol - stock symbol
        timeframe - which candle to use: minute, hour, day, week, month
        periods - how many candles to use to calculate ema
        channelID - discord channel ID to send alert to
        author - discordID of who created the command
        multiplier - how many timeframes to use, ex: 4 as multiplier and hour as timeframe would result in 4H candles used
        margin - how far away the current ema and current price can be

        returns ticketID
        Adds EMA ticket to 
        """
        return

    # @abstractmethod
    def delete(self, id: str) ->bool:
        """
        id - tickets ID

        returns whether the delete was successful or not
        Deletes ticket from database
        """
        return

    # @abstractmethod
    def get_all(self) -> List[Ticket]:
        """

        returns all tickets from database as Ticket objects
        """
        return

    # @abstractmethod
    def get_all_ema(self) -> List[EMA]:
        """
        returns all EMA tickets from database
        """
        return

    def get_all_price(self) -> List[Price]:
        """
        returns all price tickets
        """
        return

    def update_timeout(self, _id: str, timeout: int) -> None:
        """
        updates timeout of specific ticket
        """
        return
