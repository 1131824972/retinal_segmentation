from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from models.report import Report
from models.patient import Patient
from models.prediction import Prediction
from models.image import Image
from core.database import db
from services.report_service import report_service
from bson.objectid import ObjectId

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportRequest(BaseModel):
    patient_id: str
    prediction_id: str
    doctor_name: str
    diagnosis_text: str
    conclusion: str


@router.post("/generate")
async def generate_report(payload: ReportRequest):
    """
    1. 接收前端填写的医生诊断信息
    2. 保存到数据库
    """
    # 检查关联数据是否存在
    patient = await Patient.find_by_id(payload.patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    # 保存报告
    report = Report(**payload.dict())
    report_id = await report.save()

    return {"status": "success", "report_id": report_id, "message": "Report created"}


@router.get("/{report_id}/download")
async def download_report_pdf(report_id: str):
    """
    实时生成 PDF 并返回文件流供浏览器下载
    """
    # 1. 获取所有相关数据
    report_data = await Report.find_by_id(report_id)
    if not report_data:
        raise HTTPException(404, "Report not found")

    patient_data = await Patient.find_by_id(report_data['patient_id'])
    prediction_data = await db["predictions"].find_one({"_id": ObjectId(report_data['prediction_id'])})

    # 还需要获取血管分割图的 Base64 (为了画在 PDF 上)
    # 假设我们从数据库的 images 表里通过 prediction 关联去找，或者 prediction 里存了 image_id
    # 这里简化逻辑，假设前端再调用时其实不需要重新推理，我们这里为了演示，
    # 实际项目中可能需要从 gridfs 读取图片，或者 prediction_data 里如果有存 base64 缩略图最好。
    # **注意**：为了让这个跑通，你需要确保能拿到图片数据。
    # 这里暂时用一个空的或者占位符，因为读原图比较麻烦

    # 模拟一张空白图的 Base64 防止报错
    dummy_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    pdf_buffer = report_service.generate_pdf(
        patient_data=patient_data or {},
        prediction_data=prediction_data or {},
        report_data=report_data,
        image_base64=dummy_image  # 这里以后要替换成真实的血管图 Base64
    )

    # 返回 PDF 文件流
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"}
    )