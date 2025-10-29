from fastapi import APIRouter, status
from typing import List
from models.resume_file import ResumeFile
from services.resume_file_service import ResumeFileService

router = APIRouter()
service = ResumeFileService()


@router.get("/", response_model=List[ResumeFile])
def list_all_files():
    return service.list_all_files()


@router.get("/user/{user_id}", response_model=List[ResumeFile])
def list_user_files(user_id: str):
    return service.list_user_files(user_id)


@router.get("/{file_id}", response_model=ResumeFile)
def get_file(file_id: str):
    return service.get_file(file_id)


@router.post("/", response_model=ResumeFile, status_code=status.HTTP_201_CREATED)
def create_file(file: ResumeFile):
    return service.create_file(file)


@router.delete("/{file_id}")
def delete_file(file_id: str):
    service.delete_file(file_id)
    return {"message": f"Resume file {file_id} deleted successfully"}
