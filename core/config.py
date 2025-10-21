import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置中心 - 统一管理所有设置"""

    # 应用基础配置
    APP_NAME: str = "视网膜血管分割API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_DESCRIPTION: str = "基于U-Net的视网膜血管分割后端服务 - 第二次汇报版本"

    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]

    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/jpg", "image/png", "image/tiff"]
    MAX_IMAGE_DIMENSION: int = 4096  # 最大图像尺寸

    # 模型配置
    MODEL_PATH: str = "models/retina_unet.pth"
    MODEL_INPUT_SIZE: tuple = (512, 512)

    # 性能配置
    MAX_REQUESTS_PER_MINUTE: int = 60
    REQUEST_TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外字段


# 创建全局配置实例
settings = Settings()

# 文件类型映射
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/tiff": "tiff"
}

# 支持的图像格式
SUPPORTED_FORMATS = ["png", "jpg", "jpeg", "tiff"]