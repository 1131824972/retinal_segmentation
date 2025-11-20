from fastapi import APIRouter, HTTPException
from models.prediction import Prediction

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("/add")
async def add_prediction(
        request_id: str,  # 注意：这里对应新的 Prediction 模型字段
        model_version: str,
        prediction_data: dict,
        user_id: str = None
):
    """保存预测结果 (异步修复版)"""
    prediction = Prediction(
        request_id=request_id,
        model_version=model_version,
        result_data=prediction_data,
        user_id=user_id
    )

    pred_id = await prediction.save()

    return {"prediction_id": pred_id, "message": "Prediction stored successfully"}


@router.get("/image/{image_id}")
async def get_prediction_by_image(image_id: str):
    """查询该图像的全部预测记录 (异步修复版)"""
    preds = await Prediction.find_by_image(image_id)

    if not preds:
        raise HTTPException(status_code=404, detail="No prediction found for this image")

    # 序列化处理
    for p in preds:
        p["_id"] = str(p["_id"])

    return {"predictions": preds}