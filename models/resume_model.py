from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId


class Resume(BaseModel):
    id: str | None = None
    user_id: str
    filename: str
    content: str
    job_link: Optional[str] = None
    previous_content: Optional[str] = None
    source: str = Field(default="user", description="Document Source, either 'user' or 'ai'")
    uploaded_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        orm_mode = True


def create_resume(
        user_id: str,
        filename: str,
        content: str,
        job_link: str = None,
        previous_content: str = None,
        source: str = "user"
):
    if source not in ["user", "ai"]:
        raise ValueError("Invalid source: must be 'user' or 'ai'")

    return {
        "_id": ObjectId(),
        "user_id": user_id,
        "filename": filename,
        "content": content,
        "previous_content": previous_content,
        "job_link": job_link,
        "source": source,
        "uploaded_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def serialize_resume(resume_doc):
    return Resume(
        id=str(resume_doc["_id"]),
        user_id=resume_doc["user_id"],
        filename=resume_doc["filename"],
        content=resume_doc["content"],
        job_link=resume_doc.get("job_link"),
        previous_content=resume_doc.get("previous_content"),
        source=resume_doc.get("source", "user"),
        uploaded_at=resume_doc.get("uploaded_at"),
        updated_at=resume_doc.get("updated_at")
    )
