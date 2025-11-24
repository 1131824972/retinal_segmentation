# models/prediction.py
from datetime import datetime
from core.database import predictions_collection
from bson.objectid import ObjectId

class Prediction:
    def __init__(self, request_id: str, model_version: str, result_data: dict, user_id: str = None, patient_id: str = None, image_id: str = None, mask_file: str = None, overlay_file: str = None):
        self.request_id = request_id
        self.model_version = model_version
        self.result_data = result_data or {}
        # 兼容旧字段 user_id，同时增加 patient_id 和 image_id
        self.user_id = user_id
        self.patient_id = patient_id
        self.image_id = image_id
        self.mask_file = mask_file
        self.overlay_file = overlay_file
        self.created_at = datetime.utcnow()

    async def save(self):
        """异步保存预测结果"""
        result = await predictions_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    async def find_by_image(cls, image_id: str):
        """异步查询某张图的所有预测记录"""
        cursor = predictions_collection.find({"image_id": image_id})
        return await cursor.to_list(length=100)

    @classmethod
    async def find_by_patient(cls, patient_id: str):
        cursor = predictions_collection.find({"patient_id": patient_id})
        return await cursor.to_list(length=100)

    @classmethod
    async def find_by_id(cls, pred_id: str):
        try:
            return await predictions_collection.find_one({"_id": ObjectId(pred_id)})
        except Exception:
            return None
