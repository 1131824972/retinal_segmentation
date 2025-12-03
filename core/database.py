from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

# ===== MongoDB 配置 =====
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "retinal_segmentation")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ===== 集合定义 =====
# 病人集合
patients_collection = db["patients"]

images_collection = db["images"]
predictions_collection = db["predictions"]
models_collection = db["models"]


async def init_db():
    """初始化数据库索引 (异步版本)"""
    # 初始化病人集合索引 (邮箱唯一，用户名唯一)
    await patients_collection.create_index("email", unique=True)
    await patients_collection.create_index("username", unique=True)

    await images_collection.create_index("user_id")
    await predictions_collection.create_index("image_id")
    await models_collection.create_index("model_version", unique=True)