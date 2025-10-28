# models/resume_model.py
from datetime import datetime
from bson import ObjectId

def create_resume(
    user_id: str,
    filename: str,
    content: str,
    job_link: str = None,
    previous_content: str = None,
    source: str = "user"
):
    """
    Create a new resume document for MongoDB insertion.
    New strict version — no backward compatibility.
    """
    if source not in ["user", "ai"]:
        raise ValueError("Invalid source: must be 'user' or 'ai'")

    return {
        "_id": ObjectId(),
        "user_id": user_id,               # uploader id
        "filename": filename,             # e.g. resume.md
        "content": content,               # current resume content
        "previous_content": previous_content,  # last version
        "job_link": job_link,             # optional job description link
        "source": source,                 # 'user' or 'ai'
        "uploaded_at": datetime.utcnow(), # first creation time
        "updated_at": datetime.utcnow()   # last updated time
    }
