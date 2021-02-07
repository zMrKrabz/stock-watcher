import sqlite3
import unittest
from uuid import uuid4
import time
import adapter


class TicketDB:
    conn = None

    def __init__(self, path):
        if TicketDB.conn is None:
            self.conn = sqlite3.connect(path)
            c = self.conn.cursor()
            c.execute(
                "CREATE TABLE IF NOT EXISTS price_level (symbol TEXT, price FLOAT, margin FLOAT, id TEXT, timestamp INTEGER)"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS ema (symbol TEXT, timespan TEXT, time_period INTEGER, id TEXT, timestamp INTEGER)"
            )
            c.close()

    def getTables(self):
        c = self.conn.cursor()
        rows = c.execute(
            """
        SELECT
            name
        FROM
            sqlite_master
        WHERE
            type ='table' AND
            name NOT LIKE 'sqlite_%';
        """
        )
        tables = [d[0] for d in rows]
        c.close()
        return tables

    def getTicket(self, _id: str):
        """
        id - ticket id
        Returns ticket that was found matching ID
        """
        c = self.conn.cursor()
        ticketType = _id.split("-")[0]

        tables = self.getTables()
        if ticketType not in tables:
            return None

        doc = c.execute(
            "SELECT * FROM table WHERE id=?".replace("table", ticketType),
            (_id,),
        )
        ticket = doc.fetchone()

        c.close()
        if ticket == None:
            return None

        if ticketType == "price_level":
            return {
                "type": "price_level",
                "symbol": ticket[0],
                "price": ticket[1],
                "margin": ticket[2],
                "id": ticket[3],
            }

        if ticketType == "ema":
            return {
                "type": "ema",
                "symbol": ticket[0],
                "timespan": ticket[1],
                "time_period": ticket[2],
                "id": ticket[3],
            }

    def insertTicket(self, ticket: dict):
        """
        ticket - the alert to add to database
        Returns alert with ID
        """
        ticket["id"] = ticket["type"] + "-" + str(uuid4())[:8]
        ticket["timestamp"] = int(time.time())
        c = self.conn.cursor()
        value = tuple(ticket.values())[1:]
        c.execute(
            """
            INSERT INTO table 
            VALUES (?, ?, ?, ?, ?)
            """.replace(
                "table", ticket["type"]
            ),
            value,
        )
        c.close()
        self.conn.commit()
        return ticket["id"]

    def deleteTicket(self, _id: str):
        """
        Returns None if the id could not be identified, or True if delete was successful
        """
        c = self.conn.cursor()
        ticketType = _id.split("-")[0]
        tables = self.getTables()

        if ticketType not in tables:
            return None

        c.execute("DELETE FROM table WHERE id=?".replace("table", ticketType), (_id,))
        c.close()
        self.conn.commit()
        return True

    def getTickets(self, category, idx=0, count=10):
        """
        Gets all tickets from specified category (ema, price_level) by specific index and count
        """
        c = self.conn.cursor()
        tables = self.getTables()

        if category not in tables:
            return None

        rows = c.execute(
            """
        SELECT *
        FROM 
            table
        ORDER BY 
            timestamp
        LIMIT ?
        OFFSET ?
        """.replace(
                "table", category
            ),
            (count, idx),
        )

        if category == "price_level":
            return [adapter.priceLevelAdapter(d) for d in rows]

        if category == "ema":
            return [adapter.emaAdapter(d) for d in rows]

    def getAllTickets(self, category):
        """
        Gets all tickets from a category
        """
        c = self.conn.cursor()
        tables = self.getTables()

        if category not in tables:
            return None

        rows = c.execute(
            """
        SELECT *
        FROM table
        """.replace(
                "table", category
            )
        )
        if category == "price_level":
            return [adapter.priceLevelAdapter(d) for d in rows]

        if category == "ema":
            return [adapter.emaAdapter(d) for d in rows]


class Tests(unittest.TestCase):
    def setUp(self):
        self.db = TicketDB("alerts.db")

    def test_crudOperations(self):
        ticket = {"type": "price_level", "symbol": "TESTI", "price": 100, "margin": 10}
        # Create and Read
        t = self.db.insertTicket(ticket)
        check = self.db.getTicket(t["id"])
        self.assertEqual(ticket["type"], check["type"])

        # Delete
        success = self.db.deleteTicket(t["id"])
        self.assertEqual(success, True)

    def test_fetchBadTicketType(self):
        t = self.db.getTicket("; DROP TABLES-abcde")
        self.assertIsNone(t)

    def test_deleteAlert(self):
        """
        Delete inserted alert with ID
        """
        ticket = {"type": "price_level", "symbol": "TESTI", "price": 100, "margin": 10}
        t = self.db.insertTicket(ticket)
        success = self.db.deleteTicket(t["id"])
        self.assertEqual(success, True)
        pass

    def test_getMultipleAlerts(self):
        """
        Gets alerts based on count and starting index, with default of 0
        Tests for pagniation
        """
        ticket = {"type": "price_level", "symbol": "TESTI", "price": 100, "margin": 10}
        for i in range(10):
            self.db.insertTicket(ticket)
        ticket["symbol"] = "ABC"
        self.db.insertTicket(ticket)

        tickets = self.db.getTickets("price_level", 0, 5)
        self.assertEqual(len(tickets), 5)

    def tearDown(self):
        self.db.conn.execute("DELETE FROM price_level")
        self.db.conn.commit()


if __name__ == "__main__":
    unittest.main()