import aiohttp
import asyncio
import time
import os
import discord
from discord.ext import tasks, commands
from discord.ext import menus
from checker import pollTickers
from db import TicketDB


class TicketsMenu(menus.ListPageSource):
    def __init__(self, tickets):
        """
        Takes raw tickets and formats them into messages that appear on a menu
        """
        super().__init__(tickets, per_page=10)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page

        data = []
        for t in entries:
            if t["type"] == "price_level":
                data.append(
                    f"Watching {t['symbol']} @{t['price']} around {t['margin']}. ID: {t['id']}"
                )
            elif t["type"] == "ema":
                data.append(
                    f"Watching {t['symbol']} to touch ema at {t['timespan']} candle in {t['time_period']} periods. ID: {t['id']}"
                )
        message = "\n".join(d for d in data)
        return message


class Commands(commands.Cog):
    """Basic commands for the bot"""

    def __init__(self):
        self.db = TicketDB("alerts.db")
        self.monitorTickets.start()

    @commands.command(name="tickets")
    async def getTickets(self, ctx, category: str):
        """
        Replies with all the tickets that are currently being monitored
        category - price_level or ema, depending on the tickets u want to see
        """
        tickets = self.db.getAllTickets(category)

        if tickets == None:
            await ctx.send(f"No tickets have been made in {category}")
            return

        pages = menus.MenuPages(source=TicketsMenu(tickets), clear_reactions_after=True)
        await pages.start(ctx)

    @commands.command(name="price")
    async def price(self, ctx, symbol: str, price: float, margin: float):
        """
        Add a price level ticket to monitor
        symbol - capitalized stock ticker
        price - the price in float (ex. 60.1)
        margin - float $ if target bounds. Ex. If input is 0.05, it will alert when stock is around .05 dollars of the target
        """

        if price < 0:
            await ctx.send("Price can not be below 0")
            return

        if margin < 0:
            await ctx.send("Margin can not be below 0")
            return

        _id = self.db.insertTicket(
            {
                "type": "price_level",
                "symbol": symbol.upper(),
                "price": price,
                "margin": margin,
            }
        )
        await ctx.send(f"Successfully added {symbol}@{price} {margin}, id {_id}")

    @commands.command(name="ema")
    async def ema(self, ctx, symbol: str, timespan: str, time_period: int):
        """
        Adds an EMA watcher to tickets
        symbol should be capitalized stock ticker
        timespan - minute | hour | day | week | month | quarter | year
        time_period - How many candles should the EMA consider
        """

        intervalTypes = ["minute", "hour", "day", "week", "month", "quarter", "year"]
        if timespan not in intervalTypes:
            await ctx.send(
                f"You sent {timespan} but interval must be {' '.join(intervalTypes)}"
            )
            return

        if time_period < 3:
            await ctx.send(
                f"You sent {time_period} but timer_period must be greater than 3"
            )
            return

        ticket = {
            "type": "ema",
            "symbol": symbol.upper(),
            "timespan": timespan,
            "time_period": time_period,
        }
        self.db.insertTicket(ticket)
        await ctx.send("Successfully added EMA signal to tickets")

    @commands.command(name="delete")
    async def delete(self, ctx, _id: str):
        """
        Deletes alert from database
        Parameters:
        _id: id of the ticket
        """
        success = self.db.deleteTicket(_id)

        if success == None:
            await ctx.send("Unable to delete alert with ID " + _id)
            return

        await ctx.send(f"Deleted ticket {_id}")
        return

    @tasks.loop(seconds=0.5)
    async def monitorTickets(self):
        tickets = self.db.getAllTickets("price_level") + self.db.getAllTickets("ema")
        await pollTickers(tickets, self.db)


clientSecret = os.environ["CLIENT_SECRET"]
bot = commands.Bot(command_prefix="$")

bot.add_cog(Commands())
bot.run(clientSecret)