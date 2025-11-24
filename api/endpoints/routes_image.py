# api/endpoints/routes_image.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import logging
from models.image import Image

router = APIRouter(prefix="/images", tags=["Images"])
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_image(
        user_id: str = Form(...),
        file: UploadFile = File(...)
):
    """上传图像文件 (异步修复版)"""
    save_path = os.path.join(UPLOAD_DIR, file.filename)

    # 读取文件（异步）
    content = await file.read()

    # 写入文件（同步写法，保持你原逻辑）
    with open(save_path, "wb") as f:
        f.write(content)

    # 创建 Image 实例（兼容 user_id 和新增 patient_id 可一并传入）
    img = Image(
        user_id=user_id,
        patient_id=None,
        filename=file.filename,
        file_size=len(content),
        content_type=file.content_type,
        filepath=save_path
    )

    image_id = await img.save()

    return {"image_id": image_id, "message": "Image uploaded successfully"}


@router.get("/patient/{patient_id}")
async def get_images_by_user(patient_id: str):
    """根据用户ID查询该用户所有图像 (异步修复版)"""
    images = await Image.find_by_user(patient_id)

    if not images:
        raise HTTPException(status_code=404, detail="No images found for this patient")

    # 将 ObjectId 转换为字符串，方便序列化（前端显示）
    for img in images:
        img["_id"] = str(img["_id"])

    return {"images": images}
