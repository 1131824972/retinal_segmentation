import os
from typing import Optional


class Settings:
    """
    应用配置类
    """
    # 项目基础配置
    PROJECT_NAME: str = "Retinal Segmentation API"
    PROJECT_VERSION: str = "1.0.0"

    # 文件存储路径
    UPLOAD_FOLDER: str = os.path.join(os.getcwd(), "uploads")
    RESULT_FOLDER: str = os.path.join(os.getcwd(), "results")

    # 确保目录存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULT_FOLDER, exist_ok=True)

    # 图像处理配置
    IMAGE_SIZE: tuple = (512, 512)  # 统一图像尺寸
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 最大文件大小 10MB


settings = Settings()
