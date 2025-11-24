from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import logging
import uvicorn
import time
import uuid
import contextvars  # <--- 新增导入

# 导入配置
from core.config import settings
from core.database import init_db
from contextlib import asynccontextmanager
# 导入所有路由
from api.endpoints import health, predict, upload, routes_patient

# === 1. 定义上下文变量 (ContextVar) ===
# 这是一种在异步编程中安全存储"全局"变量的方式
# default="system" 意味着如果在请求之外打印日志，ID显示为 "system"
request_id_context = contextvars.ContextVar("request_id", default="system")


# === 2. 自定义日志过滤器 ===
class RequestIDFilter(logging.Filter):
    """
    这个过滤器会自动把当前的 request_id 注入到每一条日志记录中。
    如果当前没有请求，它会使用默认值 "system"。
    """

    def filter(self, record):
        record.request_id = request_id_context.get()
        return True


# === 3. 配置日志 ===
# 先配置基本格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 获取 logger
logger = logging.getLogger("retina_api")

# 关键步骤：给所有现有的 handler 添加我们定义的过滤器
# 这样就能保证每一条日志都有 request_id 字段，不会报错了
for handler in logging.root.handlers:
    handler.addFilter(RequestIDFilter())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # === 启动逻辑 (Startup) ===
    logger.info("🚀 服务启动中...")

    # 初始化数据库
    await init_db()
    logger.info("✅ MongoDB 索引初始化完成")

    # 加载 AI 模型
    from services.model_service import model_service
    await model_service.load_model(settings.MODEL_PATH)
    logger.info("✅ 模型加载完成")

    yield  # 服务运行期间停留在这里

    # === 关闭逻辑 (Shutdown) ===
    logger.info("🛑 服务正在关闭...")
    logger.info("👋 感谢使用视网膜血管分割API服务")


# 创建唯一的 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === 4. 请求ID 中间件 (修改版) ===
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    # 生成新的 UUID
    request_id = str(uuid.uuid4())

    # 将 ID 设置到上下文中，这样后续的所有日志都能拿到了
    token = request_id_context.set(request_id)

    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        logger.info(f"处理完成: {request.method} {request.url.path} - {process_time:.3f}s")
        return response
    finally:
        # 请求结束后，重置上下文，防止内存泄漏或数据混淆
        request_id_context.reset(token)


# 注册路由
app.include_router(health.router)
app.include_router(routes_patient.router, prefix="/api/v1")  # 用户认证
app.include_router(predict.router, prefix=settings.API_V1_STR)
app.include_router(upload.router, prefix=settings.API_V1_STR)



@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)