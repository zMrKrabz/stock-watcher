def priceLevelAdapter(doc: tuple):
    return {
        "type": "price_level",
        "symbol": doc[0],
        "price": doc[1],
        "margin": doc[2],
        "id": doc[3],
        "timestamp": doc[4],
        "timeout": doc[5],
        "channelID": doc[6],
        "authorID": doc[7]
    }


def emaAdapter(doc: tuple):
    return {
        "type": "ema",
        "symbol": doc[0],
        "timespan": doc[1],
        "multiplier": doc[2],
        "id": doc[3],
        "timestamp": doc[4],
        "timeout": doc[5],
        "channelID": doc[6],
        "authorID": doc[7]
    }
