from pymongo import MongoClient

try:
    mongo_client = MongoClient("mongodb://admin:COEN6313@20.151.88.17:27017/")
    print("Connected to MongoDB successfully.")
except Exception as e:
    print("Failed to connect to MongoDB:", e)
    mongo_client = None

user_db = mongo_client["user_db"] if mongo_client else None
resume_db = mongo_client["resume_db"] if mongo_client else None
chat_db = mongo_client["chat_db"] if mongo_client else None


# --- Close Connection (optional utility) ---
def close_mongo_connection():
    if mongo_client:
        mongo_client.close()
        print("🟡 MongoDB connection closed.")
