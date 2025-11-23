from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import time
import logging
import uuid
import base64

from core.config import settings, ALLOWED_CONTENT_TYPES
from services.model_service import model_service
from utils.image_utils import base64_to_image, validate_image_size, format_file_size, get_image_info

# 1. 导入所需的数据库模型
from models.image import Image
from models.prediction import Prediction
from .predict import ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# === 修复 1: 更新响应模型，添加结果字段 ===
class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    status: str
    request_id: str
    message: str
    filename: str
    file_size: str
    detected_format: str
    image_info: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    # 👇 新增：必须把这些字段加回来，前端才能收到数据！
    result_image: Optional[str] = None
    confidence: Optional[float] = None
    vessel_coverage: Optional[float] = None


# === 修复 2: 更新模型信息响应，兼容真实模型 ===
class ModelInfoResponse(BaseModel):
    """模型信息响应模型"""
    model_name: str
    version: Optional[str] = None  # 改为可选，兼容不同命名
    status: str
    input_size: Optional[str] = "512x512"
    device: Optional[str] = "CPU/GPU"  # 新增字段
    # 把旧字段设为可选，防止报错
    output_type: Optional[str] = None
    description: Optional[str] = None
    supported_formats: Optional[List[str]] = None
    performance: Optional[Dict[str, str]] = None
    integration_status: Optional[str] = None


@router.post("/upload/predict",
             response_model=FileUploadResponse,
             summary="文件上传预测",
             description="通过文件上传方式进行视网膜血管分割预测",
             responses={
                 500: {"model": ErrorResponse},
                 400: {"model": ErrorResponse},
             },
             )
async def predict_from_upload(
        file: UploadFile = File(...),
        user_id: Optional[str] = Form(None)
):
    """
    文件流方式上传图像并进行预测
    """
    start_time = time.time()
    request_id = f"file_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    logger.info(f"📤 文件上传请求 {request_id} - 文件名: {file.filename}")

    try:
        # --- 验证阶段 ---
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail={"status": "error", "message": "Unsupported file type"})

        contents = await file.read()
        file_size = len(contents)

        if file_size > settings.MAX_FILE_SIZE or file_size == 0:
            raise HTTPException(status_code=400, detail={"status": "error", "message": "File size invalid"})

        detected_format = ALLOWED_CONTENT_TYPES.get(file.content_type, "unknown")

        # 转换图像
        image_base64 = base64.b64encode(contents).decode('utf-8')
        image = base64_to_image(image_base64)

        if image is None:
            raise HTTPException(status_code=400, detail={"status": "error", "message": "Invalid image data"})

        is_valid, error_msg = validate_image_size(
            image,
            min_size=(100, 100),
            max_size=(settings.MAX_IMAGE_DIMENSION, settings.MAX_IMAGE_DIMENSION)
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail={"status": "error", "message": error_msg})

        image_info = get_image_info(image)

        # --- 预测阶段 ---
        prediction_result = await model_service.predict(image, request_id)
        processing_time = time.time() - start_time
        formatted_size = format_file_size(file_size)

        # --- 数据库集成阶段 ---
        if prediction_result["status"] == "success":
            try:
                # 保存图片
                img_record = Image(
                    user_id=user_id or "anonymous",
                    filename=file.filename,
                    file_size=file_size,
                    content_type=file.content_type
                )
                image_db_id = await img_record.save()

                # 保存预测
                pred_record = Prediction(
                    request_id=request_id,
                    model_version=getattr(model_service, "model_version", "unknown"),
                    result_data={
                        "confidence": prediction_result.get("confidence"),
                        "vessel_coverage": prediction_result.get("vessel_coverage"),
                        "processing_time": processing_time,
                        "image_db_id": image_db_id
                    },
                    user_id=user_id or "anonymous"
                )
                await pred_record.save()
                logger.info(f"💾 [DB] 已保存记录 (ID: {image_db_id})")
            except Exception as db_e:
                logger.error(f"⚠️ [DB] 保存失败: {db_e}")

        # --- 返回结果 (修复重点) ---
        # 如果预测失败，抛出异常
        if prediction_result["status"] != "success":
            raise HTTPException(status_code=500, detail=prediction_result)

        logger.info(f"✅ 预测成功 {request_id}")

        # 👇 这里把 result_image 等字段填进去，前端就能收到了！
        return FileUploadResponse(
            status="success",
            request_id=request_id,
            message=f"文件 '{file.filename}' 处理成功",
            filename=file.filename,
            file_size=formatted_size,
            detected_format=detected_format,
            image_info=image_info,
            processing_time=processing_time,
            # 新增字段赋值：
            result_image=prediction_result.get("result_image"),
            confidence=prediction_result.get("confidence"),
            vessel_coverage=prediction_result.get("vessel_coverage")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "request_id": request_id,
                "error_code": "INTERNAL_ERROR",
                "message": str(e),
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
        )


@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """获取模型详细信息接口 (兼容真实模型)"""
    # 获取服务里的原始信息
    raw_info = model_service.get_model_info()

    # 手动映射，防止 KeyError
    return ModelInfoResponse(
        model_name=raw_info.get("model_name", "Unknown Model"),
        version=raw_info.get("version") or raw_info.get("model_version"),
        status=raw_info.get("status", "unknown"),
        input_size=raw_info.get("input_size", "N/A"),
        device=raw_info.get("device", "CPU"),
        # 其他字段给默认值
        description=raw_info.get("description", "PyTorch Inference Model"),
        supported_formats=["PNG", "JPG", "BMP", "GIF", "TIFF","TIF"],
        integration_status="Ready"
    )


@router.get("/model/stats")
async def get_model_stats():
    """获取模型统计信息"""
    stats = model_service.get_service_stats()
    return {
        "status": "success",
        "model_stats": stats,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }