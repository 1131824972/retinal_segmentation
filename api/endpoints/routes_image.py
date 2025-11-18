# api/endpoints/routes_image.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi import status
from fastapi.responses import JSONResponse
from models.image import Image
from core.config import settings, ALLOWED_CONTENT_TYPES
from utils.image_utils import base64_to_image, validate_image_size, get_image_info, format_file_size
import os
import time
import uuid
import base64
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/images", tags=["Images"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...), user_id: str | None = None):
    """
    上传图像并把图像元数据写入 images 集合
    """
    request_id = f"file_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    logger.info(f"📤 文件上传请求 {request_id} - 文件名: {file.filename}")

    # 1. 验证文件类型
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    file_size = len(contents)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # 2. 保存到磁盘
    save_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    with open(save_path, "wb") as f:
        f.write(contents)

    # 3. 读取图像信息（使用你的工具）
    # 如果你已有 get_image_info，可以加载 PIL 等信息
    try:
        image = base64_to_image(base64.b64encode(contents).decode("utf-8"))
        is_valid, err = validate_image_size(image, (100,100), (settings.MAX_IMAGE_DIMENSION, settings.MAX_IMAGE_DIMENSION))
        if not is_valid:
            raise HTTPException(status_code=400, detail=err)
        image_info = get_image_info(image)
    except Exception:
        image_info = {}

    formatted_size = format_file_size(file_size)

    # 4. 插入 DB
    img = Image(user_id=user_id or "anonymous", image_path=save_path, image_metadata={
        "filename": file.filename,
        "content_type": file.content_type,
        "saved_name": save_name
    })
    image_id = await img.save()

    return JSONResponse(status_code=201, content={
        "status": "success",
        "request_id": request_id,
        "image_id": image_id,
        "filename": file.filename,
        "file_size": formatted_size,
        "image_info": image_info
    })


@router.get("", summary="List images")
async def list_images():
    # 简单列出（最多1000条）
    from core.database import images_collection
    cursor = images_collection.find().sort("uploaded_at", -1).limit(1000)
    docs = await cursor.to_list(length=1000)
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"count": len(docs), "data": docs}


@router.get("/{image_id}")
async def get_image(image_id: str):
    from core.database import images_collection
    from bson import ObjectId
    doc = await images_collection.find_one({"_id": ObjectId(image_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Image not found")
    doc["_id"] = str(doc["_id"])
    return doc
