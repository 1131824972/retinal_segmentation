from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import logging
import uvicorn
import time
import uuid
import redis.asyncio as aredis
from fastapi_limiter import FastAPILimiter

# 导入配置
from core.config import settings
from core.database import init_db

# 导入所有路由
from api.endpoints import health, predict, upload, routes_user

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("retina_api")

# 创建唯一的 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求ID 中间件
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    # Hack: 设置日志上下文 (简化版)
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record

    logging.setLogRecordFactory(record_factory)

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"处理完成: {request.method} {request.url.path} - {process_time:.3f}s")
    return response


# 注册路由
app.include_router(health.router)
app.include_router(routes_user.router, prefix="/api/v1")  # 用户认证
# 将上传和预测路由合并在 /api/v1 下
app.include_router(predict.router, prefix=settings.API_V1_STR)
app.include_router(upload.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """服务启动初始化"""
    logger.info("🚀 服务启动中...")

    # 1. 初始化数据库
    await init_db()
    logger.info("✅ MongoDB 索引初始化完成")

    # 2. 初始化 Redis 限流
    try:
        redis_conn = aredis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_conn)
        logger.info("✅ Redis 限流器连接成功")
    except Exception as e:
        logger.warning(f"⚠️ Redis 连接失败 (限流将不可用): {e}")

    # 3. 加载 AI 模型
    from services.model_service import model_service
    await model_service.load_model(settings.MODEL_PATH)
    logger.info("✅ 模型加载完成")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)