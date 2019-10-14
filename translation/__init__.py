import logging
from translation import config

logging.basicConfig(handlers=[logging.FileHandler(config.LOGGING_FILE, "w", config.LOGGING_ENCODING)],
                        level=config.LOGGING_LEVEL, format=config.LOGGING_FORMAT, datefmt=config.LOGGING_DATE_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(config.LOGGING_LEVEL)