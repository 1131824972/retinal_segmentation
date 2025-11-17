from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import logging
import psutil
import os

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    service: str
    version: str
    timestamp: str
    environment: str
    uptime: str


class ServiceInfoResponse(BaseModel):
    """服务信息响应模型"""
    service_name: str
    version: str
    environment: str
    debug_mode: bool
    api_prefix: str
    model_status: str


class SystemStatsResponse(BaseModel):
    """系统统计响应模型"""
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    active_connections: int
    boot_time: str


# 服务启动时间
startup_time = datetime.now()


def get_system_stats() -> dict:
    """获取系统统计信息"""
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "active_connections": len(psutil.net_connections()),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
    except Exception as e:
        logger.error(f"获取系统统计失败: {str(e)}")
        return {}


@router.get("/", response_model=HealthResponse)
async def root():
    """根路径 - 服务状态检查"""
    from core.config import settings

    uptime = datetime.now() - startup_time
    uptime_str = str(uptime).split('.')[0]  # 移除微秒部分

    logger.info("🌐 根路径访问")

    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now().isoformat(),
        environment=settings.ENVIRONMENT,
        uptime=uptime_str
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    from core.config import settings
    from services.model_service import model_service

    uptime = datetime.now() - startup_time
    uptime_str = str(uptime).split('.')[0]

    logger.info("❤️ 健康检查请求")

    return HealthResponse(
        status="healthy",
        service="retina-segmentation-api",
        version=settings.APP_VERSION,
        timestamp=datetime.now().isoformat(),
        environment=settings.ENVIRONMENT,
        uptime=uptime_str
    )


@router.get("/info", response_model=ServiceInfoResponse)
async def service_info():
    """服务信息端点"""
    from core.config import settings
    from services.model_service import model_service

    return ServiceInfoResponse(
        service_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        debug_mode=settings.DEBUG,
        api_prefix=settings.API_V1_STR,
        model_status="loaded" if model_service.model_loaded else "not_loaded"
    )


@router.get("/system/stats", response_model=SystemStatsResponse)
async def system_stats():
    """系统统计信息端点"""
    stats = get_system_stats()

    return SystemStatsResponse(**stats)