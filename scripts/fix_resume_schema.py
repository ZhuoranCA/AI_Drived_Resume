# scripts/fix_resume_schema.py
from pymongo import MongoClient
from datetime import datetime

try:
    client = MongoClient("mongodb://localhost:27017/")
    resume_db = client["resume_db"]
    resumes = resume_db["resumes"]
    print("Connected to MongoDB: resume_ai_db")
except Exception as e:
    print("MongoDB connection failed:", e)
    exit(1)

def migrate_resume_documents():
    """
    Update all resume documents to match the new schema.
    Adds missing fields and removes deprecated ones.
    """
    updated_count = 0
    total_docs = resumes.count_documents({})
    print(f"Found {total_docs} resume documents.")

    for doc in resumes.find({}):
        update_fields = {}

        # --- Ensure all new fields exist ---
        if "previous_content" not in doc:
            update_fields["previous_content"] = None

        if "source" not in doc:
            update_fields["source"] = "user"

        if "uploaded_at" not in doc:
            update_fields["uploaded_at"] = datetime.utcnow()

        if "updated_at" not in doc:
            update_fields["updated_at"] = datetime.utcnow()

        # --- Optional: remove old unexpected fields ---
        deprecated_fields = ["old_version", "backup_content", "ai_generated"]
        for f in deprecated_fields:
            if f in doc:
                update_fields[f] = None  # Or use $unset if you prefer

        # --- Apply update if needed ---
        if update_fields:
            resumes.update_one({"_id": doc["_id"]}, {"$set": update_fields})
            updated_count += 1

    print(f"Migration complete. Updated {updated_count} documents.")
    return updated_count

if __name__ == "__main__":
    migrate_resume_documents()
    client.close()
    print("MongoDB connection closed.")
