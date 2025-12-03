"""
文件上传预测模块 (Upload Prediction Module)
------------------------------------------
本模块负责处理通过文件上传方式进行的血管分割请求。
它包含以下核心功能：
1. 接收前端上传的图片文件 (PNG, JPG, GIF, TIFF 等)。
2. 进行严格的文件校验 (大小、格式、有效性)。
3. 调用 ModelService 进行 AI 推理。
4. 将原始图片和预测结果异步存入数据库。
5. 返回包含 Base64 结果图和医学指标的 JSON 响应。
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import time
import logging
import uuid
import base64

from core.config import settings, ALLOWED_CONTENT_TYPES
from services.model_service import model_service
from utils.image_utils import base64_to_image, validate_image_size, format_file_size, get_image_info

from models.image import Image
from models.prediction import Prediction
from .predict import ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class FileUploadResponse(BaseModel):
    status: str
    request_id: str
    message: str
    filename: str
    file_size: str
    detected_format: str
    image_info: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    result_image: Optional[str] = None
    confidence: Optional[float] = None
    vessel_coverage: Optional[float] = None


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
        #user_id: Optional[str] = Form(None),
        patient_id: Optional[str] = Form(None)
):
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
                img_record = Image(
                    #user_id=user_id or "anonymous",
                    patient_id=patient_id or "anonymous",
                    filename=file.filename,
                    file_size=file_size,
                    content_type=file.content_type
                )
                image_db_id = await img_record.save()

                pred_record = Prediction(
                    request_id=request_id,
                    model_version=getattr(model_service, "model_version", "unknown"),
                    result_data={
                        "confidence": prediction_result.get("confidence"),
                        "vessel_coverage": prediction_result.get("vessel_coverage"),
                        "processing_time": processing_time,
                        "image_db_id": image_db_id
                    },
                    #user_id=user_id or "anonymous",
                    patient_id=patient_id or "anonymous",
                    image_id=image_db_id
                )
                await pred_record.save()
                logger.info(f"💾 [DB] 已保存记录 (ID: {image_db_id})")
            except Exception as db_e:
                logger.error(f"⚠️ [DB] 保存失败: {db_e}")

        if prediction_result["status"] != "success":
            raise HTTPException(status_code=500, detail=prediction_result)

        logger.info(f"✅ 预测成功 {request_id}")

        return FileUploadResponse(
            status="success",
            request_id=request_id,
            message=f"文件 '{file.filename}' 处理成功",
            filename=file.filename,
            file_size=formatted_size,
            detected_format=detected_format,
            image_info=image_info,
            processing_time=processing_time,
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
