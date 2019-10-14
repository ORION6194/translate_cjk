# coding=utf-8
import sys
import yaml
import logging

# Translation Configuration Information
COLUMNS_TO_TRANSLATE = ["country", "company"]  # list of strings
# csv file to translate
FILE_TO_TRANSLATE = "resources/sample_input.txt"

# results from translated file - must be a .csv file name
FILE_TRANSLATED_RESULT = "sample_output.csv"

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
        print('Application Config loaded!')
        return config
    except FileNotFoundError:
        print("Failed to read config file!")
        import traceback
        traceback.print_exc()
        sys.exit()


def get_yandex_api_key():
    return conf["Yandex_API_Key"]


conf = init_config()
