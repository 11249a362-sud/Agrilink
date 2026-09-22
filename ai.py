from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException
)

from pathlib import Path
import shutil
import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.ai.predictor import predict_crop
from app.ai.demand_predictor import predict_demand
from app.ai.price_predictor import predict_price
from app.ai.buyer_recommender import recommend_buyers
from app.ai.dashboard import get_dashboard_stats
from app.ai.trends import get_trends
from app.ai.forecast import forecast_prices
from app.ai.allocation_engine import allocate_stock

from app.schemas.dashboard_schema import DashboardResponse


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# CROP IDENTIFICATION
# ============================================================

@router.post("/predict-crop")
def predict_crop_image(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # 1. Validate filename
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Image filename is missing"
        )


    # --------------------------------------------------------
    # 2. Get file extension
    # --------------------------------------------------------

    extension = Path(file.filename).suffix

    if not extension:
        raise HTTPException(
            status_code=400,
            detail="Image file extension is missing"
        )


    # --------------------------------------------------------
    # 3. Generate unique filename
    # --------------------------------------------------------

    filename = f"{uuid.uuid4()}{extension}"

    file_path = UPLOAD_DIR / filename


    # --------------------------------------------------------
    # 4. Save uploaded image
    # --------------------------------------------------------

    try:

        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save image: {str(e)}"
        )


    # --------------------------------------------------------
    # 5. Check image exists
    # --------------------------------------------------------

    if not file_path.exists():

        raise HTTPException(
            status_code=500,
            detail="Uploaded image was not saved"
        )


    # --------------------------------------------------------
    # 6. Check image is not empty
    # --------------------------------------------------------

    if file_path.stat().st_size == 0:

        raise HTTPException(
            status_code=500,
            detail="Uploaded image is empty"
        )


    # --------------------------------------------------------
    # 7. Run YOLO prediction
    # --------------------------------------------------------

    try:

        result = predict_crop(
            str(file_path)
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Crop prediction failed: {str(e)}"
        )


# ============================================================
# PRICE PREDICTION
# ============================================================

class PriceRequest(BaseModel):

    crop: str
    location: str
    quantity: float
    month: int


@router.post("/predict-price")
def predict_crop_price(
    request: PriceRequest
):

    return predict_price(
        crop=request.crop,
        location=request.location,
        quantity=request.quantity,
        month=request.month
    )


# ============================================================
# DEMAND PREDICTION
# ============================================================

class DemandRequest(BaseModel):

    crop: str
    location: str
    month: int


@router.post("/predict-demand")
def predict_crop_demand(
    request: DemandRequest
):

    return predict_demand(
        crop=request.crop,
        location=request.location,
        month=request.month
    )


# ============================================================
# BUYER RECOMMENDATION
# ============================================================

class BuyerRecommendationRequest(BaseModel):

    crop: str
    location: str
    quantity: float
    month: int


@router.post("/recommend-buyers")
def recommend_best_buyers(
    request: BuyerRecommendationRequest,
    db: Session = Depends(get_db)
):

    return recommend_buyers(
        db=db,
        crop=request.crop,
        location=request.location,
        quantity=request.quantity,
        month=request.month
    )


# ============================================================
# AI DASHBOARD
# ============================================================

@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db)
):

    return get_dashboard_stats(db)


# ============================================================
# AI DASHBOARD TRENDS
# ============================================================

@router.get("/dashboard/trends")
def dashboard_trends(
    db: Session = Depends(get_db)
):

    return get_trends(db)


# ============================================================
# PRICE FORECAST
# ============================================================

class ForecastRequest(BaseModel):

    crop: str
    location: str
    quantity: float
    month: int


@router.post("/forecast-price")
def forecast_crop_price(
    request: ForecastRequest
):

    return forecast_prices(
        crop=request.crop,
        location=request.location,
        quantity=request.quantity,
        month=request.month
    )


# ============================================================
# STOCK ALLOCATION
# ============================================================

@router.post("/allocate-stock")
def ai_allocate_stock(
    crop: str,
    quantity: float,
    location: str,
    db: Session = Depends(get_db)
):

    return allocate_stock(
        db=db,
        crop=crop,
        quantity=quantity,
        location=location
    )