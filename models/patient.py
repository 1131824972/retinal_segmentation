# models/patient.py
from datetime import datetime
from core.database import patients_collection
from bson.objectid import ObjectId

class Patient:
    def __init__(self, username: str, password_hash: str, email: str = None, display_name: str = None):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.display_name = display_name
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    async def save(self):
        """异步保存 patient（保留原异步风格）"""
        data = self.__dict__.copy()
        result = await patients_collection.insert_one(data)
        return str(result.inserted_id)

    @classmethod
    async def find_by_email(cls, email: str):
        """根据 email 查询（异步）"""
        return await patients_collection.find_one({"email": email})

    @classmethod
    async def find_by_username(cls, username: str):
        """根据 username 查询（异步）"""
        return await patients_collection.find_one({"username": username})

    @classmethod
    async def find_by_id(cls, patient_id: str):
        """根据 ObjectId 查找（异步）"""
        try:
            return await patients_collection.find_one({"_id": ObjectId(patient_id)})
        except Exception:
            return None
