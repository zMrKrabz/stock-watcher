def priceLevelAdapter(doc: tuple):
    return {
        "type": "price_level",
        "symbol": doc[0],
        "price": doc[1],
        "margin": doc[2],
        "id": doc[3],
        "timestamp": doc[4],
    }


def emaAdapter(doc: tuple):
    return {
        "type": "ema",
        "symbol": doc[0],
        "price": doc[1],
        "margin": doc[2],
        "id": doc[3],
        "timestamp": doc[4],
    }
