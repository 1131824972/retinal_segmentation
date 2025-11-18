from fastapi import APIRouter, HTTPException
from models.user import User
from passlib.hash import bcrypt

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register")
def register_user(username: str, email: str, password: str):
    """注册新用户"""
    if User.find_by_email(email):
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = bcrypt.hash(password)
    user = User(username=username, password_hash=password_hash, email=email)
    user_id = user.save()

    return {"user_id": user_id, "message": "User registered successfully"}


@router.post("/login")
def login_user(email: str, password: str):
    """用户登录"""
    user_data = User.find_by_email(email)
    if not user_data:
        raise HTTPException(status_code=400, detail="User not found")

    if not bcrypt.verify(password, user_data["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid password")

    return {"message": "Login successful", "user_id": str(user_data["_id"])}
