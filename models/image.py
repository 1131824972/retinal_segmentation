from datetime import datetime
from core.database import images_collection
from bson.objectid import ObjectId

class Image:
    def __init__(self, user_id: str, image_path: str, image_metadata: dict):
        self.user_id = user_id
        self.image_path = image_path
        self.image_metadata = image_metadata
        self.uploaded_at = datetime.utcnow()

    def save(self):
        result = images_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    def find_by_user(cls, user_id: str):
        cursor = images_collection.find({"user_id": user_id})
        return list(cursor)

    @classmethod
    def find_by_id(cls, image_id: str):
        return images_collection.find_one({"_id": ObjectId(image_id)})
