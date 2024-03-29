import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mpdates
import mplfinance as mpf

plt.style.use("ggplot")

raw = [
    {
        "v": 101835618.0,
        "vw": 129.3241,
        "o": 129.19,
        "c": 128.98,
        "h": 130.17,
        "l": 128.5,
        "t": 1610341200000,
    },
    {
        "v": 92999622.0,
        "vw": 128.4814,
        "o": 128.5,
        "c": 128.8,
        "h": 129.69,
        "l": 126.86,
        "t": 1610427600000,
    },
    {
        "v": 89531128.0,
        "vw": 130.5583,
        "o": 128.76,
        "c": 130.89,
        "h": 131.45,
        "l": 128.49,
        "t": 1610514000000,
    },
    {
        "v": 91382447.0,
        "vw": 129.7361,
        "o": 130.8,
        "c": 128.91,
        "h": 131,
        "l": 128.76,
        "t": 1610600400000,
    },
    {
        "v": 115563418.0,
        "vw": 128.2605,
        "o": 128.78,
        "c": 127.14,
        "h": 130.2242,
        "l": 127,
        "t": 1610686800000,
    },
    {
        "v": 92197017.0,
        "vw": 127.6965,
        "o": 127.78,
        "c": 127.83,
        "h": 128.71,
        "l": 126.938,
        "t": 1611032400000,
    },
    {
        "v": 106196122.0,
        "vw": 131.466,
        "o": 128.66,
        "c": 132.03,
        "h": 132.49,
        "l": 128.55,
        "t": 1611118800000,
    },
    {
        "v": 122789843.0,
        "vw": 135.8597,
        "o": 133.8,
        "c": 136.87,
        "h": 139.67,
        "l": 133.59,
        "t": 1611205200000,
    },
    {
        "v": 116272839.0,
        "vw": 137.8565,
        "o": 136.28,
        "c": 139.07,
        "h": 139.85,
        "l": 135.02,
        "t": 1611291600000,
    },
    {
        "v": 155217709.0,
        "vw": 142.6006,
        "o": 143.07,
        "c": 142.92,
        "h": 145.09,
        "l": 136.54,
        "t": 1611550800000,
    },
]
df = pd.DataFrame(raw)
print(df)
# df["t"] = pd.to_datetime(df["t"])
df.index = pd.DatetimeIndex(df["t"])
df["Date"] = df["t"]
df["Open"] = df["o"]
df["High"] = df["h"]
df["Low"] = df["l"]
df["Close"] = df["c"]
df["Volume"] = df["v"]
mpf.plot(df, type="candle", volume=True)
