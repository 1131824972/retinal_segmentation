from datetime import datetime
from core.database import predictions_collection
from bson.objectid import ObjectId

class Prediction:
    def __init__(self, image_id: str, model_version: str, prediction_data: dict):
        self.image_id = image_id
        self.model_version = model_version
        self.prediction_data = prediction_data
        self.predicted_at = datetime.utcnow()

    def save(self):
        result = predictions_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    def find_by_image(cls, image_id: str):
        cursor = predictions_collection.find({"image_id": image_id})
        return list(cursor)
