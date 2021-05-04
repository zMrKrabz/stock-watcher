import aiohttp
import asyncio
import time
import os
import discord
from discord.ext import tasks, commands
from discord.ext import menus
import time
from typing import List
from sql import SQL
from db import Ticket
import traceback
from custom_logger import get_logger
from alpaca_v1 import Alpaca_V1
from tdameritrade_api import TdAmeritradeAPI
import datetime
import holidays
import pytz
from price import Price

os.environ['TZ'] = 'utc'
time.tzset()

logger = get_logger(__name__)

class TicketsMenu(menus.ListPageSource):
    def __init__(self, tickets):
        """
        Takes raw tickets and formats them into messages that appear on a menu
        """
        super().__init__(tickets, per_page=10)

    async def format_page(self, menu, entries: List[Ticket]):
        data = []
        for t in entries:
            data.append(str(t))

        message = "\n".join(d for d in data)
        return message


tz = pytz.timezone("US/Eastern")


def after_hours(now=datetime.datetime.now(tz)):
    """
    Returns true if in after hours, false if in trading hours
    """
    open_time = datetime.time(hour=9, minute=30)
    close_time = datetime.time(hour=16)

    if now.strftime('%Y-%m-%d') in holidays.US():
        return True

    if now.time() < open_time or now.time() > close_time:
        return True

    if now.date().weekday() > 4:
        return True

    return False


class Commands(commands.Cog):
    """Basic commands for the bot"""

    def __init__(self, bot):
        self.bot = bot
        self.db = SQL('alerts.db')
        self.api = TdAmeritradeAPI()
        self.monitor.start()

    @commands.command(name="get")
    async def get(self, ctx, symbol="*", category="*"):
        """
        symbol - optional, only get tickets of specific stock
        category - optional, only get specific category, such as EMA or Price
        returns all tickets based on parameters
        """

        tickets = []
        if category == '*':
            tickets += self.db.get_all_ema(ctx.author.id, symbol=symbol)
            tickets += self.db.get_all_price(ctx.author.id, symbol=symbol)
        elif category == 'ema':
            tickets += self.db.get_all_ema(ctx.author.id, symbol=symbol)
        elif category == 'price':
            tickets += self.db.get_all_price(ctx.author.id, symbol=symbol)

        if len(tickets) < 1:
            await ctx.send(f"You have not entered any tickets <@{ctx.author.id}>")
            return

        len_str = f"You are currently watching {len(tickets)} "

        if symbol != "*":
            len_str += symbol + " "
        
        if category != "*":
            len_str += category + " "

        len_str += "tickets"
        await ctx.send(len_str)

        pages = menus.MenuPages(source=TicketsMenu(tickets), clear_reactions_after=True)
        await pages.start(ctx)

    @get.error
    async def get_error(self, ctx, error):
        await ctx.send(error)

    @commands.group(invoke_without_command=True)
    async def add(self, ctx: commands.Context):
        """
        Categories: price, ema
        """
        await ctx.send("Please specify a category: price, ema")

    @add.command(name="price")
    async def price(self, ctx: commands.Context, symbol: str, price: float, margin=1.0):
        """
        symbol - stock symbol
        price - price to watch for
        margin - dollar amount to for current and target price to differ by, optional

        Adds price ticket to database
        """
        _id = self.db.add_price(
            symbol=symbol,
            price=price,
            channelID=ctx.channel.id,
            author=ctx.author.id,
            margin=margin
        )
        await ctx.send(f"Added price ticket (ID: {_id})")

    @price.error
    async def add_price_error(self, ctx: commands.Context, error):
        await ctx.send(error)

    @add.command(name="ema")
    async def ema(self, ctx: commands.Context, symbol: str, timeframe: str, periods: str, multiplier=1, margin=0.001):
        """
        symbol - Ticker you want to put 
        timeframe - which candle to use: minute, hour, day, week, month
        periods - how many candles to use to calculate ema (8,21,50,200)
        multiplier - how many timeframes to use, ex: 4 as multiplier and hour as timeframe would result in 4H candles used
        margin - the % amount the EMA value and current price should differ by

        Adds ema ticket to database
        """
        _id = self.db.add_ema(
            symbol=symbol,
            timeframe=timeframe,
            periods=int(periods),
            channelID=ctx.channel.id,
            author=ctx.author.id,
            multiplier=multiplier,
            margin=margin,
        )
        await ctx.send(f"Added EMA ticket (ID: {_id})")

    @ema.error
    async def add_ema_error(self, ctx: commands.Context, error):
        await ctx.send(error)

    @commands.command(name="delete")
    async def delete(self, ctx: commands.Context, _id: str):
        self.db.delete(_id)
        await ctx.send(f"Deleted id: {_id}")

    @delete.error
    async def delete_error(self, ctx: commands.Context, error):
        await ctx.send(error)

    @tasks.loop(seconds=5)
    async def monitor(self):
        await self.bot.wait_until_ready()
        if after_hours():
            return

        # tickets = []
        # tickets += self.db.get_all_ema(active=True)
        # tickets += self.db.get_all_price(active=True)

        # logger.info(f"Monitoring {len(tickets)} tickets")
        start = time.perf_counter()

        async def send(message: str, channelID: int, authorID: int, _id: str, calculated_timeout: int) -> None:
            channel = self.bot.get_channel(channelID)

            if channel == None:
                logger.error(f"Could not find channel for {channelID} for {authorID}")
                self.db.delete(_id)

            try:
                await channel.send(message)

                timeout = int(time.time()) + calculated_timeout
                self.db.update_timeout(_id, timeout)
            except Exception:
                logger.error(f"ChannelID: {channelID}", exc_info=True)

        symbols = self.db.get_price_symbols()
        for symbol in symbols:
            tickets = self.db.get_prices(symbol)
            m = Price(symbol, prices=tickets)
            await m.monitor(self.api, send)
            await asyncio.sleep(2)

        end = time.perf_counter()
        dt = datetime.timedelta(seconds=(end-start))
        logger.info(f"Took {str(dt)} to monitor tickets")


if __name__ == "__main__":
    client_secret = os.environ["CLIENT_SECRET"]
    bot = commands.Bot(command_prefix="$")
    logger.info("Started bot")

    bot.add_cog(Commands(bot))
    bot.run(client_secret)
