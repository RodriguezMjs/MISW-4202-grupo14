"""
RabbitMQ Consumer example.
Consumes item events from the queue (standalone service).
"""
import pika
import json
import time
import logging
from config import RABBITMQ_URL

# Configurar logging para salida inmediata
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ItemConsumer:
    """Consume item events from RabbitMQ."""

    def __init__(self, queue_name="item_events"):
        self.queue_name = queue_name
        self.channel = None

    def connect(self):
        """Connect to RabbitMQ."""
        retries = 5
        while retries > 0:
            try:
                self.connection = pika.BlockingConnection(
                    pika.URLParameters(RABBITMQ_URL)
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                logger.info(f"✓ Connected to RabbitMQ, listening on queue '{self.queue_name}'")
                return True
            except Exception as e:
                logger.warning(
                    f"Error connecting to RabbitMQ (retry {6-retries}/5): {e}"
                )
                retries -= 1
                time.sleep(2)
        return False

    def on_message(self, ch, method, properties, body):
        """Handle incoming messages."""
        try:
            message = json.loads(body)
            event_type = message.get('event_type', 'unknown')
            data = message.get('data', {})
            logger.info(f"[EVENT CONSUMED] Type: {event_type} | Data: {data}")
            # TODO: Process the event (e.g., update cache, log, send notification)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug(f"Message acknowledged (delivery_tag: {method.delivery_tag})")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start(self):
        """Start consuming messages."""
        if not self.connect():
            logger.error("Failed to connect to RabbitMQ. Exiting.")
            return

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name, on_message_callback=self.on_message
        )
        logger.info("👂 Waiting for messages...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
            self.channel.stop_consuming()
            self.connection.close()


if __name__ == "__main__":
    consumer = ItemConsumer()
    consumer.start()
