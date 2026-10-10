# cashflow-analyzer/src/messaging.py - COMPLETE

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import aio_pika
from aio_pika import ExchangeType, Message, connect_robust
from src.core.config import settings

logger = logging.getLogger(__name__)


class EventBus:
    """RabbitMQ event bus for async communication"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self._consumer_tags = []
        self._running = False

    async def connect(self) -> bool:
        """Connect to RabbitMQ"""
        try:
            url = f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
            self.connection = await connect_robust(url)
            self.channel = await self.connection.channel()

            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                "mpesa_events",
                ExchangeType.TOPIC,
                durable=True,
            )

            logger.info("Connected to RabbitMQ")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    async def publish(
        self, routing_key: str, data: Dict[str, Any], correlation_id: str = None
    ) -> bool:
        """Publish a message to the exchange"""
        if not self.channel or not self.exchange:
            logger.error("Cannot publish: not connected to RabbitMQ")
            return False

        try:
            message = Message(
                body=json.dumps(data).encode(),
                content_type="application/json",
                correlation_id=correlation_id,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )

            await self.exchange.publish(
                message,
                routing_key=routing_key,
            )

            logger.info(f"Published message to {routing_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False

    async def consume(self, queue_name: str, routing_key: str, callback: Callable):
        """Consume messages from a queue"""
        if not self.channel:
            logger.error("Cannot consume: not connected to RabbitMQ")
            return

        try:
            # Declare queue
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
            )

            # Bind to exchange
            await queue.bind(
                self.exchange,
                routing_key=routing_key,
            )

            logger.info(f"Consuming from {queue_name} on {routing_key}")

            # Start consuming
            await queue.consume(
                callback=self._message_handler,
                no_ack=False,
            )

        except Exception as e:
            logger.error(f"Failed to consume: {e}")

    async def _message_handler(self, message: aio_pika.IncomingMessage):
        """Handle incoming messages"""
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                logger.info(f"Received message: {message.routing_key}")

                # Pass to the callback
                await self._current_callback(body) if self._current_callback else None

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Reject and requeue
                await message.nack(requeue=True)

    async def is_connected(self) -> bool:
        """Check if connected to RabbitMQ"""
        return self.connection is not None and not self.connection.is_closed

    async def close(self):
        """Close connection"""
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")
