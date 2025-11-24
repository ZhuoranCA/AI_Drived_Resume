import json
import pika
from datetime import datetime
from config.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_VIRTUAL_HOST,
    RABBITMQ_QUEUE
)


def send_event_to_rabbitmq(user_id: str, event_type: str, event_detail: str) -> bool:
    """
    Send event message to RabbitMQ
    
    Args:
        user_id: User ID
        event_type: Event type (e.g., "REGISTER", "CHAT")
        event_detail: Event detail description
        
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    try:
        # Create connection parameters
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            virtual_host=RABBITMQ_VIRTUAL_HOST,
            credentials=credentials
        )
        
        # Create connection
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare queue (if not exists) - durable to match receiver expectations
        channel.queue_declare(
            queue=RABBITMQ_QUEUE,
            durable=True
        )
        
        # Prepare message
        message = {
            "userId": user_id,
            "eventType": event_type,
            "timestamp": int(datetime.now().timestamp() * 1000),  # milliseconds
            "eventDetail": event_detail
        }
        
        # Publish message directly to queue
        channel.basic_publish(
            exchange='',  # Empty string means default exchange (direct to queue)
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )
        
        # Close connection
        connection.close()
        
        return True
        
    except Exception as e:
        # Log error but don't fail the main operation
        print(f"Failed to send message to RabbitMQ: {str(e)}")
        return False

