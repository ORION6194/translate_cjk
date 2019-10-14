from kafka import KafkaProducer

from translation_module import logger


def send_to_kafka(topic, data):
    print("Entered send_to_kafka; topic: " + str(topic) + "; data: " + str(data))
    producer = KafkaProducer(bootstrap_servers='localhost:9092', api_version=(0, 10))
    ack = producer.send(topic=topic, value=str(data).encode("UTF-32"))

    producer.flush()
    metadata = ack.get()
    logger.info("Sent " + str(data) + " to Kafka through the topic " + str(metadata.topic) +
                " and partition " + str(metadata.partition))


def run():
    topic_data_dict = {"translation1": {"country": "China", "Account Name": "Tom4",
                                        "AccountNumber": "1324234"}}
    for topic, data in topic_data_dict.items():
        send_to_kafka(topic, data)


print("Start testProducerToKafka")
run()
print("End testProducerToKafka")
