from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time
import logging
import uuid

from core.config import settings
from services.model_service import model_service
from utils.image_utils import base64_to_image, validate_image_size, get_image_info

from fastapi_limiter.depends import RateLimiter

logger = logging.getLogger(__name__)
router = APIRouter()


class Base64PredictionRequest(BaseModel):
    """Base64预测请求模型"""
    image_data: str = Field(
        ...,
        description="Base64编码的图像数据，可包含data URI前缀",
        min_length=100,
        example="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    image_format: str = Field(
        default="png",
        description="图像格式：png, jpg, jpeg",
        example="png"
    )

    class Config:
        schema_extra = {
            "example": {
                "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                "image_format": "png"
            }
        }


class PredictionResponse(BaseModel):
    """预测响应模型"""
    status: str
    request_id: str
    message: str
    processing_time: Optional[float] = None
    image_info: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    vessel_coverage: Optional[float] = None
    result_image: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    status: str = "error"
    request_id: str
    error_code: str
    message: str
    timestamp: str


@router.post("/predict",
             response_model=PredictionResponse,
             responses={
                 400: {"model": ErrorResponse},
                 500: {"model": ErrorResponse},
                 429: {"model": ErrorResponse}, # (可选) 告诉文档有 429 错误
             },
             # 使用 settings 中的配置来限流
             dependencies=[Depends(RateLimiter(
                 times=settings.MAX_REQUESTS_PER_MINUTE,
                 seconds=60
             ))]
            )
async def predict_from_base64(request: Base64PredictionRequest):
    """
    Base64格式图像上传与预测

    支持包含data URI前缀的base64字符串，自动进行图像验证和预处理
    """
    start_time = time.time()
    request_id = f"base64_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    logger.info(f"📨 收到Base64预测请求 {request_id}")

    try:
        # 1. 验证图像格式
        allowed_formats = ["png", "jpg", "jpeg"]
        if request.image_format.lower() not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "request_id": request_id,
                    "error_code": "INVALID_FORMAT",
                    "message": f"不支持的图像格式: {request.image_format}。支持: {', '.join(allowed_formats)}",
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )

        # 2. 处理base64数据
        base64_data = request.image_data
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',')[1]

        # 3. 验证base64数据
        if len(base64_data) < 100:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "request_id": request_id,
                    "error_code": "INVALID_DATA",
                    "message": "图像数据过短，可能不是有效的base64编码",
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )

        # 4. 转换base64为图像
        image = base64_to_image(base64_data)
        if image is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "request_id": request_id,
                    "error_code": "DECODE_FAILED",
                    "message": "图像数据格式错误，无法解码",
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )

        # 5. 验证图像尺寸
        is_valid, error_msg = validate_image_size(
            image,
            min_size=(100, 100),
            max_size=(settings.MAX_IMAGE_DIMENSION, settings.MAX_IMAGE_DIMENSION)
        )

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "request_id": request_id,
                    "error_code": "INVALID_DIMENSIONS",
                    "message": error_msg,
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )

        # 6. 获取图像信息
        image_info = get_image_info(image)
        logger.info(f"🖼️ 图像验证成功 {request_id} - 尺寸: {image_info['dimensions']}")

        # 7. 调用模型服务进行预测
        prediction_result = await model_service.predict(image, request_id)

        processing_time = time.time() - start_time

        if prediction_result["status"] == "success":
            logger.info(f"✅ 预测成功 {request_id}")
            return PredictionResponse(
                status="success",
                request_id=request_id,
                message=prediction_result["message"],
                processing_time=processing_time,
                image_info=image_info,
                confidence=prediction_result.get("confidence"),
                vessel_coverage=prediction_result.get("vessel_coverage"),
                result_image=prediction_result.get("result_image")
            )
        else:
            logger.error(f"❌ 预测失败 {request_id}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "request_id": request_id,
                    "error_code": "PREDICTION_FAILED",
                    "message": prediction_result["message"],
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 预测接口异常 {request_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "request_id": request_id,
                "error_code": "INTERNAL_ERROR",
                "message": f"服务器内部错误: {str(e)}",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
        )


@router.get("/predict/status")
async def get_prediction_status():
    """获取预测服务状态"""
    stats = model_service.get_service_stats()

    return {
        "status": "success",
        "service": "prediction",
        "model_loaded": stats["model_loaded"],
        "total_predictions": stats["total_predictions"],
        "service_status": stats["service_status"],
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }