from datetime import datetime
from fastapi import HTTPException
from typing import List
from database.db_connection import resume_db
from models.resume_file import ResumeFile
import uuid
from azure.storage.blob import BlobServiceClient
import os


def _to_dict(doc: dict) -> dict:
    """Convert MongoDB _id to str for JSON serialization."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


class ResumeFileService:
    def __init__(self):
        self.collection = resume_db["resume_files"]

        self.connection_string = os.getenv("AZURE_BLOB_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_BLOB_CONTAINER")
        self.base_url = os.getenv("AZURE_BLOB_BASE_URL")

        if not self.connection_string:
            raise Exception("AZURE_BLOB_CONNECTION_STRING missing in .env")

        self.blob_service = BlobServiceClient.from_connection_string(self.connection_string)
        self.container = self.blob_service.get_container_client(self.container_name)
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

    def create_file(self, upload_file, file_name: str, user_id: str) -> dict:
        file_id = f"resume_{uuid.uuid4().hex[:10]}"

        try:
            file_bytes = upload_file.file.read()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid file upload.")

        blob_name = f"{user_id}/{file_id}.pdf"
        blob_client = self.container.get_blob_client(blob_name)

        try:
            blob_client.upload_blob(file_bytes, overwrite=True)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload PDF to Azure Blob: {str(e)}"
            )

        file_url = blob_client.url

        record = {
            "file_id": file_id,
            "user_id": user_id,
            "file_name": file_name,
            "file_url": file_url,
            "created_at": datetime.utcnow()
        }

        self.collection.insert_one(record)

        return _to_dict(record)

    def delete_file(self, file_id: str) -> None:
        result = self.collection.delete_one({"file_id": file_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Resume file not found")

    def update_file_id(self, old_file_id: str, new_file_id: str):
        collection = resume_db["resume_files"]

        result = collection.find_one_and_update(
            {"file_id": old_file_id},
            {"$set": {"file_id": new_file_id}},
            return_document=True
        )

        if not result:
            raise ValueError("Resume not found")

        # 转换成 ResumeFile 模型
        return ResumeFile(**_to_dict(result))
