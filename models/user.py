from datetime import datetime
from core.database import users_collection
from bson.objectid import ObjectId

class User:
    def __init__(self, username: str, password_hash: str, email: str):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    async def save(self):
        """异步保存用户"""
        user_data = self.__dict__
        # 必须使用 await
        result = await users_collection.insert_one(user_data)
        return str(result.inserted_id)

    @classmethod
    async def find_by_email(cls, email: str):
        """异步根据邮箱查找"""
        # 必须使用 await
        data = await users_collection.find_one({"email": email})
        return data

    @classmethod
    async def find_by_id(cls, user_id: str):
        """异步根据ID查找"""
        try:
            data = await users_collection.find_one({"_id": ObjectId(user_id)})
            return data
        except:
            return None