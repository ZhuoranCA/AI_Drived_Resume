from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from typing import List
from database.db_connection import resume_db
from models.resume_file import ResumeFile

router = APIRouter()
resume_files_collection = resume_db["resume_files"]


def file_to_dict(f):
    if "_id" in f:
        f["_id"] = str(f["_id"])
    return f


@router.get("/", response_model=List[ResumeFile])
def list_all_files():
    files = list(resume_files_collection.find().sort("created_at", -1))
    return [file_to_dict(f) for f in files]


@router.get("/user/{user_id}", response_model=List[ResumeFile])
def list_user_files(user_id: str):
    files = list(resume_files_collection.find({"user_id": user_id}).sort("created_at", -1))
    return [file_to_dict(f) for f in files]


@router.get("/{file_id}", response_model=ResumeFile)
def get_file(file_id: str):
    file = resume_files_collection.find_one({"file_id": file_id})
    if not file:
        raise HTTPException(status_code=404, detail="Resume file not found")
    return file_to_dict(file)


@router.post("/", response_model=ResumeFile, status_code=status.HTTP_201_CREATED)
def create_file(file: ResumeFile):
    existing = resume_files_collection.find_one({"file_id": file.file_id})
    if existing:
        raise HTTPException(status_code=400, detail="File already exists")

    file_data = file.dict()
    file_data["created_at"] = datetime.utcnow()
    resume_files_collection.insert_one(file_data)
    return file_to_dict(file_data)


@router.delete("/{file_id}")
def delete_file(file_id: str):
    result = resume_files_collection.delete_one({"file_id": file_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resume file not found")
    return {"message": f"Resume file {file_id} deleted successfully"}
