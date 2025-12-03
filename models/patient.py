from datetime import datetime
from core.database import patients_collection
from bson.objectid import ObjectId

class Patient:
    def __init__(self, username: str, password_hash: str, email: str = None, phone: str = None):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.phone = phone # 可以加一个手机号字段，方便联系
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    async def save(self):
        """异步保存病人信息"""
        data = self.__dict__
        result = await patients_collection.insert_one(data)
        return str(result.inserted_id)

    @classmethod
    async def find_by_email(cls, email: str):
        """根据邮箱查找"""
        return await patients_collection.find_one({"email": email})

    @classmethod
    async def find_by_username(cls, username: str):
        """根据用户名查找"""
        return await patients_collection.find_one({"username": username})

    @classmethod
    async def find_by_id(cls, patient_id: str):
        """根据ID查找"""
        try:
            return await patients_collection.find_one({"_id": ObjectId(patient_id)})
        except:
            return None