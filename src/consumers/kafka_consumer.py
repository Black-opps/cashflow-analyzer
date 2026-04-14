"""
Kafka consumer for categorized transactions with health checks.
"""
import asyncio
import json
import logging
from typing import Optional
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, errors as kafka_errors

from ..core.config import settings

logger = logging.getLogger(__name__)


class KafkaHealthCheck:
    """Kafka connection health checker."""
    
    def __init__(self):
        self.status = "unknown"
    
    async def check_connection(self) -> dict:
        """Check Kafka connectivity."""
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                request_timeout_ms=5000
            )
            await producer.start()
            await producer.stop()
            self.status = "healthy"
            return {"status": "healthy", "message": "Kafka connection successful"}
        except Exception as e:
            self.status = "unhealthy"
            return {"status": "unhealthy", "message": str(e), "note": "Kafka not required for basic operation"}


class TransactionConsumer:
    """Consumes categorized transactions from Kafka."""
    
    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.health_check = KafkaHealthCheck()
        self.running = False
        self.analyzer = None
        self.processed_count = 0
    
    async def start(self):
        """Start the Kafka consumer (gracefully handles missing Kafka)."""
        try:
            from ..services.analyzer import CashflowAnalyzer
            self.analyzer = CashflowAnalyzer()
            
            self.consumer = AIOKafkaConsumer(
                settings.KAFKA_CATEGORIZED_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                max_poll_records=100,
                request_timeout_ms=10000,
                session_timeout_ms=6000
            )
            
            await self.consumer.start()
            self.running = True
            logger.info(f"✅ Kafka consumer started. Listening to: {settings.KAFKA_CATEGORIZED_TOPIC}")
            
            async for msg in self.consumer:
                if not self.running:
                    break
                await self.process_message(msg)
            
        except kafka_errors.KafkaConnectionError as e:
            logger.warning(f"⚠️ Kafka not available: {e}")
            logger.warning("Running without Kafka - will not process real-time transactions")
            self.running = False
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            self.running = False
    
    async def stop(self):
        """Stop the Kafka consumer."""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        if self.analyzer:
            self.analyzer.close()
        logger.info("Kafka consumer stopped")
    
    async def process_message(self, msg):
        """Process a single Kafka message."""
        try:
            transaction = msg.value
            self.processed_count += 1
            logger.debug(f"Processing transaction #{self.processed_count}: {transaction.get('id', 'unknown')}")
            
            await self.analyzer.update_metrics(transaction)
            await self.consumer.commit()
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def get_health(self) -> dict:
        """Get consumer health status."""
        kafka_status = await self.health_check.check_connection()
        
        return {
            "consumer_running": self.running,
            "topic": settings.KAFKA_CATEGORIZED_TOPIC if self.running else "not connected",
            "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "kafka": kafka_status,
            "messages_processed": self.processed_count,
            "note": "Kafka is optional - service works without it"
        }


# Global consumer instance
consumer = TransactionConsumer()


async def get_consumer_health() -> dict:
    """Get consumer health for API endpoint."""
    return await consumer.get_health()
def get_consumer_health():
    """
    Kafka consumer health status check.
    Returns basic connectivity info.
    """
    return {
        "status": "ok",
        "consumer": "running",
        "service": "cashflow-analyzer"
    }