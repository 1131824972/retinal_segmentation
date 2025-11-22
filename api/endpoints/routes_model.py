# api/endpoints/routes_model.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.model import ModelInfo

router = APIRouter(prefix="/api/v1/models", tags=["Models"])

class ModelRegister(BaseModel):
    model_version: str
    model_metadata: dict = {}

@router.post("/register")
async def register_model(payload: ModelRegister):
    exists = await ModelInfo.find_by_version(payload.model_version)
    if exists:
        raise HTTPException(status_code=400, detail="Model version exists")
    m = ModelInfo(model_version=payload.model_version, model_metadata=payload.model_metadata)
    mid = await m.save()
    return {"status":"success","model_id": mid}

@router.get("")
async def list_models():
    docs = await ModelInfo.list_models()
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"count": len(docs), "data": docs}
