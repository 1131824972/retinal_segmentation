# models/image.py
from datetime import datetime
from core.database import images_collection
from bson.objectid import ObjectId

class Image:
    def __init__(self, user_id: str, image_path: str, image_metadata: dict):
        self.user_id = user_id
        self.image_path = image_path
        self.image_metadata = image_metadata
        self.uploaded_at = datetime.utcnow()

    async def save(self):
        result = await images_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    async def find_by_user(cls, user_id: str):
        cursor = images_collection.find({"user_id": user_id})
        docs = await cursor.to_list(length=1000)
        return docs

    @classmethod
    async def find_by_id(cls, image_id: str):
        doc = await images_collection.find_one({"_id": ObjectId(image_id)})
        return doc
