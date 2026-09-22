from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models.supplier_product import SupplierProduct
from app.models.supplier_order import SupplierOrder
from app.models.user import User

from app.schemas.supplier_product_schema import (
    SupplierProductCreate,
    SupplierProductResponse
)

from app.schemas.supplier_order_schema import (
    SupplierOrderCreate,
    SupplierOrderResponse
)

from app.utils.dependencies import (
    require_supplier,
    require_farmer
)

from app.services.location_service import (
    get_location_from_coordinates
)


router = APIRouter(
    prefix="/supplier",
    tags=["Supplier"]
)


# ============================================================
# SUPPLIER PRODUCTS
# ============================================================

@router.post(
    "/products",
    response_model=SupplierProductResponse
)
def create_supplier_product(
    product: SupplierProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    # --------------------------------------------------------
    # Validate quantity
    # --------------------------------------------------------

    if product.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    # --------------------------------------------------------
    # Validate price
    # --------------------------------------------------------

    if product.price < 0:
        raise HTTPException(
            status_code=400,
            detail="Price cannot be negative"
        )

    # --------------------------------------------------------
    # Automatically determine location
    # --------------------------------------------------------

    location = "Unknown"

    if (
        product.latitude is not None
        and product.longitude is not None
    ):

        try:

            detected_location = get_location_from_coordinates(
                product.latitude,
                product.longitude
            )

            if detected_location:
                location = detected_location

        except Exception:
            # Do not fail product creation just because
            # reverse geocoding failed.
            location = "Unknown"

    # --------------------------------------------------------
    # Create product
    # --------------------------------------------------------

    new_product = SupplierProduct(

        name=product.name,

        description=product.description,

        category=product.category,

        quantity=product.quantity,

        price=product.price,

        unit=product.unit,

        location=location,

        latitude=product.latitude,

        longitude=product.longitude,

        owner_id=current_user.id
    )

    db.add(new_product)

    db.commit()

    db.refresh(new_product)

    return new_product


# ============================================================
# GET ALL SUPPLIER PRODUCTS
# ============================================================
@router.get(
    "/products",
    response_model=list[SupplierProductResponse]
)
def get_supplier_products(
    category: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(SupplierProduct)

    if category:
        query = query.filter(
            SupplierProduct.category == category
        )

    return query.all()

# ============================================================
# GET MY SUPPLIER PRODUCTS
# ============================================================

@router.get(
    "/my-products",
    response_model=list[SupplierProductResponse]
)
def get_my_supplier_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    return (
        db.query(SupplierProduct)
        .filter(
            SupplierProduct.owner_id == current_user.id
        )
        .all()
    )


# ============================================================
# UPDATE SUPPLIER PRODUCT
# ============================================================

@router.put(
    "/products/{product_id}",
    response_model=SupplierProductResponse
)
def update_supplier_product(
    product_id: int,
    product: SupplierProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    existing = (
        db.query(SupplierProduct)
        .filter(
            SupplierProduct.id == product_id,
            SupplierProduct.owner_id == current_user.id
        )
        .first()
    )

    if not existing:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # --------------------------------------------------------
    # Validate quantity
    # --------------------------------------------------------

    if product.quantity <= 0:

        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    # --------------------------------------------------------
    # Validate price
    # --------------------------------------------------------

    if product.price < 0:

        raise HTTPException(
            status_code=400,
            detail="Price cannot be negative"
        )

    # --------------------------------------------------------
    # Update location
    # --------------------------------------------------------

    location = existing.location

    if (
        product.latitude is not None
        and product.longitude is not None
    ):

        try:

            detected_location = get_location_from_coordinates(
                product.latitude,
                product.longitude
            )

            if detected_location:
                location = detected_location

        except Exception:
            pass

    # --------------------------------------------------------
    # Update fields
    # --------------------------------------------------------

    existing.name = product.name

    existing.description = product.description

    existing.category = product.category

    existing.quantity = product.quantity

    existing.price = product.price

    existing.unit = product.unit

    existing.latitude = product.latitude

    existing.longitude = product.longitude

    existing.location = location

    db.commit()

    db.refresh(existing)

    return existing


# ============================================================
# DELETE SUPPLIER PRODUCT
# ============================================================

@router.delete(
    "/products/{product_id}"
)
def delete_supplier_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    product = (
        db.query(SupplierProduct)
        .filter(
            SupplierProduct.id == product_id,
            SupplierProduct.owner_id == current_user.id
        )
        .first()
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)

    db.commit()

    return {
        "message": "Supplier product deleted"
    }


# ============================================================
# FARMER PLACES SUPPLIER ORDER
# ============================================================

@router.post(
    "/orders",
    response_model=SupplierOrderResponse
)
def place_supplier_order(
    order: SupplierOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):

    product = (
        db.query(SupplierProduct)
        .filter(
            SupplierProduct.id == order.product_id
        )
        .first()
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Supplier product not found"
        )

    if order.quantity <= 0:

        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    if order.quantity > product.quantity:

        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock"
        )

    new_order = SupplierOrder(

        product_id=order.product_id,

        farmer_id=current_user.id,

        quantity=order.quantity,

        status="Pending"
    )

    db.add(new_order)

    db.commit()

    db.refresh(new_order)

    return new_order


# ============================================================
# SUPPLIER VIEWS THEIR ORDERS
# ============================================================

@router.get(
    "/orders",
    response_model=list[SupplierOrderResponse]
)
def get_supplier_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    orders = (
        db.query(SupplierOrder)
        .join(SupplierProduct)
        .filter(
            SupplierProduct.owner_id == current_user.id
        )
        .all()
    )

    return orders


# ============================================================
# SUPPLIER ACCEPTS ORDER
# ============================================================

@router.put(
    "/orders/{order_id}/accept"
)
def accept_supplier_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    order = (
        db.query(SupplierOrder)
        .join(SupplierProduct)
        .filter(
            SupplierOrder.id == order_id,
            SupplierProduct.owner_id == current_user.id
        )
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.status != "Pending":

        raise HTTPException(
            status_code=400,
            detail="Order already processed"
        )

    product = (
        db.query(SupplierProduct)
        .filter(
            SupplierProduct.id == order.product_id
        )
        .first()
    )

    if order.quantity > product.quantity:

        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    # Remove ordered quantity from stock
    product.quantity -= order.quantity

    order.status = "Accepted"

    db.commit()

    return {
        "message": "Supplier order accepted",
        "order_id": order.id,
        "status": order.status
    }


# ============================================================
# SUPPLIER REJECTS ORDER
# ============================================================

@router.put(
    "/orders/{order_id}/reject"
)
def reject_supplier_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier)
):

    order = (
        db.query(SupplierOrder)
        .join(SupplierProduct)
        .filter(
            SupplierOrder.id == order_id,
            SupplierProduct.owner_id == current_user.id
        )
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.status != "Pending":

        raise HTTPException(
            status_code=400,
            detail="Order already processed"
        )

    order.status = "Rejected"

    db.commit()

    return {
        "message": "Supplier order rejected",
        "order_id": order.id,
        "status": order.status
    }