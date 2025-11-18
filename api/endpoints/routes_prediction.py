# api/endpoints/routes_prediction.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.prediction import Prediction
from core.database import predictions_collection
from services.model_service import model_service
import time
import uuid
from typing import Optional, Dict, Any
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])


class PredictRunRequest(BaseModel):
    image_id: str
    model_version: str | None = None
    extra: Optional[Dict[str, Any]] = None


@router.post("/run")
async def run_prediction(payload: PredictRunRequest):
    """
    根据已上传的 image_id 运行模型预测（如果你也允许直接上传并预测，请使用 upload 接口）
    """
    request_id = f"pred_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    # 调用 model_service（保持你现有逻辑）
    # model_service.predict 应该接收 image_id 或 image object; 这里假定可接收 image path 或 image object
    result = await model_service.predict(image_id=payload.image_id, request_id=request_id)

    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail="Prediction failed")

    # 写入 predictions 集合
    pred = Prediction(image_id=payload.image_id, model_version=payload.model_version or "default", prediction_data=result)
    pred_id = await pred.save()

    return JSONResponse(status_code=201, content={
        "status": "success",
        "request_id": request_id,
        "prediction_id": pred_id,
        "result": result
    })


@router.get("", summary="list predictions")
async def list_predictions():
    from core.database import predictions_collection
    cursor = predictions_collection.find().sort("predicted_at", -1).limit(1000)
    docs = await cursor.to_list(length=1000)
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"count": len(docs), "data": docs}


@router.get("/{pid}")
async def get_prediction(pid: str):
    from core.database import predictions_collection
    from bson import ObjectId
    doc = await predictions_collection.find_one({"_id": ObjectId(pid)})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    doc["_id"] = str(doc["_id"])
    return doc
