from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from passlib.hash import bcrypt
from pydantic import BaseModel
from models.user import User  # 确保这一行导入了你的 User 模型

router = APIRouter(prefix="/users", tags=["Users"])


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register_user(user_data: UserRegister):
    """注册新用户 (异步 + 线程池加密)"""
    # 1. 异步检查邮箱是否存在
    if await User.find_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. 在线程池中运行耗时的哈希计算，避免阻塞
    password_hash = await run_in_threadpool(bcrypt.hash, user_data.password)

    # 3. 异步保存
    new_user = User(username=user_data.username, password_hash=password_hash, email=user_data.email)
    user_id = await new_user.save()

    return {"user_id": user_id, "message": "User registered successfully"}


@router.post("/login")
async def login_user(login_data: UserLogin):
    """用户登录"""
    # 1. 异步查找用户
    user_doc = await User.find_by_email(login_data.email)
    if not user_doc:
        raise HTTPException(status_code=400, detail="User not found")

    # 2. 在线程池中验证密码
    is_valid = await run_in_threadpool(bcrypt.verify, login_data.password, user_doc["password_hash"])
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid password")

    return {"message": "Login successful", "user_id": str(user_doc["_id"])}