# api/endpoints/routes_patient.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from passlib.hash import bcrypt
from pydantic import BaseModel
from models.patient import Patient

router = APIRouter(prefix="/patients", tags=["Patients"])


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register_user(user_data: UserRegister):
    """注册新用户（现在即病人记录） - 异步 + 线程池加密"""
    # 1. 异步检查邮箱是否存在
    if await Patient.find_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. 在线程池中运行耗时的哈希计算，避免阻塞
    password_hash = await run_in_threadpool(bcrypt.hash, user_data.password)

    # 3. 异步保存为 Patient
    new_patient = Patient(username=user_data.username,
                          password_hash=password_hash,
                          email=user_data.email,
                          display_name=user_data.username
                          )
    patient_id = await new_patient.save()

    return {"patient_id": patient_id, "message": "Registered successfully"}


@router.post("/login")
async def login_user(login_data: UserLogin):
    """用户登录（即患者登录）"""
    patient_doc = await Patient.find_by_email(login_data.email)
    if not patient_doc:
        raise HTTPException(status_code=400, detail="User not found")

    # 在线程池中校验密码
    is_valid = await run_in_threadpool(bcrypt.verify, login_data.password, patient_doc["password_hash"])
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid password")

    return {"message": "Login successful", "patient_id": str(patient_doc["_id"])}
