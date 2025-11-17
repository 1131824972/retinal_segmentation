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
    """上传图像文件"""
    save_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(save_path, "wb") as f:
        f.write(await file.read())

    metadata = {
        "filename": file.filename,
        "content_type": file.content_type
    }

    img = Image(user_id=user_id, image_path=save_path, image_metadata=metadata)
    image_id = img.save()

    return {"image_id": image_id, "message": "Image uploaded successfully"}


@router.get("/user/{user_id}")
def get_images_by_user(user_id: str):
    """根据用户ID查询该用户所有图像"""
    images = Image.find_by_user(user_id)

    if not images:
        raise HTTPException(status_code=404, detail="No images found for this user")

    return {"images": images}
