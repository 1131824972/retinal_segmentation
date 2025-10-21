from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ImageBase(BaseModel):
    """
    图像基础模型
    """
    filename: str
    original_name: str
    file_size: int
    content_type: str

class ImageCreate(ImageBase):
    """
    创建图像时的模型
    """
    pass

class ImageResponse(ImageBase):
    """
    图像响应模型
    """
    id: str
    upload_time: datetime
    result_path: Optional[str] = None
    processed_time: Optional[datetime] = None

    class Config:
        orm_mode = True
