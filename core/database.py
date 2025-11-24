# core/database.py
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "retinal_segmentation")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
patients_collection = db["patients"]
images_collection = db["images"]
predictions_collection = db["predictions"]
models_collection = db["models"]

async def init_db():
    """初始化数据库索引 (异步版本)"""
    # create_index is async in motor
    await patients_collection.create_index("email", unique=True)
    await images_collection.create_index("patient_id")
    await predictions_collection.create_index("image_id")
    await models_collection.create_index("model_version", unique=True)
