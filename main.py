

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from services.exam_security import router as exam_security_router
load_dotenv()
from database import engine, Base
from routers.teacher import router as teacher_router
import models
from database import test_connection, get_db
from models import User
from schemas import UserCreate, UserUpdate, UserLogin
from routers.auth import router as auth_router
from routers.users import router as users_router
from services.auth import require_teacher
from routers import student
from services.auth import (
    password_hasher,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


app = FastAPI(
    title="SkillBridge API",
    description="Career Readiness and Skill Development Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth_router)
app.include_router(users_router)
app.include_router(teacher_router)
app.include_router(student.router)
app.include_router(exam_security_router)
# Home
@app.get("/")
def home():
    return {
        "message": "Welcome to SkillBridge!",
        "status": "Backend is running"
    }


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Database test
@app.get("/test-db")
def test_database():
    result = test_connection()
    return {
        "database": "connected",
        "test_result": result
    }




@app.get("/me")
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }


