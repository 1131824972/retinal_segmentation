from datetime import datetime
from core.database import models_collection

class ModelInfo:
    def __init__(self, model_version: str, model_metadata: dict):
        self.model_version = model_version
        self.model_metadata = model_metadata
        self.trained_at = datetime.datetime.utcnow()

    def save(self):
        result = models_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    def find_by_version(cls, version: str):
        return models_collection.find_one({"model_version": version})
