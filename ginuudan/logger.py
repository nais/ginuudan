import logging
from pythonjsonlogger import jsonlogger


def setup_logger(name):
    logger = logging.getLogger(name)

    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)-8s %(message)s")
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    return logger
