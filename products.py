from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
)

from sqlalchemy.orm import Session

from app.services.location_service import get_location_from_coordinates
from app.models.rotten_crop import RottenCropRequest
from app.database.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product_schema import ProductResponse, ProductUpdate
from app.utils.dependencies import require_farmer
from app.ai.price_predictor import predict_price


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# ============================================================
# UPLOAD FOLDER
# ============================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# TRAINING / AI MODEL CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

TRAINING_DIR = BASE_DIR / "training"

PYTHON_EXE = TRAINING_DIR / "venv311" / "Scripts" / "python.exe"
PREDICT_SCRIPT = TRAINING_DIR / "predict.py"


# ============================================================
# CREATE PRODUCT
# Farmer only
#
# Features:
# - GPS → Location
# - Image upload
# - AI image grading
# - AI price prediction
# - AI demand prediction
# - Automatic RottenCropRequest creation
# ============================================================

@router.post("/", response_model=ProductResponse)
async def create_product(
    name: str = Form(...),
    description: str = Form(""),
    quantity: float = Form(...),
    unit: str = Form(...),

    # Location
    location: str | None = Form(None),

    # Pickup coordinates
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),

    # Product image
    image: UploadFile = File(...),

    # Database
    db: Session = Depends(get_db),

    # Logged-in farmer
    current_user: User = Depends(require_farmer),
):
    # ========================================================
    # 1. DETERMINE LOCATION FROM GPS
    # ========================================================

    if latitude is not None and longitude is not None:
        try:
            detected_location = get_location_from_coordinates(
                latitude,
                longitude
            )

            if detected_location:
                location = detected_location

        except Exception:
            # If reverse geocoding fails, continue with
            # the location supplied by the user.
            pass

    if not location:
        location = "Unknown"


    # ========================================================
    # 2. SAVE UPLOADED IMAGE
    # ========================================================

    if not image.filename:
        raise HTTPException(
            status_code=400,
            detail="Image filename is missing"
        )

    file_path = UPLOAD_DIR / image.filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                image.file,
                buffer
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save image: {str(e)}"
        )


    # ========================================================
    # 3. AI IMAGE GRADING
    # ========================================================

    if not PYTHON_EXE.exists():
        raise HTTPException(
            status_code=500,
            detail=f"AI Python executable not found: {PYTHON_EXE}"
        )

    if not PREDICT_SCRIPT.exists():
        raise HTTPException(
            status_code=500,
            detail=f"AI prediction script not found: {PREDICT_SCRIPT}"
        )

    try:
        result = subprocess.run(
            [
                str(PYTHON_EXE),
                str(PREDICT_SCRIPT),
                str(file_path)
            ],
            capture_output=True,
            text=True
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run AI grading model: {str(e)}"
        )


    # ========================================================
    # 4. CHECK AI PROCESS RESULT
    # ========================================================

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"AI grading failed: {result.stderr}"
        )


    # ========================================================
    # 5. PARSE AI RESULT
    # ========================================================

    try:
        grade = json.loads(result.stdout)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=(
                "Invalid response from AI grading model. "
                f"Model output: {result.stdout}"
            )
        )


    # ========================================================
    # 6. VALIDATE AI RESULT
    # ========================================================

    required_grade_fields = [
        "condition",
        "confidence",
        "recommendation"
    ]

    for field in required_grade_fields:
        if field not in grade:
            raise HTTPException(
                status_code=500,
                detail=f"AI grading response missing field: {field}"
            )


    # ========================================================
    # 7. AI PRICE PREDICTION
    # ========================================================

    current_month = datetime.now().month

    try:
        ai_result = predict_price(
            crop=name,
            location=location,
            quantity=quantity,
            month=current_month
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI price prediction failed: {str(e)}"
        )


    # ========================================================
    # 8. VALIDATE PRICE PREDICTION
    # ========================================================

    if "predicted_price_per_kg" not in ai_result:
        raise HTTPException(
            status_code=500,
            detail="AI price prediction did not return a price"
        )

    if "demand" not in ai_result:
        raise HTTPException(
            status_code=500,
            detail="AI price prediction did not return demand"
        )


    # ========================================================
    # 9. CREATE PRODUCT
    # ========================================================

    new_product = Product(
        name=name,
        description=description,
        quantity=quantity,

        # AI predicted price
        price=ai_result["predicted_price_per_kg"],

        unit=unit,
        location=location,

        # GPS coordinates
        latitude=latitude,
        longitude=longitude,

        # AI demand
        ai_demand=ai_result["demand"],

        # Image
        image_path=str(file_path),

        # AI image grading
        condition=grade["condition"],
        grade_confidence=grade["confidence"],
        recommendation=grade["recommendation"],

        # Farmer
        owner_id=current_user.id
    )


    # ========================================================
    # 10. ADD PRODUCT
    # ========================================================

    db.add(new_product)

    # flush() sends the INSERT to the database without
    # committing the transaction.
    #
    # This gives us new_product.id so that it can be used
    # by RottenCropRequest.
    db.flush()


    # ========================================================
    # 11. AUTOMATIC ROTTEN CROP REQUEST
    # ========================================================

    if str(grade["condition"]).lower() == "rotten":

        rotten_request = RottenCropRequest(
            product_id=new_product.id,
            farmer_id=current_user.id,
            quantity=new_product.quantity,
            location=new_product.location,
            status="Pending"
        )

        db.add(rotten_request)


    # ========================================================
    # 12. COMMIT EVERYTHING
    # ========================================================

    try:
        db.commit()

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save product: {str(e)}"
        )


    # ========================================================
    # 13. REFRESH PRODUCT
    # ========================================================

    db.refresh(new_product)


    # ========================================================
    # 14. RETURN PRODUCT
    # ========================================================

    return new_product


# ============================================================
# GET ALL PRODUCTS
# ============================================================

@router.get("/", response_model=list[ProductResponse])
def get_products(
    db: Session = Depends(get_db)
):
    products = (
        db.query(Product)
        .all()
    )

    return products


# ============================================================
# GET SINGLE PRODUCT
# ============================================================
@router.get(
    "/my-products",
    response_model=list[ProductResponse]
)
def get_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):
    products = (
        db.query(Product)
        .filter(
            Product.owner_id == current_user.id
        )
        .all()
    )

    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# ============================================================
# UPDATE PRODUCT
# ============================================================

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):
    # ========================================================
    # 1. FIND PRODUCT
    # ========================================================

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )


    # ========================================================
    # 2. OWNERSHIP CHECK
    # ========================================================

    if product.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own products"
        )


    # ========================================================
    # 3. AI PRICE PREDICTION
    # ========================================================

    current_month = datetime.now().month

    try:
        ai_result = predict_price(
            crop=product_update.name,
            location=product_update.location,
            quantity=product_update.quantity,
            month=current_month
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI price prediction failed: {str(e)}"
        )


    # ========================================================
    # 4. UPDATE PRODUCT
    # ========================================================

    product.name = product_update.name
    product.description = product_update.description
    product.quantity = product_update.quantity

    # AI predicted price
    product.price = ai_result["predicted_price_per_kg"]

    product.unit = product_update.unit
    product.location = product_update.location

    # GPS coordinates
    product.latitude = product_update.latitude
    product.longitude = product_update.longitude

    # AI demand
    product.ai_demand = ai_result["demand"]


    # ========================================================
    # 5. SAVE
    # ========================================================

    try:
        db.commit()
        db.refresh(product)

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to update product: {str(e)}"
        )


    return product


# ============================================================
# DELETE PRODUCT
# ============================================================

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):
    # ========================================================
    # 1. FIND PRODUCT
    # ========================================================

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )


    # ========================================================
    # 2. OWNERSHIP CHECK
    # ========================================================

    if product.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own products"
        )


    # ========================================================
    # 3. DELETE PRODUCT
    # ========================================================

    try:
        db.delete(product)
        db.commit()

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete product: {str(e)}"
        )


    return {
        "message": "Product deleted successfully"
    }


# ============================================================
# GET MY PRODUCTS
# Farmer only
# ============================================================

