from datetime import datetime
from core.database import predictions_collection

class Prediction:
    def __init__(self, request_id: str, model_version: str, result_data: dict, user_id: str = None):
        self.request_id = request_id
        self.model_version = model_version
        self.result_data = result_data
        self.user_id = user_id
        self.created_at = datetime.utcnow()

    async def save(self):
        """异步保存预测结果"""
        result = await predictions_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    async def find_by_image(cls, image_id: str):
        """异步查询某张图的所有预测记录"""
        # Motor 的 find 返回一个 cursor，需要用 to_list 转换为列表
        cursor = predictions_collection.find({"image_id": image_id})
        return await cursor.to_list(length=100)