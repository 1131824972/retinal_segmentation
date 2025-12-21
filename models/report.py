from datetime import datetime
from core.database import db
from bson.objectid import ObjectId

# 这里的 reports_collection 稍后要在 database.py 里定义
reports_collection = db["reports"]

class Report:
    def __init__(self, patient_id: str, prediction_id: str, doctor_name: str, diagnosis_text: str, conclusion: str):
        self.patient_id = patient_id        # 关联病人
        self.prediction_id = prediction_id  # 关联那次AI预测记录
        self.doctor_name = doctor_name      # 诊断医生
        self.diagnosis_text = diagnosis_text # 医生的详细描述
        self.conclusion = conclusion        # 结论 (比如：正常 / 轻度病变 / 需复查)
        self.created_at = datetime.utcnow()

    async def save(self):
        result = await reports_collection.insert_one(self.__dict__)
        return str(result.inserted_id)

    @classmethod
    async def find_by_prediction(cls, prediction_id: str):
        return await reports_collection.find_one({"prediction_id": prediction_id})

    @classmethod
    async def find_by_id(cls, report_id: str):
        try:
            return await reports_collection.find_one({"_id": ObjectId(report_id)})
        except:
            return None