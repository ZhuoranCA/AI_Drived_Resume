from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from typing import List
from database.db_connection import chat_db
from models.history_session import HistorySession, HistorySessionUpdate

router = APIRouter(prefix="")
sessions_collection = chat_db["sessions"]


def session_to_dict(s):
    if "_id" in s:
        s["_id"] = str(s["_id"])
    return s


@router.get("/user/{user_id}", response_model=List[HistorySession])
def list_user_sessions(user_id: str):
    sessions = list(
        sessions_collection.find({"user_id": user_id}).sort("updated_at", -1)
    )
    return [session_to_dict(s) for s in sessions]


@router.post("/", response_model=HistorySession, status_code=status.HTTP_201_CREATED)
def create_session(session: HistorySession):
    existing = sessions_collection.find_one({"session_id": session.session_id})
    if existing:
        raise HTTPException(status_code=400, detail="Session already exists")

    session_data = session.dict()
    session_data["created_at"] = datetime.utcnow()
    session_data["updated_at"] = datetime.utcnow()
    sessions_collection.insert_one(session_data)
    return session_to_dict(session_data)


@router.get("/{session_id}", response_model=HistorySession)
def get_session(session_id: str):
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_to_dict(session)


@router.get("/{session_id}/history")
def get_chat_history(session_id: str):
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "title": session.get("title", ""),
        "messages": session.get("messages", []),
    }


@router.delete("/{session_id}")
def delete_session(session_id: str):
    result = sessions_collection.delete_one({"session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": f"Session {session_id} deleted successfully"}


@router.patch("/{session_id}/title", response_model=HistorySession)
def update_session_title(session_id: str, update: HistorySessionUpdate):
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if update.title is None:
        raise HTTPException(status_code=400, detail="Title cannot be null")

    sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "title": update.title,
                "updated_at": datetime.utcnow()
            }
        }
    )

    updated = sessions_collection.find_one({"session_id": session_id})
    return session_to_dict(updated)