from db import DB
from ticket import Ticket
from api import API
from ema import EMA
from price import Price
import sqlite3
from typing import List
from uuid import uuid4
import unittest
import time

class SQL(DB):
    conn = None

    def __init__(self, path: str):
        if SQL.conn is None:
            self.conn = sqlite3.connect(path)
            c = self.conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS 
                    price (
                        id TEXT,
                        symbol TEXT, 
                        price FLOAT, 
                        margin FLOAT, 
                        timestamp INTEGER, 
                        timeout INTEGER,
                        channelID INTEGER,
                        author INTEGER
                    )
                """
            )
            c.execute(
                """CREATE TABLE IF NOT EXISTS 
                    ema (
                        id TEXT,
                        symbol TEXT, 
                        timeframe TEXT, 
                        multiplier INTEGER,
                        periods INTEGER,
                        margin FLOAT,
                        timestamp INTEGER,
                        timeout INTEGER,
                        channelID INTEGER,
                        author INTEGER
                    )
                """
            )
            c.close()

    def add_price(self, symbol: str, price: float, channelID: int, author: int, margin=1.0) -> str:
        """
        symbol - stock symbol
        price
        channelID - discord channel ID to send alert to
        author - discordID of who created the command
        margin - how far away the current and target price can be

        returns ticketID
        Adds price ticket to database
        """
        c = self.conn.cursor()
        _id = f"price_{str(uuid4())[:8]}"
        timestamp = int(time.time())

        c.execute(
            """
            INSERT INTO
                price
            VALUES
                (?, ?, ?, ?, ?, 0, ?, ?)   
            """,
            (
                _id,
                symbol,
                price,
                margin,
                timestamp,
                channelID,
                author
            )
        )
        c.close()
        self.conn.commit()
        return _id

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
        c = self.conn.cursor()
        _id = f"ema_{str(uuid4())[:8]}"
        timestamp = int(time.time())

        c.execute(
            """
            INSERT INTO
                ema
            VALUES
                (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                _id,
                symbol,
                timeframe,
                multiplier,
                periods,
                margin,
                timestamp,
                channelID,
                author
            )
        )
        c.close()
        self.conn.commit()
        return _id

    def get_all_ema(self, authorID=0, symbol="*", active=False) -> List[EMA]:
        """
        authorID -  of ticket author
        symbol - optional, only get tickets with this symbol
        active - if true, will only get tickets where now > timeout
        Gets all the EMA alerts made by author
        """
        c = self.conn.cursor()
        query = """
            SELECT
                *
            FROM 
                ema  
        """
        values = ()

        if (authorID != 0):
            query += "WHERE author = ?\n"
            values += (authorID,)

        if symbol != "*":
            if (len(values) == 0):
                query += "WHERE symbol = ?\n"
            else:
                query += "AND symbol = ?\n"

            values = values + (symbol,)

        if active == True:
            if (len(values) == 0):
                query += "WHERE timeout = ?\n"
            else:
                query += "AND timeout < ?\n"
            values = values + (int(time.time()),)

        query += "ORDER BY symbol"

        rows = c.execute(
            query,
            values
        )

        tickets = [EMA(
            _id=d[0],
            symbol=d[1],
            timeframe=d[2],
            periods=d[4],
            channelID=d[7],
            author=d[8],
            multiplier=d[3],
            margin=d[5]
        ) for d in rows]

        c.close()
        return tickets

    def get_all_price(self, authorID=0, symbol='*', active=False) -> List[Price]:
        """
        authorID -  of ticket author
        symbol - optional, only get tickets with this symbol
        active - if true, will only get tickets where now > timeout

        Gets all the price alerts made by author
        """
        c = self.conn.cursor()

        query = """
            SELECT
                *
            FROM 
                price
        """

        values = ()
        if (authorID != 0):
            query += "WHERE author = ?\n"
            values += (authorID,)

        if symbol != "*":
            if (len(values) == 0):
                query += "WHERE symbol = ?\n"
            else:
                query += "AND symbol = ?\n"

            values = values + (symbol,)

        if active == True:
            if (len(values) == 0):
                query += "WHERE timeout < ?\n"
            else:
                query += "AND timeout < ?\n"
            values = values + (int(time.time()),)

        query += "ORDER BY symbol"

        rows = c.execute(
            query,
            values
        )

        tickets = [Price(
            _id=d[0],
            symbol=d[1],
            price=d[2],
            channelID=d[6],
            author=d[7],
            margin=d[3]
        ) for d in rows]

        c.close()
        return tickets

    def delete(self, _id: str) -> bool:
        """
        _id - id of ticket to delete

        returns if delete was successful
        """
        c = self.conn.cursor()

        t = _id.split("_")
        table = t[0]

        if table not in ['price', 'ema']:
            return False

        c.execute(
            """
            DELETE FROM
                table_name
            WHERE
                id = ?
            """.replace("table_name", table),
            (_id,)
        )

        c.close()
        return True

    def update_timeout(self, _id: str, timeout: int) -> None:
        """
        _id - id of ticket to update
        timeout - when to wait until, not duration

        Updates timeout of _id
        """
        c = self.conn.cursor()

        t = _id.split("_")
        table = t[0]

        if table not in ['price', 'ema']:
            return False

        c.execute(
            """
            UPDATE
                table_name
            SET 
                timeout = ?
            WHERE
                id = ?
            """.replace("table_name", table),
            (timeout, _id)
        )

        c.close()
        self.conn.commit()
    
class Test(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = SQL('./test_alerts.db')
    
    async def test_ema(self):
        _id = self.db.add_ema('AAPL', 'hour', 50, channelID=12345, author=12345)
        tickets = self.db.get_all_ema(12345)
        t = tickets[0]
        self.assertEqual(t._id, _id)

    async def test_ema_no_author(self):
        _id = self.db.add_ema('AAPL', 'hour', 50, channelID=12345, author=12345)
        tickets = self.db.get_all_ema()
        self.assertEqual(len(tickets), 1)

    async def test_price(self):
        _id = self.db.add_price('AAPL', 134, channelID=123, author=456, margin=0.01)
        tickets = self.db.get_all_price(456)
        t = tickets[0]
        self.assertEqual(_id, t._id)

    async def test_price_no_author(self):
        _id = self.db.add_price('AAPL', 134, channelID=123, author=456, margin=0.01)
        tickets = self.db.get_all_price()
        self.assertEqual(len(tickets), 1)

    async def test_delete(self):
        _id = self.db.add_price('AAPL', 134, channelID=123, author=456, margin=0.01)
        self.db.delete(_id)
        tickets = self.db.get_all_price(456)
        self.assertEqual(len(tickets), 0)

    async def test_update(self):
        _id = self.db.add_price('AAPL', 134, channelID=123, author=456, margin=0.01)
        self.db.update_timeout(_id, time.time() + 10000)
        active_tickets = self.db.get_all_price(456, active=True)
        inactive_tickets = self.db.get_all_price(456)
        self.assertGreater(len(inactive_tickets), len(active_tickets))


    async def asyncTearDown(self):
        self.db.conn.execute("DELETE FROM ema")
        self.db.conn.execute("DELETE FROM price")
        self.db.conn.commit()

if __name__ == "__main__":
    unittest.main()