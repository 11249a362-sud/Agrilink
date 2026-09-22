from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.rotten_crop import RottenCropRequest
from app.models.product import Product
from app.models.fertilizer import FertilizerProduct
from app.models.user import User
from app.utils.dependencies import require_farmer, require_supplier

router = APIRouter(
    prefix="/rotten-crops",
    tags=["Rotten Crops"]
)


# ============================================================
# FARMER CREATES ROTTEN CROP REQUEST
# ============================================================

@router.post("/")
def create_rotten_crop_request(
    product_id: int,
    quantity: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
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

    if product.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create requests for your own products"
        )

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    if quantity > product.quantity:
        raise HTTPException(
            status_code=400,
            detail="Quantity exceeds available product quantity"
        )

    request = RottenCropRequest(
        product_id=product.id,
        farmer_id=current_user.id,
        quantity=quantity,
        location=product.location,
        status="Pending"
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return {
        "message": "Rotten crop request created successfully",
        "request_id": request.id,
        "status": request.status
    }


# ============================================================
# SUPPLIER VIEWS ALL PENDING REQUESTS
# ============================================================

@router.get("/")
def get_rotten_crop_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    requests = (
        db.query(RottenCropRequest)
        .filter(RottenCropRequest.status == "Pending")
        .all()
    )

    return requests


# ============================================================
# SUPPLIER ACCEPTS COLLECTION
# AUTOMATICALLY CREATES FERTILIZER PRODUCT
# ============================================================

@router.put("/{request_id}/accept")
def accept_rotten_crop_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    request = (
        db.query(RottenCropRequest)
        .filter(RottenCropRequest.id == request_id)
        .first()
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )

    if request.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Request has already been processed"
        )

    # --------------------------------------------------------
    # Get original crop product
    # --------------------------------------------------------

    product = (
        db.query(Product)
        .filter(Product.id == request.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Original product not found"
        )

    # --------------------------------------------------------
    # Accept the request
    # --------------------------------------------------------

    request.status = "Accepted"

    # --------------------------------------------------------
    # Reduce farmer's product quantity
    # --------------------------------------------------------

    product.quantity -= request.quantity

    if product.quantity < 0:
        product.quantity = 0

    # --------------------------------------------------------
    # Automatically create fertilizer product
    # --------------------------------------------------------

    fertilizer = FertilizerProduct(
        name=f"Organic Fertilizer - {product.name}",
        description=f"Produced from collected {product.name} crop waste",
        quantity=request.quantity,
        price=12.0,
        unit="kg",
        location=request.location,
        supplier_id=current_user.id
    )

    db.add(fertilizer)
    db.commit()

    db.refresh(request)
    db.refresh(product)
    db.refresh(fertilizer)

    return {
        "message": "Rotten crop collected and fertilizer product created",
        "request_id": request.id,
        "status": request.status,
        "fertilizer_product_id": fertilizer.id
    }


# ============================================================
# FARMER VIEWS THEIR ROTTEN CROP REQUESTS
# ============================================================

@router.get("/my-requests")
def get_my_rotten_crop_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):

    requests = (
        db.query(RottenCropRequest)
        .filter(RottenCropRequest.farmer_id == current_user.id)
        .all()
    )

    return requests