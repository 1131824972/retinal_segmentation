from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
import time
import uuid

import redis.asyncio as aredis
from fastapi_limiter import FastAPILimiter

from core.database import init_db
from api.endpoints import routes_user, routes_image, routes_prediction

app = FastAPI(title="Retinal Segmentation Backend (FastAPI + MongoDB)")

init_db()  # 初始化 MongoDB 索引等

app.include_router(routes_user.router)
app.include_router(routes_image.router)
app.include_router(routes_prediction.router)

# 导入配置
from core.config import settings
# 导入路由
from api.endpoints import health, predict, upload

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("retina_api")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "后端开发组",
        "email": "team@retina-project.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# 请求ID中间件
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """为每个请求添加唯一ID用于追踪"""
    request_id = str(uuid.uuid4())

    # 将request_id添加到日志记录器
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record

    logging.setLogRecordFactory(record_factory)

    # 处理请求
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # 添加自定义头
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    logger.info(f"请求处理完成 - 方法: {request.method}, 路径: {request.url.path}, 耗时: {process_time:.3f}s")

    return response


# 注册路由
app.include_router(health.router)
app.include_router(predict.router, prefix=settings.API_V1_STR)
app.include_router(upload.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """服务启动事件"""
    logger.info("🚀 视网膜血管分割API服务启动中...")
    logger.info(f"📋 项目: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"🌍 环境: {settings.ENVIRONMENT}")
    logger.info(f"🔧 调试模式: {settings.DEBUG}")
    try:
        # 假设 Redis 运行在本地默认端口
        redis_conn = aredis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_conn)
        logger.info("✅ 成功连接到 Redis 并初始化 API 限流器")
    except Exception as e:
        logger.error(f"❌ 连接 Redis 或初始化限流器失败: {e}")
        # 在开发中可以先不退出，但在生产中可能需要
        # raise e

    # 模拟模型加载
    from services.model_service import model_service
    await model_service.load_model(settings.MODEL_PATH)

    logger.info("✅ 服务启动完成！")
    logger.info(f"📚 API文档地址: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"🌐 服务访问地址: http://{settings.HOST}:{settings.PORT}")
    logger.info("🎯 准备接收请求...")


@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭事件"""
    logger.info("🛑 服务正在关闭...")
    logger.info("👋 感谢使用视网膜血管分割API服务")


# 全局异常处理
@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """500错误处理"""
    request_id = request.headers.get("X-Request-ID", "unknown")

    logger.error(f"服务器内部错误 [{request_id}]: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "request_id": request_id,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误，请稍后重试",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    """404错误处理"""
    request_id = request.headers.get("X-Request-ID", "unknown")

    logger.warning(f"接口未找到 [{request_id}]: {request.url.path}")

    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "request_id": request_id,
            "error_code": "ENDPOINT_NOT_FOUND",
            "message": f"请求的接口不存在: {request.url.path}",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
    )


@app.exception_handler(422)
async def validation_error_handler(request: Request, exc: Exception):
    """422验证错误处理"""
    request_id = request.headers.get("X-Request-ID", "unknown")

    logger.warning(f"请求参数验证失败 [{request_id}]: {str(exc)}")

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "request_id": request_id,
            "error_code": "VALIDATION_ERROR",
            "message": "请求参数格式错误",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
    )


# 根路径重定向到文档
@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """重定向到API文档"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

@app.get("/")
def root():
    return {"message": "Retinal Segmentation API Running"}


if __name__ == "__main__":
    """主程序入口"""
    logger.info(f"🎯 启动服务器: {settings.HOST}:{settings.PORT}")

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level="info",
        access_log=True,
        workers=1
    )
