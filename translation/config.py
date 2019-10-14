# coding=utf-8
import os
import yaml
import logging
from translation import logger

# Translation Configuration Information
COLUMNS_TO_TRANSLATE = ["country", "company"]  # list of strings
# csv file to translate
FILE_TO_TRANSLATE = "trans_test_input.csv"
# results from translated file - must be a .csv file name
FILE_TRANSLATED_RESULT = "trans_test_output.csv"

# Kafka Configuration Information
KAFKA_ENCODING = "utf-8"
KAFKA_IP = ""
PORT = "9092"
IP_AND_PORT = str(KAFKA_IP) + ":" + str(PORT)
API_VERSIONS = (0, 10)
CONSUMER_TIMEOUT = 100000  # in ms

# Logging Configuration Information
LOGGING_FILE = 'Translationlogger.log'
LOGGING_FORMAT = '%(asctime)s - %(levelname)s\t%(filename)s %(lineno)d: %(funcName)s() - %(message)s'
LOGGING_LEVEL = logging.DEBUG
LOGGING_DATE_FORMAT = '%m/%d/%Y %I:%M:%S %p'
LOGGING_ENCODING = "utf-8"


def init_config() -> dict:
    try:
        config = yaml.load(open('resources/default_config.yml', 'r'), Loader=yaml.FullLoader)
        logger.info('Application Config loaded!')
        return config
    except FileNotFoundError:
        logger.exception("Failed to read config file!")


def get_yandex_api_key():
    return conf["Yandex_API_Key"]


conf = init_config()
