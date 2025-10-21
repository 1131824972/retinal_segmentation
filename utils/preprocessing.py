import cv2
import numpy as np
from PIL import Image
import io

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    预处理上传的图像

    Args:
        image_bytes: 图像的字节数据

    Returns:
        np.ndarray: 预处理后的图像数组
    """
    # 将字节数据转换为OpenCV图像
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 转换为RGB格式
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img

def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    标准化图像数据

    Args:
        image: 输入图像数组

    Returns:
        np.ndarray: 标准化后的图像
    """
    # 转换为浮点数并归一化到[0,1]范围
    normalized = image.astype(np.float32) / 255.0
    return normalized
