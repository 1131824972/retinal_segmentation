from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64

# 创建FastAPI应用实例
app = FastAPI(title="视网膜血管分割后端服务", version="0.1.0")

# 配置CORS（重要！让前端能访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 后期改成前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查接口 - 用来证明服务是活的
@app.get("/")
async def health_check():
    return {
        "status": "服务运行正常",
        "message": "视网膜血管分割后端API已启动",
        "version": "0.1.0"
    }

# 模型信息接口 - 展示项目规划
@app.get("/model/info")
async def get_model_info():
    return {
        "model_name": "U-Net视网膜血管分割模型",
        "status": "开发中",
        "input_format": "眼底图像 (PNG/JPG)",
        "output_format": "二值分割掩膜",
        "planned_features": ["图像上传", "血管分割", "结果可视化"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)