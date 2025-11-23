from doctest import debug

from fastapi import FastAPI, Request
from routes.user_routes import router as user_router
from routes.resume_routes import router as resume_router
from routes.resume_ai_routers import router as resume_ai_router
from routes.session_routes import router as session_routes
from routes.resume_file_routers import router as resume_file

app = FastAPI(
    title="AI Resume Enhancer API",
    version="1.0.0",
    description="FastAPI backend for user registration and resume upload"
)

app.include_router(user_router, prefix="/api/users", tags=["Users"])
app.include_router(resume_router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(resume_ai_router, prefix="/api/resume/optimization", tags=["Resumes_AI"])
app.include_router(session_routes, prefix="/api/session", tags=["Session"])
app.include_router(resume_file, prefix="/api/resume-files", tags=["Resume Files"])


@app.get("/")
def root():
    return {"message": "API is running successfully!"}


@app.on_event("shutdown")
def shutdown_event():
    print("Application shutting down, MongoDB connections will close automatically.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)