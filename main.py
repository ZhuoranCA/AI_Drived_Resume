from fastapi import FastAPI
from routes.user_routes import router as user_router
from routes.resume_routes import router as resume_router

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

@app.get("/")
def root():
    return {"message": "API is running successfully!"}
