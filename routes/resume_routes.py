# routes/resume_routes.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from bson import ObjectId
from database.db_connection import resume_db
from models.resume_model import create_resume
from utils.file_handler import save_upload_file, read_file_content
from utils.auth_handler import get_current_user, require_role

router = APIRouter(prefix="", tags=["Resumes"])


# -----------------------------
# 1️⃣ Upload a new resume
# -----------------------------
@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    job_link: str | None = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload .md resume file (login required)
    """
    if resume_db is None:
        raise HTTPException(status_code=500, detail="Database not initialized.")

    # ensure only markdown files
    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Only .md files are supported.")

    # save to local folder
    saved_path = save_upload_file(file)

    # read markdown text
    content = read_file_content(saved_path)

    # create resume doc
    doc = create_resume(
        user_id=current_user["user_id"],
        filename=file.filename,
        content=content,
        job_link=job_link,
        source="user"  # mark as user-uploaded
    )

    result = resume_db["resumes"].insert_one(doc)
    return {
        "message": "Resume uploaded successfully.",
        "resume_id": str(result.inserted_id),
        "uploaded_by": current_user["email"]
    }


# -----------------------------
# 2️⃣ Get all resumes (admin only)
# -----------------------------
@router.get("/", dependencies=[Depends(require_role("admin"))])
def get_all_resumes():
    """Admin only: fetch all resumes"""
    resumes_col = resume_db["resumes"]
    resumes = list(resumes_col.find({}))
    for r in resumes:
        r["_id"] = str(r["_id"])
    return resumes


# -----------------------------
# 3️⃣ Get current user's resumes
# -----------------------------
@router.get("/my")
def get_my_resumes(current_user: dict = Depends(get_current_user)):
    """Fetch all resumes uploaded by the current user"""
    resumes_col = resume_db["resumes"]
    resumes = list(resumes_col.find({"user_id": current_user["user_id"]}))
    for r in resumes:
        r["_id"] = str(r["_id"])
    return resumes


# -----------------------------
# 4️⃣ Update resume (self or admin)
# -----------------------------
@router.put("/{resume_id}")
def update_resume(
    resume_id: str,
    new_content: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Update resume content"""
    resumes_col = resume_db["resumes"]
    resume = resumes_col.find_one({"_id": ObjectId(resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    # only owner or admin can update
    if (
        current_user["role"] != "admin"
        and resume["user_id"] != current_user["user_id"]
    ):
        raise HTTPException(status_code=403, detail="Access denied.")

    resumes_col.update_one(
        {"_id": ObjectId(resume_id)},
        {"$set": {"previous_content": resume["content"], "content": new_content}}
    )

    return {"message": "Resume updated successfully."}


# -----------------------------
# 5️⃣ Delete resume (self or admin)
# -----------------------------
@router.delete("/{resume_id}")
def delete_resume(resume_id: str, current_user: dict = Depends(get_current_user)):
    """Delete resume"""
    resumes_col = resume_db["resumes"]
    resume = resumes_col.find_one({"_id": ObjectId(resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if (
        current_user["role"] != "admin"
        and resume["user_id"] != current_user["user_id"]
    ):
        raise HTTPException(status_code=403, detail="Access denied.")

    resumes_col.delete_one({"_id": ObjectId(resume_id)})
    return {"message": "Resume deleted successfully."}
