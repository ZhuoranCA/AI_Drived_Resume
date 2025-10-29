from datetime import datetime
from fastapi import HTTPException, status
from typing import List, Optional
from database.db_connection import resume_db
from models.resume_file import ResumeFile


def _to_dict(doc: dict) -> dict:
    """Convert MongoDB _id to str for JSON serialization."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


class ResumeFileService:
    """
    Service layer for managing ResumeFile records.
    Handles all database logic (CRUD).
    """

    def __init__(self):
        self.collection = resume_db["resume_files"]

    # ------------------ CRUD ------------------ #
    def list_all_files(self) -> List[dict]:
        files = list(self.collection.find().sort("created_at", -1))
        return [_to_dict(f) for f in files]

    def list_user_files(self, user_id: str) -> List[dict]:
        files = list(self.collection.find({"user_id": user_id}).sort("created_at", -1))
        return [_to_dict(f) for f in files]

    def get_file(self, file_id: str) -> dict:
        file = self.collection.find_one({"file_id": file_id})
        if not file:
            raise HTTPException(status_code=404, detail="Resume file not found")
        return _to_dict(file)

    def create_file(self, file: ResumeFile) -> dict:
        existing = self.collection.find_one({"file_id": file.file_id})
        if existing:
            raise HTTPException(status_code=400, detail="File already exists")

        file_data = file.dict()
        file_data["created_at"] = datetime.utcnow()
        self.collection.insert_one(file_data)
        return _to_dict(file_data)

    def delete_file(self, file_id: str) -> None:
        result = self.collection.delete_one({"file_id": file_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Resume file not found")
