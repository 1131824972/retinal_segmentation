from fastapi import APIRouter, HTTPException
from models.prediction import Prediction

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("/add")
def add_prediction(
    image_id: str,
    model_version: str,
    prediction_data: dict
):
    """保存某张图像的预测结果"""
    prediction = Prediction(
        image_id=image_id,
        model_version=model_version,
        prediction_data=prediction_data
    )
    pred_id = prediction.save()

    return {"prediction_id": pred_id, "message": "Prediction stored successfully"}


@router.get("/image/{image_id}")
def get_prediction_by_image(image_id: str):
    """查询该图像的全部预测记录"""
    preds = Prediction.find_by_image(image_id)

    if not preds:
        raise HTTPException(status_code=404, detail="No prediction found for this image")

    return {"predictions": preds}
