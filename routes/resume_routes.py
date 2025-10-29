from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from bson import ObjectId
from datetime import datetime

from database.db_connection import resume_db
from models.resume_model import Resume, create_resume, serialize_resume
from utils.file_handler import save_upload_file, read_file_content
from utils.auth_handler import get_current_user, require_role

router = APIRouter(prefix="", tags=["Resumes"])


@router.post("/upload", response_model=Resume)
async def upload_resume(
    file: UploadFile = File(...),
    job_link: str | None = Form(None),
    current_user: dict = Depends(get_current_user)
):
    if resume_db is None:
        raise HTTPException(status_code=500, detail="Database not initialized.")

    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Only .md files are supported.")
    
    saved_path = save_upload_file(file)
    content = read_file_content(saved_path)

    doc = create_resume(
        user_id=current_user["user_id"],
        filename=file.filename,
        content=content,
        job_link=job_link,
        source="user"
    )

    result = resume_db["resumes"].insert_one(doc)
    inserted = resume_db["resumes"].find_one({"_id": result.inserted_id})
    return serialize_resume(inserted)


# @router.get("/", dependencies=[Depends(require_role("admin"))], response_model=list[Resume])
@router.get("/", response_model=list[Resume])
def get_all_resumes():
    resumes_col = resume_db["resumes"]
    resumes = list(resumes_col.find({}))
    return [serialize_resume(r) for r in resumes]


@router.get("/user/{user_id}", response_model=list[Resume])
def get_user_resumes(user_id: str):
    """
    Return all resumes that belong to a specific user.
    Example: GET /api/resumes/user/bochao
    """
    resumes_col = resume_db["resumes"]
    resumes = list(resumes_col.find({"user_id": user_id}))
    if not resumes:
        raise HTTPException(status_code=404, detail="No resumes found for this user")
    return [serialize_resume(r) for r in resumes]


@router.put("/{resume_id}")
def update_resume(
    resume_id: str,
    new_content: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    resumes_col = resume_db["resumes"]
    resume = resumes_col.find_one({"_id": ObjectId(resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if current_user["role"] != "admin" and resume["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    result = resumes_col.update_one(
        {"_id": ObjectId(resume_id)},
        {
            "$set": {
                "previous_content": resume["content"],
                "content": new_content,
                "updated_at": datetime.utcnow()
            }
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Update failed.")

    return {"message": "Resume updated successfully."}


@router.delete("/{resume_id}")
def delete_resume(resume_id: str, current_user: dict = Depends(get_current_user)):
    resumes_col = resume_db["resumes"]
    resume = resumes_col.find_one({"_id": ObjectId(resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if current_user["role"] != "admin" and resume["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    resumes_col.delete_one({"_id": ObjectId(resume_id)})
    return {"message": "Resume deleted successfully."}
