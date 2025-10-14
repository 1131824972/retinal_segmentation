from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
import os
from app.models.image import ImageResponse
from app.services.storage import StorageService
from app.services.segmentation import SegmentationService
from app.utils.preprocessing import preprocess_image
from app.config import settings
import cv2
import numpy as np

router = APIRouter()

@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)):
    """
    上传视网膜图像

    Args:
        file: 上传的图像文件

    Returns:
        ImageResponse: 图像信息响应
    """
    # 验证文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持图像文件上传"
        )

    # 读取文件内容
    file_content = await file.read()

    # 验证文件大小
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小超过限制"
        )

    # 保存文件
    file_id, file_path = StorageService.save_uploaded_file(file_content, file.filename)

    # 构建响应
    response = ImageResponse(
        id=file_id,
        filename=os.path.basename(file_path),
        original_name=file.filename,
        file_size=len(file_content),
        content_type=file.content_type,
        upload_time=cv2.getTickCount()  # 简化时间处理
    )

    return response

@router.post("/segment/{image_id}", response_model=ImageResponse)
async def segment_image(image_id: str):
    """
    对指定图像进行分割处理

    Args:
        image_id: 图像ID

    Returns:
        ImageResponse: 处理结果信息
    """
    # 构建文件路径
    file_path = os.path.join(settings.UPLOAD_FOLDER, f"{image_id}.jpg")
    if not os.path.exists(file_path):
        file_path = os.path.join(settings.UPLOAD_FOLDER, f"{image_id}.png")
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="图像文件未找到"
            )

    # 读取并预处理图像
    image = cv2.imread(file_path)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法读取图像文件"
        )

    # 执行分割
    segmented = SegmentationService.segment_retinal_image(image)

    # 保存结果
    _, buffer = cv2.imencode('.png', segmented)
    result_path = StorageService.save_result_image(image_id, buffer.tobytes())

    # 构建响应（简化处理）
    response = ImageResponse(
        id=image_id,
        filename=f"{image_id}.jpg",
        original_name="original.jpg",
        file_size=1000,  # 示例值
        content_type="image/jpeg",
        upload_time=cv2.getTickCount(),
        result_path=result_path
    )

    return response

@router.get("/result/{image_id}")
async def get_segmentation_result(image_id: str):
    """
    获取分割结果图像

    Args:
        image_id: 图像ID

    Returns:
        FileResponse: 分割结果图像文件
    """
    result_path = os.path.join(settings.RESULT_FOLDER, f"{image_id}_segmented.png")

    if not os.path.exists(result_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分割结果未找到"
        )

    return FileResponse(result_path, media_type="image/png")
@router.get("/hybridaction/{action}")
async def handle_hybrid_action(action: str):
    """
    处理混合动作请求（用于兼容前端统计脚本）
    """
    return {"status": "success", "message": "Action processed"}
