import logging
import time
import numpy as np
from typing import Dict, Any
import os
import sys
import torch
import cv2
from datetime import datetime

from core.config import settings
from utils.image_utils import image_to_base64

# === 关键设置 ===
# 1. 把 ai_core 加入系统路径，这样才能导入 Unet.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_core'))

# 2. 尝试导入模型架构 (防止编辑器报错)
try:
    # ⚠️ 这里的类名必须和你 ai_core/Unet.py 里的类名一致
    # 如果你的类名是 U_Net，请改为: from ai_core.Unet import U_Net as UNet
    from ai_core.Unet import UNet
except ImportError as e:
    print(f"❌ 导入模型架构失败: {e}")
    UNet = None

logger = logging.getLogger(__name__)


class ModelService:
    """
    模型服务类 - 正式版
    集成真实的 PyTorch U-Net 模型进行推理
    """

    def __init__(self):
        self.model = None
        self.model_loaded = False
        # 自动检测设备：有显卡用显卡，没显卡用CPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = "U-Net (PyTorch)"
        self.model_version = "1.0.0-release"
        self.load_time = None
        self.prediction_count = 0

        logger.info(f"🎯 模型服务初始化 (设备: {self.device})")

    async def load_model(self, model_path: str) -> bool:
        """
        加载真实模型权重
        """
        try:
            logger.info(f"🔧 开始加载模型")
            start_time = time.time()

            # 1. 修正路径：指向 ai_core 下的 bestmodel.pt
            real_model_path = os.path.join(os.path.dirname(__file__), '..', 'ai_core', 'bestmodel.pt')

            if not os.path.exists(real_model_path):
                logger.error(f"❌ 找不到模型文件: {real_model_path}")
                return False

            # 2. 加载完整模型
            # 使用 torch.load 直接加载整个模型对象
            self.model = torch.load(real_model_path, map_location=self.device)

            # 3. 转移到设备 (CPU 或 CUDA)
            self.model.to(self.device)
            self.model.eval()  # 开启评估模式

            self.model_loaded = True
            self.load_time = datetime.now()
            load_duration = time.time() - start_time

            logger.info(f"✅ 模型加载成功! 耗时: {load_duration:.2f}s")
            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.model_loaded = False
            return False

    async def predict(self, image: np.ndarray, request_id: str) -> Dict[str, Any]:
        """
        使用真实模型进行推理
        """
        if not self.model_loaded:
            return {"status": "error", "message": "模型未加载", "request_id": request_id}

        try:
            start_time = time.time()
            self.prediction_count += 1

            # === 1. 图像预处理 ===
            # 原始 image 是 (H, W, 3) 的 BGR 格式 (OpenCV读取)
            original_h, original_w = image.shape[:2]

            # 转为 RGB
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # 调整大小到模型输入尺寸 (例如 512x512)
            # ⚠️ 注意：如果模型训练时用的不是 512x512，这里需要改
            input_size = (512, 512)
            img_resized = cv2.resize(img_rgb, input_size)

            # 归一化 (0-255 -> 0.0-1.0)
            img_normalized = img_resized.astype(np.float32) / 255.0

            # 转换维度: (H, W, C) -> (C, H, W)
            img_transposed = img_normalized.transpose((2, 0, 1))

            # 转为 Tensor 并增加 Batch 维度: (1, C, H, W)
            img_tensor = torch.from_numpy(img_transposed).unsqueeze(0)
            img_tensor = img_tensor.to(self.device)

            # === 2. 模型推理 ===
            with torch.no_grad():  # 不计算梯度，节省内存
                output = self.model(img_tensor)

                # U-Net 输出通常是 Logits，需要经过 Sigmoid 变成概率 (0-1)
                probs = torch.sigmoid(output)

                # 移除 Batch 和 Channel 维度 -> (H, W)
                probs = probs.squeeze().cpu().numpy()

            # === 3. 后处理 ===
            # 阈值处理：大于 0.5 算血管，小于 0.5 算背景
            mask = (probs > 0.5).astype(np.uint8) * 255

            # 调整回原始尺寸
            if mask.shape != (original_h, original_w):
                mask = cv2.resize(mask, (original_w, original_h), interpolation=cv2.INTER_NEAREST)

            # 计算置信度和覆盖率 (简单的统计)
            confidence = float(probs.mean())
            vessel_coverage = float(np.count_nonzero(mask) / mask.size)

            # 转为 Base64
            result_base64 = image_to_base64(mask, "png")
            actual_time = time.time() - start_time

            logger.info(f"✅ 真实预测完成 [{request_id}]")

            return {
                "status": "success",
                "request_id": request_id,
                "result_image": result_base64,
                "processing_time": actual_time,
                "confidence": round(confidence, 4),
                "vessel_coverage": round(vessel_coverage, 4),
                "message": "预测成功 (真实模型)"
            }

        except Exception as e:
            logger.error(f"❌ 预测过程出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "request_id": request_id,
                "message": f"预测失败: {str(e)}"
            }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "version": self.model_version,
            "status": "loaded" if self.model_loaded else "error",
            "device": str(self.device),
            "input_size": "512x512"
        }

    def get_service_stats(self) -> Dict[str, Any]:
        return {
            "total_predictions": self.prediction_count,
            "uptime": str(datetime.now() - self.load_time) if self.load_time else "N/A"
        }


# 创建全局实例
model_service = ModelService()