from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ResumeFile(BaseModel):
    file_id: str = Field(..., description="Unique identifier for the generated PDF file.")
    user_id: str = Field(..., description="The owner user ID of this resume file.")
    file_url: str = Field(..., description="Public Azure Blob URL for the stored resume PDF.")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "file_id": "resume_20251101_001",
                "user_id": "bochao",
                "file_url": "https://vffice.blob.core.windows.net/resumes/bochao_20251101_001.pdf",
                "created_at": "2025-11-01T15:20:00Z"
            }
        }
    )
