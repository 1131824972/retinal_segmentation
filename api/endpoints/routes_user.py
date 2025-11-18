# api/endpoints/routes_user.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from models.user import User

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: str = ""


@router.post("/register")
async def register_user(payload: UserRegister):
    exists = await User.find_by_email(payload.email)
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = bcrypt.hash(payload.password)
    user = User(username=payload.username, password_hash=password_hash, email=payload.email)
    user_id = await user.save()
    return {"status": "success", "user_id": user_id}


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
async def login_user(payload: UserLogin):
    user_doc = await User.find_by_email(payload.email)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt.verify(payload.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"status": "success", "user_id": str(user_doc["_id"])}
