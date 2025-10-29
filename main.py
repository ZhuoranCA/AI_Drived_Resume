from fastapi import FastAPI
from routes.user_routes import router as user_router
from routes.resume_routes import router as resume_router


app = FastAPI(
    title="AI Resume Enhancer API",
    version="1.0.0",
    description="FastAPI backend for user registration and resume upload"
)

app.include_router(user_router, prefix="/api/users", tags=["Users"])
app.include_router(resume_router, prefix="/api/resumes", tags=["Resumes"])

@app.get("/")
def root():
    return {"message": "API is running successfully!"}

@app.on_event("shutdown")
def shutdown_event():
    print("Application shutting down, MongoDB connections will close automatically.")
