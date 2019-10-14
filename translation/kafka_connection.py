import ast
import warnings

from translation import config, logger
from translation.main import translate_one_row
from kafka import KafkaConsumer, KafkaProducer


def convert_message_to_dict(message):
    if type(message) is str:
        logger.debug("converting string message to dictionary")
        return ast.literal_eval(message)


def translate_message(message):
    """

    :param message:
    :return:
    """
    message = message.value.decode(config.KAFKA_ENCODING)
    if type(message) is not dict:
        warnings.warn("Messages should be of type dictionary")
        message = convert_message_to_dict(message)
    translation = translate_one_row(convert_message_to_dict(message.get("content")), list(message.get("columns")))
    return translation


def send_translation_back(translation, topic):
    """

    :param translation:
    :param topic:
    """
    print("Entered send_to_kafka; topic: " + str(topic) + "; data: " + str(translation))
    producer = KafkaProducer(bootstrap_servers='localhost:9092', api_version=(0, 10))
    ack = producer.send(topic=topic, value=str(translation).encode("UTF-32"))

    producer.flush()
    metadata = ack.get()
    logger.info("Sent " + str(translation) + " to Kafka through the topic " + str(metadata.topic) +
                 " and partition " + str(metadata.partition))


def start_translate_from_kafka(topics_incoming, topic_translation):
    """
    Subscribe to topics and read in the messages from there. The messages should be of type dictionary with the headers
    as the keys and the information to translate as the values.
    :param topic_translation: Kafka topic to which translations should be returned
    :param topics_incoming: Kafka topics to subscribe to for receiving content to translate
    """

    # Config logging file
    logger.basicConfig(handlers=[logger.FileHandler(config.LOGGING_FILE, "w", config.LOGGING_ENCODING)],
                        level=config.LOGGING_LEVEL, format=config.LOGGING_FORMAT, datefmt=config.LOGGING_DATE_FORMAT)

    consumer = KafkaConsumer(bootstrap_servers=config.IP_AND_PORT, api_version=config.API_VERSIONS,
                             consumer_timeout_ms=config.CONSUMER_TIMEOUT)
    for topic in topics_incoming:
        consumer.subscribe(topic)
        logger.info("Topic subscribed: " + str(topic))
    for message in consumer:
        logger.info("New Message received: " + str(message))
        translation = translate_message(message)
        send_translation_back(translation, topic_translation)
