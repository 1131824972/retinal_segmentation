import os
import uuid
from typing import Tuple
from app.config import settings

class StorageService:
    """
    文件存储服务
    """

    @staticmethod
    def save_uploaded_file(file_content: bytes, original_filename: str) -> Tuple[str, str]:
        """
        保存上传的文件

        Args:
            file_content: 文件内容
            original_filename: 原始文件名

        Returns:
            Tuple[str, str]: (文件ID, 文件保存路径)
        """
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(original_filename)[1]
        new_filename = f"{file_id}{file_extension}"

        # 构建文件保存路径
        file_path = os.path.join(settings.UPLOAD_FOLDER, new_filename)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        return file_id, file_path

    @staticmethod
    def save_result_image(file_id: str, result_image: bytes) -> str:
        """
        保存分割结果图像

        Args:
            file_id: 关联的文件ID
            result_image: 分割结果图像数据

        Returns:
            str: 结果文件保存路径
        """
        result_filename = f"{file_id}_segmented.png"
        result_path = os.path.join(settings.RESULT_FOLDER, result_filename)

        with open(result_path, "wb") as f:
            f.write(result_image)

        return result_path
