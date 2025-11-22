from datetime import datetime
from core.database import images_collection
from bson.objectid import ObjectId

class Image:
    def __init__(self, user_id: str, filename: str, file_size: int, content_type: str):
        self.user_id = user_id
        self.filename = filename
        self.file_size = file_size
        self.content_type = content_type
        self.uploaded_at = datetime.utcnow()

    async def save(self):
        """异步保存图像记录"""
        result = await images_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    async def find_by_user(cls, user_id: str):
        """异步查找用户的所有图像"""
        cursor = images_collection.find({"user_id": user_id})
        # motor cursor 需要用 to_list 转换
        return await cursor.to_list(length=100)