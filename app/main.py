from fastapi import FastAPI
from app.api.routes import router
from app.config import settings

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="视网膜图像分割API服务"
)

# 注册路由
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """
    根路径，返回API信息
    """
    return {
        "message": "欢迎使用视网膜图像分割API",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {"status": "healthy"}
