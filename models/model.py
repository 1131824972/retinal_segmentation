# models/model.py
from datetime import datetime
from core.database import models_collection
from bson.objectid import ObjectId

class ModelInfo:
    def __init__(self, model_version: str, model_metadata: dict):
        self.model_version = model_version
        self.model_metadata = model_metadata
        self.trained_at = datetime.utcnow()

    async def save(self):
        result = await models_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    async def find_by_version(cls, version: str):
        doc = await models_collection.find_one({"model_version": version})
        return doc

    @classmethod
    async def list_models(cls, limit: int = 100):
        cursor = models_collection.find().sort("trained_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return docs
