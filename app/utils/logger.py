from loguru import logger

logger.add(lambda msg: print(msg, end=""), level="INFO")
