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
# 1. 把 ai_core 加入系统路径
AI_CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'ai_core')
sys.path.append(AI_CORE_PATH)

logger = logging.getLogger(__name__)


class ModelService:
    """
    模型服务类 - 正式版
    集成真实的 PyTorch U-Net 模型进行推理
    """

    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = "U-Net (PyTorch)"
        self.model_version = "1.0.0-release"
        self.load_time = None
        self.prediction_count = 0

        logger.info(f"🎯 模型服务初始化 (设备: {self.device})")

    async def load_model(self, model_path: str) -> bool:
        """加载真实模型权重"""
        try:
            logger.info(f"🔧 开始加载模型...")
            start_time = time.time()

            real_model_path = os.path.join(AI_CORE_PATH, 'bestmodel.pt')

            if not os.path.exists(real_model_path):
                logger.error(f"❌ 找不到模型文件: {real_model_path}")
                return False

            # 2. 加载完整模型
            # weights_only=False 解决 FutureWarning
            self.model = torch.load(real_model_path, map_location=self.device, weights_only=False)

            self.model.to(self.device)
            self.model.eval()

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
        """使用真实模型进行推理 (Debug 版)"""
        if not self.model_loaded:
            return {"status": "error", "message": "模型未加载", "request_id": request_id}

        try:
            start_time = time.time()
            self.prediction_count += 1

            # === 1. 图像预处理 ===
            original_h, original_w = image.shape[:2]
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img_rgb, (512, 512))

            # 归一化 (匹配 dataset.py)
            img_float = img_resized.astype(np.float32)
            min_val = np.min(img_float)
            max_val = np.max(img_float)
            if max_val - min_val > 1e-5:
                img_normalized = (img_float - min_val) / (max_val - min_val)
            else:
                img_normalized = img_float / 255.0

            img_transposed = img_normalized.transpose((2, 0, 1))
            img_tensor = torch.from_numpy(img_transposed).unsqueeze(0).to(self.device)

            # === 2. 模型推理 ===
            with torch.no_grad():
                output = self.model(img_tensor)

                # 🛑【关键 Debug】打印模型输出形状
                logger.info(f"🔍 [Debug] 模型原始输出 Shape: {output.shape}")

                # 处理输出
                # 如果是多分类 (Batch, 2, H, W)，通常 Channel 1 是血管
                if output.shape[1] == 2:
                    logger.info("🔍 [Debug] 检测到双通道输出，取第2个通道 (Index 1) 作为血管")
                    # 取出血管通道，并保留维度以便后续处理
                    output_vessel = output[:, 1, :, :].unsqueeze(1)
                else:
                    # 单通道直接用
                    output_vessel = output

                # ⚠️ 尝试移除 Sigmoid，直接看原始值分布
                # 很多 U-Net 最后一层已经是 Sigmoid 了，或者输出就是概率
                probs = output_vessel.squeeze().cpu().numpy()

                # 🛑【关键 Debug】打印数值范围，判断是否需要 Sigmoid
                logger.info(f"🔍 [Debug] 输出数值范围: Min={probs.min():.4f}, Max={probs.max():.4f}")

                # 动态决策：如果数值在 [0, 1] 之外（比如 -10, +10），说明需要 Sigmoid
                if probs.min() < 0 or probs.max() > 1.5:
                    logger.info("🔍 [Debug] 数值超出 [0,1]，应用 Sigmoid 激活")
                    probs = 1 / (1 + np.exp(-probs))  # NumPy 版 Sigmoid

            # === 3. 后处理 ===
            # 阈值化
            mask = (probs > 0.5).astype(np.uint8) * 255

            if mask.shape != (original_h, original_w):
                mask = cv2.resize(mask, (original_w, original_h), interpolation=cv2.INTER_NEAREST)

            confidence = float(probs.mean())
            vessel_coverage = float(np.count_nonzero(mask) / mask.size)

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
                "message": "预测成功"
            }

        except Exception as e:
            logger.error(f"❌ 预测异常: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "request_id": request_id, "message": str(e)}

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