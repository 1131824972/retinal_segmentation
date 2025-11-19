from datetime import datetime
from core.database import predictions_collection

class Prediction:
    def __init__(self, request_id: str, model_version: str, result_data: dict, user_id: str = None):
        self.request_id = request_id
        self.model_version = model_version
        self.result_data = result_data # 存置信度、覆盖率等，不要存巨大的base64
        self.user_id = user_id
        self.created_at = datetime.utcnow()

    async def save(self):
        """异步保存预测结果"""
        result = await predictions_collection.insert_one(self.__dict__)
        return str(result.inserted_id)