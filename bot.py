import aiohttp
import asyncio
import time
import os
import discord
from discord.ext import tasks, commands
from checker import pollTickers

tickets = []


class Commands(commands.Cog):
    """Basic commands for the bot"""

    @commands.command(name="tickets")
    async def getTickets(self, ctx):
        """
        Replies with all the tickets that are currently being monitored
        """
        message = ""
        for t in tickets:
            if t["type"] == "price_level":
                message += (
                    f"Watching for {t['symbol']} to go {t['signal']} {t['price']}\n"
                )
            elif t["type"] == "ema":
                message += f"Watching for {t['symbol']} to touch ema at {t['interval']} candle in {t['time_period']} periods"

        if message == "":
            message = "There are no tickets being monitored"
        await ctx.send(message)

    @commands.command(name="price")
    async def price(self, ctx, symbol: str, price: float, signal: str):
        """
        Add a price level ticket to monitor
        symbol should be capitalized stock ticker
        price should be the price in float (ex. 60.1)
        signal should be "ABOVE" or "BELOW"
        """

        if price < 0:
            await ctx.send("Price can not be below 0")
            return

        if (signal == "ABOVE") or (signal == "BELOW"):
            tickets.append(
                {
                    "type": "price_level",
                    "symbol": symbol.upper(),
                    "price": price,
                    "signal": signal,
                }
            )
            await ctx.send("Successfully added price level signal to tickets")
        else:
            await ctx.send(f"You sent {signal}. Signal must be ABOVE or BELOW")

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
        tickets.append(ticket)
        await ctx.send("Successfully added EMA signal to tickets")


@tasks.loop(seconds=5.0)
async def monitorTickets():
    global tickets
    newTickets = await pollTickers(tickets)
    tickets = newTickets


monitorTickets.start()

clientSecret = os.environ["CLIENT_SECRET"]
bot = commands.Bot(command_prefix="$")

bot.add_cog(Commands())
bot.run(clientSecret)