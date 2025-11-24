from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ai.resume_ai import define_graph
from database.db_connection import chat_db
from models.history_session import ChatMessage, HistorySession
from utils.rabbitmq_handler import send_event_to_rabbitmq
from dotenv import load_dotenv
import re

load_dotenv()

router = APIRouter(prefix="")
sessions_collection = chat_db["sessions"]

# Global model configuration (default: gpt-4o-mini)
current_global_model = "gpt-4o-mini"
llm = ChatOpenAI(model=current_global_model, temperature=0.3)

# Available OpenAI models list
AVAILABLE_MODELS = [
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": ""},
    {"id": "gpt-4o", "name": "GPT-4o", "description": ""},
    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": ""},
]


class Message(BaseModel):
    user_id: str
    session_id: str
    message: str


class ModelSwitchRequest(BaseModel):
    model: str


@router.get("/models")
def get_available_models():
    """Get list of available AI models"""
    return {"models": AVAILABLE_MODELS}


@router.get("/model/current")
def get_current_model():
    """Get the currently active global model"""
    return {"model": current_global_model}


@router.post("/model/switch")
def switch_model(request: ModelSwitchRequest):
    """Switch the global model"""
    global current_global_model, llm
    
    model_name = request.model
    
    # Validate model is in the supported list
    valid_models = [m["id"] for m in AVAILABLE_MODELS]
    if model_name not in valid_models:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model_name}. Supported models: {', '.join(valid_models)}")
    
    # Update global model
    current_global_model = model_name
    llm = ChatOpenAI(model=current_global_model, temperature=0.3)
    
    return {"message": f"Model switched to: {model_name}", "model": current_global_model}


@router.post("/chat")
def chat(msg: Message):
    global current_global_model, llm

    user_id, session_id, text = msg.user_id, msg.session_id, msg.message.strip()

    # Use global model
    model_name = current_global_model

    session = sessions_collection.find_one({"user_id": user_id, "session_id": session_id})
    if not session:
        # Use global model to generate title when creating new session
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

    # Create graph using selected global model
    graph = define_graph(model_name=model_name, temperature=0.6)
    compiled = graph.compile()
    result = compiled.invoke(state)
    reply = result.get("response", "No response generated.")

    raw_resume_md = result.get("resume_md", session.get("resume_md", ""))
    cleaned_resume_md = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", raw_resume_md.strip(), flags=re.MULTILINE)

    user_msg = ChatMessage(role="user", content=text)
    ai_msg = ChatMessage(role="assistant", content=reply)

    sessions_collection.update_one(
        {"user_id": user_id, "session_id": session_id},
        {
            "$push": {"messages": {"$each": [user_msg.dict(), ai_msg.dict()]}},
            "$set": {
                "resume_md": cleaned_resume_md,
                "jd_md": result.get("jd_md", session.get("jd_md", "")),
                "goal": result.get("goal", session.get("goal", "")),
                "final_resume": result.get("final_resume", session.get("final_resume", "")),
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Send CHAT event to RabbitMQ
    event_detail = f"User {user_id} sent a chat message in session {session_id}"
    send_event_to_rabbitmq(user_id, "CHAT", event_detail)
    
    return {
        "reply": reply,
        "resume_md": cleaned_resume_md,
        "model": model_name
    }


@router.get("/history/{user_id}/{session_id}")
def get_chat_history(user_id: str, session_id: str):
    """Return the full conversation history for a session."""
    session = sessions_collection.find_one({"user_id": user_id, "session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "title": session.get("title", ""),
        "messages": session.get("messages", [])
    }


@router.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
