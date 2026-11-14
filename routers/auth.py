
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import secrets
from database import get_db
from models import User
from schemas import UserCreate, UserLogin,TeacherRegister
from services.auth import (
    password_hasher,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(tags=["Authentication"])


@router.post("/register", status_code=201)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hasher.hash(user_data.password),
        role="student"
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create user"
        )

    return {
        "message": "Registration successful",
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role
    }




@router.post("/teacher/register", status_code=201)
def register_teacher(
    user_data: TeacherRegister,
    db: Session = Depends(get_db)
):
    invitation_code = os.getenv("TEACHER_INVITE_CODE")
    if not secrets.compare_digest(
        user_data.invitation_code,
        invitation_code
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid invitation code"
        )

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    new_teacher = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hasher.hash(
            user_data.password
        ),
        role="teacher"
    )

    try:
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create teacher"
        )

    return {
        "message": "Teacher registration successful",
        "id": new_teacher.id,
        "name": new_teacher.name,
        "email": new_teacher.email,
        "role": new_teacher.role
    }



@router.post("/login")
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if user is None or not password_hasher.verify(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }
