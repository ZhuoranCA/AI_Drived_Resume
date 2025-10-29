from datetime import datetime
from pydantic import BaseModel, EmailStr
from bson import ObjectId


class User(BaseModel):
    id: str | None = None
    email: EmailStr
    username: str | None = None
    password: str | None = None
    role: str = "user"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        orm_mode = True


def create_user(email: str, username: str, password_hash: str, role: str = "user"):
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
    return User(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        username=user_doc["username"],
        role=user_doc.get("role", "user"),
        created_at=user_doc.get("created_at"),
        updated_at=user_doc.get("updated_at")
    )
