import logging
import time
import numpy as np
from typing import Dict, Any
import os
import sys
import torch
import cv2
from datetime import datetime

from utils.image_utils import image_to_base64

# ========= 关键：确保可以 import 模型类 =========
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_core'))

try:
    from ai_core.Unet import UNet
except Exception:
    UNet = None


logger = logging.getLogger(__name__)


class ModelService:

    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_loaded = False
        self.load_time = None
        self.prediction_count = 0

        logger.info(f"🎯 ModelService Initialized, device={self.device}")

    async def load_model(self, model_path: str):

        try:
            logger.info(f"🔧 开始加载模型...")

            real_model_path = os.path.join(os.path.dirname(__file__), '..', 'ai_core', 'bestmodel.pt')

            if not os.path.exists(real_model_path):
                logger.error("❌ 模型文件不存在")
                return False

            self.model = torch.load(real_model_path, map_location=self.device)
            self.model.to(self.device)
            self.model.eval()

            self.model_loaded = True
            self.load_time = datetime.now()

            logger.info("✅ 模型加载成功")
            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            return False


    async def predict(self, image: np.ndarray, request_id: str) -> Dict[str, Any]:

        if not self.model_loaded:
            return {"status": "error", "message": "模型未加载"}

        try:
            start_time = time.time()
            self.prediction_count += 1

            h, w = image.shape[:2]

            # ====================
            # PREPROCESS (RGB)
            # ====================

            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            img_resized = cv2.resize(img_rgb, (512, 512))

            img_norm = img_resized.astype(np.float32) / 255.0

            img_chw = img_norm.transpose((2, 0, 1))  # (3, 512, 512)

            img_tensor = torch.from_numpy(img_chw).unsqueeze(0).to(self.device)


            # ====================
            # INFER
            # ====================
            with torch.no_grad():
                y = self.model(img_tensor)
                y = torch.sigmoid(y).squeeze().cpu().numpy()

            mask = (y > 0.5).astype(np.uint8) * 255

            if mask.shape != (h, w):
                mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)

            # ====================
            # SAVE
            # ====================

            outputs_dir = os.path.join(os.getcwd(), "outputs")
            os.makedirs(outputs_dir, exist_ok=True)

            mask_file = f"{request_id}_mask.png"
            overlay_file = f"{request_id}_overlay.png"

            # 保存mask
            cv2.imwrite(os.path.join(outputs_dir, mask_file), mask)

            # overlay
            green_map = np.zeros_like(image)
            green_map[:, :, 1] = mask

            overlay = cv2.addWeighted(image, 0.7, green_map, 0.3, 0)
            cv2.imwrite(os.path.join(outputs_dir, overlay_file), overlay)

            # swagger return
            result_base64 = image_to_base64(mask, "png")

            return {
                "status": "success",
                "request_id": request_id,
                "mask_file": mask_file,
                "overlay_file": overlay_file,
                "result_image": result_base64,
                "processing_time": time.time() - start_time,
                "message": "预测成功（RGB 3-channel）"
            }

        except Exception as e:
            logger.error(f"❌ 推理失败: {e}")
            return {
                "status": "error",
                "request_id": request_id,
                "message": str(e)
            }


model_service = ModelService()
