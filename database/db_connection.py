from pymongo import MongoClient
from config.config import MONGO_URI, USER_DB, RESUME_DB, AI_DB
from urllib.parse import urlparse

try:
    client = MongoClient(MONGO_URI)

    user_db = client[USER_DB]
    resume_db = client[RESUME_DB]
    resume_ai_db = client[AI_DB]

    parsed = urlparse(MONGO_URI)
    host_info = parsed.hostname or "Unknown host"
    conn_type = "CLOUD (MongoDB Atlas)" if "mongodb+srv" in MONGO_URI else "LOCAL (localhost)"

    print("Connected to MongoDB cluster:")
    print(f"   Host: {host_info}")
    print(f"   Type: {conn_type}")
    print(f"   - User DB: {USER_DB}")
    print(f"   - Resume DB: {RESUME_DB}")
    print(f"   - AI DB: {AI_DB}")

except Exception as e:
    print("Failed to connect to MongoDB:", e)
    user_db = None
    resume_db = None
    resume_ai_db = None
