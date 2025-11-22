import cv2
import numpy as np
import base64
from typing import Tuple, Optional, Dict, Any
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)


def base64_to_image(base64_string: str) -> Optional[np.ndarray]:
    """
    将base64字符串转换为OpenCV图像
    (已升级：支持 GIF / TIFF)
    """
    try:
        # 移除可能的data URI前缀
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        # 解码base64
        image_data = base64.b64decode(base64_string)

        # 先尝试OpenCV解码
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # ⚠️ 如果OpenCV失败：尝试Pillow (处理 GIF / TIFF / 其他格式)
        if image is None:
            pil_image = Image.open(io.BytesIO(image_data))

            # 对于TIFF / GIF 等格式，统一转 RGB
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            logger.info(f"🟢 使用 Pillow 成功解码 TIFF/GIF 图像, 尺寸: {image.shape}")
        else:
            logger.info(f"🟢 图像解码成功，尺寸: {image.shape}")

        return image

    except Exception as e:
        logger.error(f"❌ Base64转换失败: {str(e)}")
        return None



def image_to_base64(image: np.ndarray, format: str = "png") -> str:
    """
    将OpenCV图像转换为base64字符串

    Args:
        image: OpenCV图像
        format: 输出格式

    Returns:
        base64编码的字符串
    """
    try:
        # 编码图像
        success, encoded_image = cv2.imencode(f'.{format}', image)
        if not success:
            logger.error("图像编码失败")
            return ""

        # 转换为base64
        base64_data = base64.b64encode(encoded_image.tobytes()).decode('utf-8')
        return f"data:image/{format};base64,{base64_data}"

    except Exception as e:
        logger.error(f"图像转Base64失败: {str(e)}")
        return ""


def resize_image(image: np.ndarray, target_size: Tuple[int, int] = (512, 512)) -> np.ndarray:
    """
    调整图像尺寸

    Args:
        image: 输入图像
        target_size: 目标尺寸 (宽, 高)

    Returns:
        调整后的图像
    """
    try:
        resized = cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)
        logger.debug(f"图像尺寸调整: {image.shape[:2]} -> {target_size}")
        return resized
    except Exception as e:
        logger.error(f"图像尺寸调整失败: {str(e)}")
        return image


def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    归一化图像像素值到 [0, 1] 范围

    Args:
        image: 输入图像

    Returns:
        归一化后的图像
    """
    return image.astype(np.float32) / 255.0


def validate_image_size(image: np.ndarray,
                        min_size: Tuple[int, int] = (100, 100),
                        max_size: Tuple[int, int] = (4096, 4096)) -> Tuple[bool, str]:
    """
    验证图像尺寸是否符合要求

    Args:
        image: 输入图像
        min_size: 最小允许尺寸
        max_size: 最大允许尺寸

    Returns:
        (是否通过验证, 错误信息)
    """
    height, width = image.shape[:2]

    if width < min_size[0] or height < min_size[1]:
        message = f"图像尺寸过小: {width}x{height}，最小要求: {min_size[0]}x{min_size[1]}"
        logger.warning(message)
        return False, message

    if width > max_size[0] or height > max_size[1]:
        message = f"图像尺寸过大: {width}x{height}，最大允许: {max_size[0]}x{max_size[1]}"
        logger.warning(message)
        return False, message

    return True, ""


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.2f} {size_names[i]}"


def get_image_info(image: np.ndarray) -> Dict[str, Any]:
    """
    获取图像详细信息

    Args:
        image: 输入图像

    Returns:
        图像信息字典
    """
    height, width = image.shape[:2]
    channels = image.shape[2] if len(image.shape) > 2 else 1

    return {
        "width": width,
        "height": height,
        "channels": channels,
        "dimensions": f"{width}x{height}",
        "size_pixels": width * height
    }


def create_mock_segmentation(image: np.ndarray) -> np.ndarray:
    """
    创建模拟的血管分割结果

    Args:
        image: 输入图像

    Returns:
        模拟的分割掩码
    """
    height, width = image.shape[:2]

    # 创建空白掩膜
    mask = np.zeros((height, width), dtype=np.uint8)

    # 模拟主要血管（从中心辐射的线条）
    center_x, center_y = width // 2, height // 2

    # 绘制主要血管
    cv2.line(mask, (center_x, center_y), (50, 50), 255, 3)
    cv2.line(mask, (center_x, center_y), (width - 50, 50), 255, 3)
    cv2.line(mask, (center_x, center_y), (50, height - 50), 255, 3)
    cv2.line(mask, (center_x, center_y), (width - 50, height - 50), 255, 3)

    # 添加血管分支（随机线条）
    for i in range(15):
        start_x = np.random.randint(0, width)
        start_y = np.random.randint(0, height)
        end_x = start_x + np.random.randint(-100, 100)
        end_y = start_y + np.random.randint(-100, 100)

        # 确保在图像范围内
        end_x = max(0, min(width - 1, end_x))
        end_y = max(0, min(height - 1, end_y))

        cv2.line(mask, (start_x, start_y), (end_x, end_y), 200, 1)

    # 添加毛细血管（随机点）
    for i in range(100):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        cv2.circle(mask, (x, y), 1, 150, -1)

    # 添加一些高斯噪声模拟真实分割的不确定性
    noise = np.random.normal(0, 25, (height, width)).astype(np.uint8)
    mask = cv2.add(mask, noise)

    # 二值化
    _, mask = cv2.threshold(mask, 128, 255, cv2.THRESH_BINARY)

    return mask