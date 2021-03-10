import aiohttp
import asyncio
import time
import os
import discord
from discord.ext import tasks, commands
from discord.ext import menus
from checker import pollTickets
from db import TicketDB
from datetime import datetime, time

"""
Base ticket
channelID: str - Will send ticket to this channel
author: str - Will @ this person in chat when ticket hits
type: str - Currently supports price_level, ema. Future supports RSI
symbol: str - The ticker to watch
id: str - Unique identifier for ticket
"""

"""
Price level ticket
price: float - Price that the person expects to hit
margin: float - the dollar amount around the price
"""

"""
EMA ticket
timespan: str - minute, hour, day
multiplier: int - how many timespans
"""

class TicketsMenu(menus.ListPageSource):
    def __init__(self, tickets):
        """
        Takes raw tickets and formats them into messages that appear on a menu
        """
        super().__init__(tickets, per_page=10)

    async def format_page(self, menu, entries):
        data = []
        for t in entries:
            if t["type"] == "price_level":
                data.append(
                    f"Watching {t['symbol']} @{t['price']} around {t['margin']}. ID: {t['id']}"
                )
            elif t["type"] == "ema":
                data.append(
                    f"Watching {t['symbol']} to touch ema at {t['timespan']} candle with {t['multiplier']} multiplier. ID: {t['id']}"
                )
        message = "\n".join(d for d in data)
        return message


class Commands(commands.Cog):
    """Basic commands for the bot"""

    def __init__(self, bot):
        self.db = TicketDB("alerts.db")
        self.monitorTickets.start()
        self.bot = bot

    @commands.command()
    async def echo(self, ctx):
        authorID = ctx.author.id
        channelID = ctx.channel.id
        channel = self.bot.get_channel(616474868254244915)
        await channel.send(f"Hi <@{authorID}>")

    @commands.command(name="tickets")
    async def getTickets(self, ctx, category: str):
        """
        Replies with all the tickets that are currently being monitored
        category - price_level or ema, depending on the tickets u want to see
        """
        tickets = self.db.getAllTickets(category)

        if (tickets == None or len(tickets) < 1):
            await ctx.send(f"No tickets have been made in {category}")
            return

        pages = menus.MenuPages(source=TicketsMenu(tickets), clear_reactions_after=True)
        await pages.start(ctx)

    @getTickets.error
    async def getTicketsError(self, ctx, error):
        await ctx.send(error)

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

        _id = self.db.insertPriceTicket(
            {
                "type": "price_level",
                "symbol": symbol.upper(),
                "price": price,
                "margin": margin,
                "channelID": ctx.channel.id,
                "authorID": ctx.author.id
            }
        )
        await ctx.send(f"Successfully added {symbol}@{price} {margin}, id {_id} <@{ctx.author.id}>")

    @commands.command(name="ema")
    async def ema(self, ctx, symbol: str, timespan: str, period: int, multiplier=1):
        """
        Adds an EMA watcher to tickets
        symbol should be capitalized stock ticker
        timespan - minute | hour | day 
        multiplier: int - how many timespans
        """

        intervalTypes = ["minute", "hour", "day"]
        if timespan not in intervalTypes:
            await ctx.send(
                f"You sent {timespan} but interval must be {' '.join(intervalTypes)}"
            )
            return

        ticket = {
            "type": "ema",
            "symbol": symbol.upper(),
            "timespan": timespan,
            "multiplier": multiplier,
            "period": period,
            "channelID": ctx.channel.id,
            "authorID": ctx.author.id
        }
        self.db.insertEMATicket(ticket)
        await ctx.send(f"Successfully added EMA signal to tickets <@{ctx.author.id}>")

    @ema.error
    async def handleEMAError(self, ctx, error):
        await ctx.send(error)

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
        await self.bot.wait_until_ready()
        now = datetime.utcnow().time()
        start = time(14, 0)
        end = time(21, 0)
        if now > start and now < end:
            tickets = self.db.getAllTickets("price_level") + self.db.getAllTickets(
                "ema"
            )
            await pollTickets(tickets, self.db, self.bot)


clientSecret = os.environ["CLIENT_SECRET"]
bot = commands.Bot(command_prefix="$")

bot.add_cog(Commands(bot))
print("Started bot")
bot.run(clientSecret)
