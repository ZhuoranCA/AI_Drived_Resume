import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")


USER_DB = os.getenv("USER_DB")
RESUME_DB = os.getenv("RESUME_DB")
AI_DB = os.getenv("AI_DB")
