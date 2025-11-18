# models/prediction.py
from datetime import datetime
from core.database import predictions_collection
from bson.objectid import ObjectId

class Prediction:
    def __init__(self, image_id: str, model_version: str, prediction_data: dict):
        self.image_id = image_id
        self.model_version = model_version
        self.prediction_data = prediction_data
        self.predicted_at = datetime.utcnow()

    async def save(self):
        result = await predictions_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    async def find_by_image(cls, image_id: str):
        cursor = predictions_collection.find({"image_id": image_id})
        docs = await cursor.to_list(length=1000)
        return docs

    @classmethod
    async def find_by_id(cls, pid: str):
        doc = await predictions_collection.find_one({"_id": ObjectId(pid)})
        return doc
