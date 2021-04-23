"""
Command line interface for bot
"""
from alpaca_v1 import Alpaca_V1 as API
import ema
from datetime import datetime
from time import strftime
import dateutil
import pytz
import asyncio
import asyncclick as click

@click.group()
def cli():
    pass

@click.command()
async def save():
    api = API()
    symbol = input("Symbol: ")
    timeframe = input("Timeframe (minute, hour, day, week, month): ")
    multiplier = int(input("Multiplier: "))
    limit = int(input("Limit: "))
    candles = await api.get_bars(symbol, timeframe, multiplier, limit)

    add_ema = input("Add EMA? (Y/n)")

    if (add_ema == 'Y'):
        periods = int(input("Periods: "))
        ema.get(candles, periods)

    candles = candles.drop(columns=["t"])
    now = datetime.now().strftime("%Y-%m-%d")
    candles.to_csv(f'{symbol}_{multiplier}{timeframe}_{now}.csv')

@click.command()
@click.argument('t')
def utctoest(t: str):
    """
    Converts ISO8601 timestamp into EST timestamp
    """
    tz = pytz.timezone('America/New_York')
    dt = dateutil.parser.parse(t)
    converted = dt.astimezone(tz)
    print(converted.isoformat())
    
@click.command()
@click.argument('t')
def tstoest(t: int):
    """
    Converts EPOCH timestamp into EST
    """
    tz = pytz.timezone('America/New_York')
    dt = datetime.fromtimestamp(int(t))
    print(tz.localize(dt).isoformat())
    
cli.add_command(save)
cli.add_command(utctoest)
cli.add_command(tstoest)

if __name__ == '__main__':
    cli()