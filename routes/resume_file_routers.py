from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List
from bson import ObjectId
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException

from models.resume_file import ResumeFile
from services.resume_file_service import ResumeFileService
from utils.auth_handler import get_current_user, require_role

router = APIRouter()
service = ResumeFileService()
security = HTTPBearer()



# -----------------------------
#  Resume File APIs
# -----------------------------

@router.get("", response_model=List[ResumeFile])
def list_all_files(current_user: dict = Depends(get_current_user)):
    # 只有管理员可以查看所有文件
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")
    return service.list_all_files()


@router.get("/user/{user_id}", response_model=List[ResumeFile])
def list_user_files(user_id: str, current_user: dict = Depends(get_current_user)):
    # 普通用户只能查看自己的文件
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return service.list_user_files(user_id)


@router.get("/{file_id}", response_model=ResumeFile)
def get_file(file_id: str, current_user: dict = Depends(get_current_user)):
    resume = service.get_file(file_id)

    if not resume:
        raise HTTPException(status_code=404, detail="File not found.")

    # 权限验证
    if current_user["role"] != "admin" and resume.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    return resume

@router.post("/", response_model=ResumeFile, status_code=201)
def create_file(
    file: UploadFile = File(...),
    file_name: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    # 权限验证：普通用户只能创建自己的
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return service.create_file(file, file_name,  user_id)

@router.put("/{resume_id}/file-id")
def update_file_id(
    resume_id: str,
    new_file_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    resume = service.get_file(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    updated_resume = service.update_file_id(resume_id, new_file_id)

    return {
        "message": "File ID updated successfully",
        "new_file_id": new_file_id
    }

# -----------------------------
#  Delete Resume (权限保护)
# -----------------------------
@router.delete("/{file_id}")
def delete_file(file_id: str, current_user: dict = Depends(get_current_user)):
    resume = service.get_file(file_id)

    if not resume:
        raise HTTPException(status_code=404, detail="File not found.")
    user_id = current_user["user_id"]
    if current_user["role"] != "admin" and user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    service.delete_file(file_id)
    return {"message": f"Resume file {file_id} deleted successfully"}
