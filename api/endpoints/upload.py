from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time
import logging
import uuid

from core.config import settings, ALLOWED_CONTENT_TYPES
from services.model_service import model_service
from utils.image_utils import base64_to_image, validate_image_size, format_file_size, get_image_info

logger = logging.getLogger(__name__)
router = APIRouter()


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


class ModelInfoResponse(BaseModel):
    """模型信息响应模型"""
    model_name: str
    model_version: str
    status: str
    input_size: str
    output_type: str
    description: str
    supported_formats: list
    performance: Dict[str, str]
    integration_status: str


@router.post("/upload/predict",
             response_model=FileUploadResponse,
             summary="文件上传预测",
             description="通过文件上传方式进行视网膜血管分割预测")
async def predict_from_upload(file: UploadFile = File(...)):
    """
    文件流方式上传图像并进行预测

    支持直接拖拽或选择图像文件，自动检测文件格式和验证图像有效性
    """
    start_time = time.time()
    request_id = f"file_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    logger.info(f"📤 文件上传请求 {request_id} - 文件名: {file.filename}")

    try:
        # 1. 验证文件类型
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "request_id": request_id,
                    "error_code": "UNSUPPORTED_TYPE",
                    "message": f"不支持的文件类型: {file.content_type}。支持的类型: {', '.join(settings.ALLOWED_IMAGE_TYPES)}",
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )

        # 2. 读取并验证文件大小
        contents = await file.read()
        file_size = len(contents)

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "request_id": request_id,
                    "error_code": "FILE_TOO_LARGE",
                    "message": f"文件过大: {format_file_size(file_size)}。最大支持: {format_file_size(settings.MAX_FILE_SIZE)}",
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "request_id": request_id,
                    "error_code": "EMPTY_FILE",
                    "message": "文件为空",
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )

        # 3. 检测文件格式
        detected_format = ALLOWED_CONTENT_TYPES[file.content_type]

        # 4. 将文件内容转换为图像并进行验证
        import base64
        image_base64 = base64.b64encode(contents).decode('utf-8')
        image = base64_to_image(image_base64)

        if image is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "request_id": request_id,
                    "error_code": "INVALID_IMAGE",
                    "message": "上传的文件不是有效的图像格式",
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

        # 6. 获取图像详细信息
        image_info = get_image_info(image)

        formatted_size = format_file_size(file_size)

        processing_time = time.time() - start_time

        logger.info(f"✅ 文件上传成功 {request_id}")
        logger.info(f"📊 文件详情 - 名称: {file.filename}, 大小: {formatted_size}, 格式: {detected_format}")
        logger.info(f"🖼️ 图像信息 - 尺寸: {image_info['dimensions']}, 通道: {image_info['channels']}")

        return FileUploadResponse(
            status="success",
            request_id=request_id,
            message=f"文件 '{file.filename}' 上传成功，等待模型集成后返回分割结果",
            filename=file.filename,
            file_size=formatted_size,
            detected_format=detected_format,
            image_info=image_info,
            processing_time=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 文件上传失败 {request_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "request_id": request_id,
                "error_code": "UPLOAD_FAILED",
                "message": f"文件处理失败: {str(e)}",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
        )


@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """获取模型详细信息接口"""
    model_info = model_service.get_model_info()

    return ModelInfoResponse(
        model_name=model_info["model_name"],
        model_version=model_info["model_version"],
        status=model_info["status"],
        input_size=model_info["input_size"],
        output_type=model_info["output_type"],
        description=model_info["description"],
        supported_formats=model_info["supported_formats"],
        performance=model_info["performance"],
        integration_status=model_info["integration_status"]
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