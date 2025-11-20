from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models.image import Image
import os

router = APIRouter(prefix="/images", tags=["Images"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_image(
        user_id: str = Form(...),
        file: UploadFile = File(...)
):
    """上传图像文件 (异步修复版)"""
    save_path = os.path.join(UPLOAD_DIR, file.filename)

    # 这里的 file.read() 是异步操作，建议加 await，虽然 FastAPI 有时兼容同步写法，但异步更好
    content = await file.read()

    # 写入文件是阻塞操作，生产环境建议用 aiofiles，这里演示用普通写入即可
    with open(save_path, "wb") as f:
        f.write(content)

    metadata = {
        "filename": file.filename,
        "content_type": file.content_type
    }

    # 创建 Image 实例
    img = Image(
        user_id=user_id,
        filename=file.filename,
        file_size=len(content),
        content_type=file.content_type
    )

    # 关键修复：添加 await
    image_id = await img.save()

    return {"image_id": image_id, "message": "Image uploaded successfully"}


@router.get("/user/{user_id}")
async def get_images_by_user(user_id: str):
    """根据用户ID查询该用户所有图像 (异步修复版)"""
    # 关键修复：添加 await
    images = await Image.find_by_user(user_id)

    if not images:
        raise HTTPException(status_code=404, detail="No images found for this user")

    # 将 ObjectId 转换为字符串，以便 JSON 序列化
    for img in images:
        img["_id"] = str(img["_id"])

    return {"images": images}