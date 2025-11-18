# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import logging
import uvicorn
import time
import uuid
import asyncio

from core.config import settings
from core.database import init_db

# import routers
from api.endpoints import routes_user, routes_image, routes_prediction, routes_model
from api.endpoints import health, predict, upload

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("retina_api")

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# request id middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    old_factory = logging.getLogRecordFactory()
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record
    logging.setLogRecordFactory(record_factory)

    start = time.time()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(time.time() - start)
    return response

# register routers (all)
app.include_router(health.router)
app.include_router(upload.router, prefix=settings.API_V1_STR)
app.include_router(predict.router, prefix=settings.API_V1_STR)

# our CRUD routers
app.include_router(routes_user.router)
app.include_router(routes_image.router)
app.include_router(routes_prediction.router)
app.include_router(routes_model.router)

# startup/shutdown
@app.on_event("startup")
async def startup_event():
    logger.info("Starting service...")
    # init db indexes
    try:
        await init_db()
        logger.info("MongoDB indexes ready.")
    except Exception as e:
        logger.error(f"init_db failed: {e}")

    # load model (keep your existing model_service)
    try:
        from services.model_service import model_service
        await model_service.load_model(settings.MODEL_PATH)
        logger.info("Model loaded.")
    except Exception as e:
        logger.error(f"model load failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")

# exception handlers
@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.error(f"SERVER ERROR [{request_id}]: {exc}")
    return JSONResponse(status_code=500, content={
        "status": "error",
        "request_id": request_id,
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "服务器内部错误，请稍后重试"
    })

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")
