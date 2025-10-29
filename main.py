from fastapi import FastAPI
from routes.user_routes import router as user_router
from routes.resume_routes import router as resume_router
from routes.resume_ai_routers import router as resume_ai_router
from routes.session_routes import router as session_routes
from routes.resume_file_routers import router as resume_file

# We no longer import connect_to_mongo, only close if needed
from database.db_connection import close_mongo_connection

app = FastAPI(
    title="AI Resume Enhancer API",
    version="1.0.0",
    description="FastAPI backend for user registration and resume upload"
)

# Register routers
app.include_router(user_router, prefix="/api/users", tags=["Users"])
app.include_router(resume_router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(resume_ai_router, prefix="/api/resume/optimization", tags=["Resumes_AI"])
app.include_router(session_routes, prefix="/api/session", tags=["Session"])
app.include_router(resume_file, prefix="/api/resume-files", tags=["Resume Files"])

@app.get("/")
def root():
    return {"message": "API is running successfully!"}
