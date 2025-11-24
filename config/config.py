import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")


USER_DB = os.getenv("USER_DB")
RESUME_DB = os.getenv("RESUME_DB")
AI_DB = os.getenv("AI_DB")
CHAT_DB = os.getenv("CHAT_DB")

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "20.151.88.17")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "coen6313")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "coen6313")
RABBITMQ_VIRTUAL_HOST = os.getenv("RABBITMQ_VIRTUAL_HOST", "/")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "user-events")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")