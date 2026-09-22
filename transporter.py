from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.order import Order
from app.models.user import User
from app.models.location import Location
from app.schemas.location_schema import LocationUpdate, LocationResponse
from app.utils.dependencies import require_transporter


router = APIRouter(
    prefix="/transporter",
    tags=["Transporter"]
)


# ============================================================
# TRANSPORTER - VIEW ASSIGNED ORDERS
# ============================================================

@router.get("/orders")
def get_transporter_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_transporter)
):

    orders = (
        db.query(Order)
        .filter(
            Order.transporter_id == current_user.id
        )
        .all()
    )

    return {
        "count": len(orders),
        "orders": [
            {
                "id": order.id,
                "status": order.status,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "buyer_id": order.buyer_id,
                "created_at": order.created_at
            }
            for order in orders
        ]
    }


# ============================================================
# TRANSPORTER - UPDATE DELIVERY STATUS
# ============================================================

@router.put("/orders/{order_id}/status")
def update_delivery_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_transporter)
):

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
            detail="Order not assigned to this transporter"
        )

    allowed_statuses = [
        "Assigned",
        "Picked Up",
        "In Transit",
        "Delivered"
    ]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid delivery status"
        )

    order.status = status

    # Free transporter after delivery
    if status == "Delivered":
        current_user.availability_status = "available"

    db.commit()
    db.refresh(order)

    return {
        "message": "Delivery status updated",
        "order_id": order.id,
        "status": order.status
    }


# ============================================================
# TRANSPORTER - UPDATE GPS LOCATION
# ============================================================

@router.put(
    "/orders/{order_id}/location",
    response_model=LocationResponse
)
def update_location(
    order_id: int,
    location: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_transporter)
):

    # --------------------------------------------------------
    # Verify that this order belongs to this transporter
    # --------------------------------------------------------

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
            detail="Assigned order not found"
        )

    # --------------------------------------------------------
    # 1. Update transporter's current GPS location
    # --------------------------------------------------------

    current_user.latitude = location.latitude
    current_user.longitude = location.longitude

    # --------------------------------------------------------
    # 2. Also save the GPS location for this specific order
    # --------------------------------------------------------

    existing = (
        db.query(Location)
        .filter(
            Location.order_id == order_id
        )
        .first()
    )

    if existing:

        existing.latitude = location.latitude
        existing.longitude = location.longitude

        db.commit()
        db.refresh(existing)

        return existing

    # --------------------------------------------------------
    # Create location record if this is the first GPS update
    # --------------------------------------------------------

    new_location = Location(
        order_id=order_id,
        latitude=location.latitude,
        longitude=location.longitude
    )

    db.add(new_location)

    db.commit()
    db.refresh(new_location)

    return new_location