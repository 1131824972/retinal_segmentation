from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time
import logging
import uuid
import base64  # 确保导入了 base64

from core.config import settings, ALLOWED_CONTENT_TYPES
from services.model_service import model_service
from utils.image_utils import base64_to_image, validate_image_size, format_file_size, get_image_info

from fastapi_limiter.depends import RateLimiter

# 1. 导入所需的数据库模型 (确保这些模型已经是异步版本)
from models.image import Image
from models.prediction import Prediction
# 2. 导入 ErrorResponse 以修复之前的 "Unresolved reference" 错误
from .predict import ErrorResponse

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
             description="通过文件上传方式进行视网膜血管分割预测",
             responses={
                 429: {"model": ErrorResponse},  # 限流错误文档
                 500: {"model": ErrorResponse},
                 400: {"model": ErrorResponse},
             },
             dependencies=[Depends(RateLimiter(
                 times=settings.MAX_REQUESTS_PER_MINUTE,
                 seconds=60
             ))]
             )
async def predict_from_upload(
        file: UploadFile = File(...),
        # 3. 新增 user_id 参数，允许前端传递用户ID (可选)
        # 使用 Form(...) 因为这是文件上传接口，参数在表单中
        user_id: Optional[str] = Form(None)
):
    """
    文件流方式上传图像并进行预测
    """
    start_time = time.time()
    request_id = f"file_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    logger.info(f"📤 文件上传请求 {request_id} - 文件名: {file.filename}")

    try:
        # --- 验证阶段 (保持不变) ---

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

        # 4. 转换图像
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

        # --- 预测阶段 ---

        # 7. 调用模型服务进行预测
        prediction_result = await model_service.predict(image, request_id)

        processing_time = time.time() - start_time
        formatted_size = format_file_size(file_size)

        # --- 数据库集成阶段 (新增部分) ---

        if prediction_result["status"] == "success":
            try:
                # 8. 保存图片记录
                # 注意：这里我们只存元数据。如果要存文件本身，通常会存到磁盘或云存储(S3)，
                # 然后把路径(image_path)存数据库。这里为简单起见，image_path 暂存文件名。
                img_record = Image(
                    user_id=user_id or "anonymous",  # 如果前端没传 user_id，记为匿名
                    filename=file.filename,
                    file_size=file_size,
                    content_type=file.content_type
                )
                # 必须使用 await，因为我们把 save 改成了 async
                image_db_id = await img_record.save()

                # 9. 保存预测结果记录
                # 我们不存result_image(base64)，因为它太大了，只存关键指标
                pred_record = Prediction(
                    request_id=request_id,
                    model_version=model_service.model_version,
                    result_data={
                        "confidence": prediction_result.get("confidence"),
                        "vessel_coverage": prediction_result.get("vessel_coverage"),
                        "processing_time": processing_time,
                        "image_db_id": image_db_id  # 关联到刚才存的图片
                    },
                    user_id=user_id or "anonymous"
                )
                await pred_record.save()

                logger.info(f"💾 [DB] 已保存图片和预测记录 (ID: {image_db_id})")

            except Exception as db_e:
                # 数据库保存失败不应该导致接口报错，因为预测本身是成功的
                # 我们只需要记录日志，然后继续返回结果给用户
                logger.error(f"⚠️ [DB] 保存记录失败: {db_e}")

        # --- 返回结果 ---

        logger.info(f"✅ 文件上传预测成功 {request_id}")

        return FileUploadResponse(
            status="success",
            request_id=request_id,
            message=f"文件 '{file.filename}' 处理成功",
            filename=file.filename,
            file_size=formatted_size,
            detected_format=detected_format,
            image_info=image_info,
            processing_time=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 文件上传处理失败 {request_id}: {str(e)}")
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