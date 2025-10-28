# models/user_model.py
from datetime import datetime
from bson import ObjectId

def create_user(email: str, username: str, password_hash: str, role: str = "user"):
    """
    创建一个新的用户文档，准备插入 MongoDB。
    role 字段：'admin' 或 'user'（默认）
    """
    if role not in ["admin", "user"]:
        raise ValueError("Invalid role: must be 'admin' or 'user'")

    return {
        "_id": ObjectId(),
        "email": email,
        "username": username,
        "password_hash": password_hash,
        "role": role,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def serialize_user(user_doc):
    """
    将 MongoDB 返回的用户文档转换为可返回给前端的 JSON 格式。
    """
    return {
        "id": str(user_doc["_id"]),
        "email": user_doc["email"],
        "username": user_doc["username"],
        "role": user_doc.get("role", "user"),
        "created_at": user_doc.get("created_at"),
        "updated_at": user_doc.get("updated_at")
    }
