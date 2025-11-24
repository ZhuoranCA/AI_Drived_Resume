import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.user_routes import router as user_router
from routes.resume_routes import router as resume_router
from routes.resume_ai_routers import router as resume_ai_router
from routes.session_routes import router as session_routes
from routes.resume_file_routers import router as resume_file

from services.rabbitmq_listener_service import start_listening, stop_listening
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Resume Enhancer API",
    version="1.0.0",
    description="FastAPI backend for user registration and resume upload"
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api/users", tags=["Users"])
app.include_router(resume_router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(resume_ai_router, prefix="/api/resume/optimization", tags=["Resumes_AI"])
app.include_router(session_routes, prefix="/api/session", tags=["Session"])
app.include_router(resume_file, prefix="/api/resume-files", tags=["Resume Files"])


@app.get("/")
def root():
    return {"message": "API is running successfully!"}


@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")

    def run_listener():
        start_listening()

    threading.Thread(target=run_listener, daemon=True).start()
    logger.info("RabbitMQ listener started in background thread")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    try:
        stop_listening()
        logger.info("RabbitMQ listener stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping RabbitMQ listener: {e}", exc_info=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
