from abc import ABC, abstractmethod
from typing import Callable, Awaitable
from api import API

class Ticket(object):
    def __init__(self, channelID: int, author: int, _id: str):
        self.channelID = channelID
        self.author = author
        self._id = _id

    def __str__(self):
        return f'{self._id} {self.channelID} {self.author}'
        
    async def monitor(self, api: API, callback: Callable[[str, int, int, str, int], Awaitable[None]]) -> None:
        """
        Monitor function. First argument is the message, second is the channelID, third is the authorID
        async def send(message: str, channelID: int, authorID: int, _id: str, calculated_timeout: int) -> None:
        """
        return

    def timeout(self) -> int:
        """
        Returns the timeout duration
        """
        return
