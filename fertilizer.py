from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.fertilizer_order import FertilizerOrder
from app.utils.dependencies import require_farmer
from app.database.database import get_db
from app.models.fertilizer import FertilizerProduct
from app.models.user import User
from app.utils.dependencies import require_supplier, require_farmer

router = APIRouter(
    prefix="/fertilizers",
    tags=["Fertilizers"]
)

# --------------------------------------------------
# Supplier creates fertilizer product
# --------------------------------------------------

@router.post("/")
def create_fertilizer_product(
    name: str,
    description: str,
    quantity: float,
    price: float,
    unit: str,
    location: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    fertilizer = FertilizerProduct(
        name=name,
        description=description,
        quantity=quantity,
        price=price,
        unit=unit,
        location=location,
        supplier_id=current_user.id
    )

    db.add(fertilizer)
    db.commit()
    db.refresh(fertilizer)

    return fertilizer


# --------------------------------------------------
# Farmer views all fertilizers
# --------------------------------------------------

@router.get("/")
def get_all_fertilizers(
    db: Session = Depends(get_db)
):

    return db.query(FertilizerProduct).all()


# --------------------------------------------------
# Supplier views only their fertilizer products
# --------------------------------------------------

@router.get("/my-products")
def get_my_fertilizers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    return (
        db.query(FertilizerProduct)
        .filter(FertilizerProduct.supplier_id == current_user.id)
        .all()
    )
@router.put("/{fertilizer_id}")
def update_fertilizer_product(
    fertilizer_id: int,
    name: str,
    description: str,
    quantity: float,
    price: float,
    unit: str,
    location: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):
    fertilizer = (
        db.query(FertilizerProduct)
        .filter(FertilizerProduct.id == fertilizer_id)
        .first()
    )

    if not fertilizer:
        raise HTTPException(status_code=404, detail="Fertilizer product not found")

    if fertilizer.supplier_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own fertilizer products")

    fertilizer.name = name
    fertilizer.description = description
    fertilizer.quantity = quantity
    fertilizer.price = price
    fertilizer.unit = unit
    fertilizer.location = location

    db.commit()
    db.refresh(fertilizer)

    return fertilizer
@router.delete("/{fertilizer_id}")
def delete_fertilizer_product(
    fertilizer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):
    fertilizer = (
        db.query(FertilizerProduct)
        .filter(FertilizerProduct.id == fertilizer_id)
        .first()
    )

    if not fertilizer:
        raise HTTPException(status_code=404, detail="Fertilizer product not found")

    if fertilizer.supplier_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own fertilizer products")

    db.delete(fertilizer)
    db.commit()

    return {"message": "Fertilizer product deleted successfully"}
@router.post("/orders")
def place_fertilizer_order(
    fertilizer_id: int,
    quantity: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):
    fertilizer = (
        db.query(FertilizerProduct)
        .filter(FertilizerProduct.id == fertilizer_id)
        .first()
    )

    if not fertilizer:
        raise HTTPException(status_code=404, detail="Fertilizer product not found")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

    if quantity > fertilizer.quantity:
        raise HTTPException(status_code=400, detail="Insufficient fertilizer quantity")

    order = FertilizerOrder(
        fertilizer_id=fertilizer.id,
        farmer_id=current_user.id,
        quantity=quantity,
        status="Pending"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order
@router.get("/orders/my-orders")
def get_my_fertilizer_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):
    return (
        db.query(FertilizerOrder)
        .filter(FertilizerOrder.farmer_id == current_user.id)
        .all()
    )
@router.get("/orders")
def get_supplier_fertilizer_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):
    return (
        db.query(FertilizerOrder)
        .join(FertilizerProduct)
        .filter(FertilizerProduct.supplier_id == current_user.id)
        .all()
    )
@router.get("/orders")
def get_supplier_fertilizer_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):
    return (
        db.query(FertilizerOrder)
        .join(FertilizerProduct)
        .filter(FertilizerProduct.supplier_id == current_user.id)
        .all()
    )
@router.put("/orders/{order_id}/accept")
def accept_fertilizer_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):
    order = (
        db.query(FertilizerOrder)
        .join(FertilizerProduct)
        .filter(
            FertilizerOrder.id == order_id,
            FertilizerProduct.supplier_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "Pending":
        raise HTTPException(status_code=400, detail="Order already processed")

    fertilizer = (
        db.query(FertilizerProduct)
        .filter(FertilizerProduct.id == order.fertilizer_id)
        .first()
    )

    if order.quantity > fertilizer.quantity:
        raise HTTPException(status_code=400, detail="Not enough fertilizer stock")

    fertilizer.quantity -= order.quantity
    order.status = "Accepted"

    db.commit()
    db.refresh(order)

    return order
@router.put("/orders/{order_id}/reject")
def reject_fertilizer_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):
    order = (
        db.query(FertilizerOrder)
        .join(FertilizerProduct)
        .filter(
            FertilizerOrder.id == order_id,
            FertilizerProduct.supplier_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "Pending":
        raise HTTPException(status_code=400, detail="Order already processed")

    order.status = "Rejected"

    db.commit()
    db.refresh(order)

    return order