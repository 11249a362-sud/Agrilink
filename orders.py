from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.utils.dependencies import (
    get_current_user,
    require_industry,
    require_farmer,
)

from app.database.database import get_db

from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.models.location import Location

from app.schemas.location_schema import LocationResponse

from app.schemas.order_schema import (
    OrderCreate,
    OrderResponse,
    OrderStatusResponse,
    AssignTransporterRequest,
)

from app.services.transporter_assignment import assign_transporter


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# ============================================================
# INDUSTRY - PLACE ORDER
# ============================================================

@router.post("/", response_model=OrderResponse)
def place_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_industry)
):

    product = (
        db.query(Product)
        .filter(Product.id == order.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if order.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero."
        )

    if order.quantity > product.quantity:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock."
        )

    new_order = Order(
        product_id=order.product_id,
        buyer_id=current_user.id,
        quantity=order.quantity,
        status="Pending"
    )

    product.quantity -= order.quantity

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


# ============================================================
# INDUSTRY - VIEW OWN ORDERS
# ============================================================

@router.get(
    "/my-orders",
    response_model=list[OrderResponse]
)
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_industry)
):

    orders = (
        db.query(Order)
        .filter(
            Order.buyer_id == current_user.id
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


# ============================================================
# INDUSTRY - ORDER HISTORY
# ============================================================

@router.get(
    "/history",
    response_model=list[OrderResponse]
)
def get_order_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_industry)
):

    orders = (
        db.query(Order)
        .filter(
            Order.buyer_id == current_user.id,
            Order.status == "Delivered"
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


# ============================================================
# FARMER - VIEW FARMER ORDERS
# ============================================================

@router.get(
    "/farmer-orders",
    response_model=list[OrderResponse]
)
def get_farmer_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):

    orders = (
        db.query(Order)
        .join(
            Product,
            Order.product_id == Product.id
        )
        .filter(
            Product.owner_id == current_user.id
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


# ============================================================
# FARMER - ACCEPT ORDER
# ============================================================

@router.put(
    "/{order_id}/accept",
    response_model=OrderStatusResponse
)
def accept_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):

    order = (
        db.query(Order)
        .join(
            Product,
            Order.product_id == Product.id
        )
        .filter(
            Order.id == order_id,
            Product.owner_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    if order.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be accepted."
        )

    order.status = "Accepted"

    db.commit()
    db.refresh(order)

    return {
        "message": "Order accepted successfully.",
        "order": order
    }


# ============================================================
# FARMER - REJECT ORDER
# ============================================================

@router.put(
    "/{order_id}/reject",
    response_model=OrderStatusResponse
)
def reject_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):

    order = (
        db.query(Order)
        .join(
            Product,
            Order.product_id == Product.id
        )
        .filter(
            Order.id == order_id,
            Product.owner_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    if order.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be rejected."
        )

    order.status = "Rejected"

    db.commit()
    db.refresh(order)

    return {
        "message": "Order rejected successfully.",
        "order": order
    }


# ============================================================
# FARMER - MANUAL TRANSPORTER ASSIGNMENT
# ============================================================

@router.put(
    "/{order_id}/assign-transporter",
    response_model=OrderStatusResponse
)
def assign_transporter_manually(
    order_id: int,
    data: AssignTransporterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):

    order = (
        db.query(Order)
        .join(
            Product,
            Order.product_id == Product.id
        )
        .filter(
            Order.id == order_id,
            Product.owner_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    if order.status != "Accepted":
        raise HTTPException(
            status_code=400,
            detail="Only accepted orders can be assigned."
        )

    transporter = (
        db.query(User)
        .filter(
            User.id == data.transporter_id,
            User.role == "transporter"
        )
        .first()
    )

    if not transporter:
        raise HTTPException(
            status_code=404,
            detail="Transporter not found."
        )

    if transporter.availability_status != "available":
        raise HTTPException(
            status_code=400,
            detail="Transporter is not available."
        )

    order.transporter_id = transporter.id
    order.status = "Assigned"

    transporter.availability_status = "busy"

    db.commit()
    db.refresh(order)

    return {
        "message": "Transporter assigned successfully.",
        "order": order
    }


# ============================================================
# FARMER - AUTOMATIC NEAREST TRANSPORTER ASSIGNMENT
# ============================================================

@router.put(
    "/{order_id}/auto-assign-transporter",
    response_model=OrderStatusResponse
)
def auto_assign_transporter(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):

    order = (
        db.query(Order)
        .join(
            Product,
            Order.product_id == Product.id
        )
        .filter(
            Order.id == order_id,
            Product.owner_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    if order.status != "Accepted":
        raise HTTPException(
            status_code=400,
            detail="Only accepted orders can be assigned a transporter."
        )

    transporter = assign_transporter(
        order,
        db
    )

    if not transporter:
        return {
            "message": (
                "No available transporter found automatically. "
                "Manual transporter assignment is available."
            ),
            "order": order
        }

    return {
        "message": "Nearest transporter assigned successfully.",
        "order": order
    }


# ============================================================
# FARMER - DELIVERY HISTORY
# ============================================================

@router.get(
    "/farmer-history",
    response_model=list[OrderResponse]
)
def get_farmer_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer)
):

    orders = (
        db.query(Order)
        .join(
            Product,
            Order.product_id == Product.id
        )
        .filter(
            Product.owner_id == current_user.id,
            Order.status == "Delivered"
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


# ============================================================
# TRANSPORTER - VIEW ASSIGNED ORDERS
# ============================================================

@router.get(
    "/transporter-orders",
    response_model=list[OrderResponse]
)
def get_transporter_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "transporter":
        raise HTTPException(
            status_code=403,
            detail="Only transporters can access this endpoint."
        )

    orders = (
        db.query(Order)
        .filter(
            Order.transporter_id == current_user.id
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


# ============================================================
# TRANSPORTER - ACCEPT DELIVERY
# ============================================================

@router.put(
    "/{order_id}/accept-delivery",
    response_model=OrderStatusResponse
)
def accept_delivery(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "transporter":
        raise HTTPException(
            status_code=403,
            detail="Only transporters can accept deliveries."
        )

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.transporter_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    if order.status != "Assigned":
        raise HTTPException(
            status_code=400,
            detail="Only assigned orders can be accepted."
        )

    order.status = "In Transit"

    db.commit()
    db.refresh(order)

    return {
        "message": "Delivery accepted successfully.",
        "order": order
    }


# ============================================================
# TRANSPORTER - MARK ORDER DELIVERED
# ============================================================

@router.put(
    "/{order_id}/deliver",
    response_model=OrderStatusResponse
)
def mark_delivered(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "transporter":
        raise HTTPException(
            status_code=403,
            detail="Only transporters can mark deliveries."
        )

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.transporter_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    if order.status != "In Transit":
        raise HTTPException(
            status_code=400,
            detail="Only orders in transit can be delivered."
        )

    order.status = "Delivered"

    current_user.availability_status = "available"

    db.commit()
    db.refresh(order)

    return {
        "message": "Order marked as delivered.",
        "order": order
    }


# ============================================================
# ORDER LOCATION / TRACKING
# ============================================================

@router.get(
    "/{order_id}/location"
)
def get_order_location(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    authorized = False

    # Buyer
    if current_user.id == order.buyer_id:
        authorized = True

    # Transporter
    if current_user.id == order.transporter_id:
        authorized = True

    # Farmer
    if not authorized:
        product = (
            db.query(Product)
            .filter(
                Product.id == order.product_id
            )
            .first()
        )

        if product and product.owner_id == current_user.id:
            authorized = True

    if not authorized:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view this order."
        )

    if not order.transporter_id:
        return {
            "order_id": order.id,
            "status": order.status,
            "transporter_assigned": False,
            "latitude": None,
            "longitude": None
        }

    transporter = (
        db.query(User)
        .filter(
            User.id == order.transporter_id
        )
        .first()
    )

    if not transporter:
        return {
            "order_id": order.id,
            "status": order.status,
            "transporter_assigned": False,
            "latitude": None,
            "longitude": None
        }

    return {
        "order_id": order.id,
        "status": order.status,
        "transporter_assigned": True,
        "transporter_id": transporter.id,
        "latitude": transporter.latitude,
        "longitude": transporter.longitude
    }