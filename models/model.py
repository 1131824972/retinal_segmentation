from datetime import datetime
from core.database import models_collection
from typing import List, Dict, Any

class ModelInfo:
    def __init__(self, model_version: str, model_metadata: dict):
        self.model_version = model_version
        self.model_metadata = model_metadata
        self.trained_at = datetime.utcnow()

    async def save(self):
        data = self.__dict__
        result = await models_collection.insert_one(data)
        return str(result.inserted_id)

    @classmethod
    async def find_by_version(cls, version: str):
        return await models_collection.find_one({"model_version": version})

    @classmethod
    async def list_models(cls) -> List[Dict[str, Any]]:
        """获取所有模型记录"""
        cursor = models_collection.find({}).sort("trained_at", -1)
        return await cursor.to_list(length=100)