"""
RabbitMQ Producer example.
Sends messages to a queue when items are created.
"""
import pika
import json
from config import RABBITMQ_URL


class ItemProducer:
    """Publish item events to RabbitMQ."""

    def __init__(self, queue_name="item_events"):
        self.queue_name = queue_name

    def connect(self):
        """Connect to RabbitMQ."""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(RABBITMQ_URL)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
        except Exception as e:
            import logging
            logging.error(f"Error connecting to RabbitMQ: {e}")
            return False
        return True

    def publish(self, event_type, data):
        """Publish an event to the queue."""
        if not hasattr(self, "channel"):
            if not self.connect():
                return False

        message = {
            "event_type": event_type,
            "data": data,
        }
        try:
            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),  # persistent
            )
            return True
        except Exception as e:
            import logging
            logging.error(f"Error publishing message: {e}")
            return False

    def close(self):
        """Close the connection."""
        if hasattr(self, "connection"):
            self.connection.close()
