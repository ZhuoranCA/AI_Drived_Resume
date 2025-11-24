from fastapi import APIRouter, HTTPException, Depends
from passlib.hash import bcrypt
from bson import ObjectId
from datetime import datetime

from database.db_connection import user_db
from models.user_model import User, create_user, serialize_user
from utils.auth_handler import create_access_token, get_current_user, require_role
from utils.rabbitmq_handler import send_event_to_rabbitmq

router = APIRouter(prefix="", tags=["Users"])


@router.post("/register", response_model=User)
def register_user(user: User):
    if user_db is None:
        raise HTTPException(status_code=500, detail="Database not initialized.")

    users_col = user_db["users"]

    if users_col.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered.")

    if not user.password:
        raise HTTPException(status_code=400, detail="Password is required.")

    hashed_pw = bcrypt.hash(user.password[:72])
    new_user = create_user(email=user.email, username=user.username, password_hash=hashed_pw)
    new_user["role"] = user.role

    result = users_col.insert_one(new_user)
    inserted = users_col.find_one({"_id": result.inserted_id})
    serialized = serialize_user(inserted)
    
    # Send REGISTER event to RabbitMQ
    user_id = str(inserted["_id"])
    event_detail = f"{user.email} register"
    send_event_to_rabbitmq(user_id, "REGISTER", event_detail)
    
    return serialized


@router.post("/login")
def login_user(user: User):
    users_col = user_db["users"]
    found = users_col.find_one({"email": user.email})

    if not found or not user.password or not bcrypt.verify(user.password, found["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({
        "user_id": str(found["_id"]),
        "email": found["email"],
        "role": found.get("role", "user")
    })

    return {"access_token": token, "token_type": "bearer", "user_id": str(found["_id"])}


@router.get("/", dependencies=[Depends(require_role("admin"))])
# @router.get("/")
def get_all_users():
    users_col = user_db["users"]
    users = list(users_col.find({}, {"password_hash": 0}))
    for u in users:
        u["_id"] = str(u["_id"])
    return users


@router.get("/{user_id}", response_model=User)
def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    users_col = user_db["users"]
    user = users_col.find_one({"_id": ObjectId(user_id)}, {"password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if str(current_user["user_id"]) != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")

    return serialize_user(user)


@router.put("/{user_id}")
def update_user(user_id: str, update: User, current_user: dict = Depends(get_current_user)):
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
    if update_fields:
        update_fields["updated_at"] = datetime.utcnow()

    result = users_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes made.")

    return {"message": "User updated successfully."}


@router.delete("/{user_id}")
def delete_user(user_id: str):
    users_col = user_db["users"]
    result = users_col.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "User deleted successfully."}
