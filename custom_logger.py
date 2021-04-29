import logging
import logging.handlers

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel("DEBUG")
    formatter = logging.Formatter('%(name)s [%(asctime)s] %(message)s', datefmt="%FT%T%z")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel("DEBUG")
    logger.addHandler(stream_handler)

    file_handler = logging.handlers.TimedRotatingFileHandler("logs/history.log", when="midnight", interval=1)
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel("DEBUG")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
