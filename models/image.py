# models/image.py
from datetime import datetime
from core.database import images_collection
from bson.objectid import ObjectId

class Image:
    def __init__(self, user_id: str = None, patient_id: str = None, filename: str = None, file_size: int = 0, content_type: str = None, filepath: str = None, width: int = None, height: int = None):
        # 兼容旧字段 user_id，并增加 patient_id（不会破坏旧数据）
        self.user_id = user_id
        self.patient_id = patient_id
        self.filename = filename
        self.file_size = file_size
        self.content_type = content_type
        self.filepath = filepath
        self.width = width
        self.height = height
        self.uploaded_at = datetime.utcnow()

    async def save(self):
        """异步保存图像记录"""
        result = await images_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    async def find_by_user(cls, user_id: str):
        """按原逻辑保留：根据上传者 user_id 查询"""
        cursor = images_collection.find({"user_id": user_id})
        return await cursor.to_list(length=100)

    @classmethod
    async def find_by_patient(cls, patient_id: str):
        """新增：根据 patient_id 查询该病人的所有图像"""
        cursor = images_collection.find({"patient_id": patient_id})
        return await cursor.to_list(length=100)

    @classmethod
    async def find_by_id(cls, image_id: str):
        try:
            doc = await images_collection.find_one({"_id": ObjectId(image_id)})
            return doc
        except Exception:
            return None
