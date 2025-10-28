# routes/user_routes.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from bson import ObjectId
from database.db_connection import user_db
from models.user_model import create_user
from utils.auth_handler import create_access_token, get_current_user, require_role

router = APIRouter(prefix="", tags=["Users"])

# -----------------------------
# Pydantic Schemas
# -----------------------------
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"  # default: normal user


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None


# -----------------------------
# Routes
# -----------------------------

@router.post("/register")
def register_user(user: UserRegister):
    """Register new user"""
    if user_db is None:
        raise HTTPException(status_code=500, detail="Database not initialized.")

    users_col = user_db["users"]

    if users_col.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed_pw = bcrypt.hash(user.password[:72])
    new_user = create_user(email=user.email, username=user.username, password_hash=hashed_pw)
    new_user["role"] = user.role

    result = users_col.insert_one(new_user)
    return {"message": "User registered successfully.", "user_id": str(result.inserted_id)}


@router.post("/login")
def login_user(user: UserLogin):
    """Login user and return JWT token"""
    users_col = user_db["users"]
    found = users_col.find_one({"email": user.email})
    if not found or not bcrypt.verify(user.password, found["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({
        "user_id": str(found["_id"]),
        "email": found["email"],
        "role": found.get("role", "user")
    })

    return {"access_token": token, "token_type": "bearer"}


@router.get("/", dependencies=[Depends(require_role("admin"))])
def get_all_users():
    """Admin only: Get all users"""
    users_col = user_db["users"]
    users = list(users_col.find({}, {"password_hash": 0}))
    for u in users:
        u["_id"] = str(u["_id"])
    return users


@router.get("/{user_id}")
def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get user details (self or admin)"""
    users_col = user_db["users"]
    user = users_col.find_one({"_id": ObjectId(user_id)}, {"password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # only self or admin can view
    if str(current_user["user_id"]) != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")

    user["_id"] = str(user["_id"])
    return user


@router.put("/{user_id}")
def update_user(user_id: str, update: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update username/password (self or admin)"""
    users_col = user_db["users"]
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if str(current_user["user_id"]) != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")

    update_fields = {}
    if update.username:
        update_fields["username"] = update.username
    if update.password:
        update_fields["password_hash"] = bcrypt.hash(update.password[:72])

    users_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    return {"message": "User updated successfully."}


@router.delete("/{user_id}", dependencies=[Depends(require_role("admin"))])
def delete_user(user_id: str):
    """Admin only: Delete user"""
    users_col = user_db["users"]
    result = users_col.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "User deleted successfully."}
