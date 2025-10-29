from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ai.resume_ai import define_graph
from database.db_connection import chat_db
from models.history_session import ChatMessage, HistorySession
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="")
sessions_collection = chat_db["sessions"]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


class Message(BaseModel):
    user_id: str
    session_id: str
    message: str


@router.post("/chat")
def chat(msg: Message):
    user_id, session_id, text = msg.user_id, msg.session_id, msg.message.strip()
    session = sessions_collection.find_one({"user_id": user_id, "session_id": session_id})
    if not session:
        title_prompt = f"Generate a short title (max 7 words) summarizing this request:\n{text}"
        title = llm.invoke([HumanMessage(content=title_prompt)]).content.strip()
        session = HistorySession(
            session_id=session_id,
            user_id=user_id,
            title=title or "New Resume Optimization",
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ).dict()
        sessions_collection.insert_one(session)

    state = {
        "user_message": text,
        "resume_md": session.get("resume_md", ""),
        "jd_md": session.get("jd_md", ""),
        "goal": session.get("goal", ""),
        "final_resume": session.get("final_resume", ""),
        "response": ""
    }

    graph = define_graph()
    compiled = graph.compile()
    result = compiled.invoke(state)
    reply = result.get("response", "No response generated.")

    user_msg = ChatMessage(role="user", content=text)
    ai_msg = ChatMessage(role="assistant", content=reply)

    sessions_collection.update_one(
        {"user_id": user_id, "session_id": session_id},
        {
            "$push": {"messages": {"$each": [user_msg.dict(), ai_msg.dict()]}},
            "$set": {
                "resume_md": result.get("resume_md", session.get("resume_md", "")),
                "jd_md": result.get("jd_md", session.get("jd_md", "")),
                "goal": result.get("goal", session.get("goal", "")),
                "final_resume": result.get("final_resume", session.get("final_resume", "")),
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"reply": reply}


@router.get("/history/{user_id}/{session_id}")
def get_chat_history(user_id: str, session_id: str):
    session = sessions_collection.find_one({"user_id": user_id, "session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "title": session.get("title", ""),
        "messages": session.get("messages", [])
    }


@router.get("/health")
def health():
    return {"status": "ok"}
