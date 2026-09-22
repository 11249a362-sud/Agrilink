from math import radians, sin, cos, sqrt, atan2

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.order import Order
from app.models.product import Product


def calculate_distance(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float
) -> float:

    earth_radius_km = 6371.0

    lat1 = radians(latitude1)
    lon1 = radians(longitude1)

    lat2 = radians(latitude2)
    lon2 = radians(longitude2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius_km * c


def assign_transporter(order: Order, db: Session):

    if order.status != "Accepted":
        raise HTTPException(
            status_code=400,
            detail="Only accepted orders can be assigned a transporter."
        )

    product = (
        db.query(Product)
        .filter(Product.id == order.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found."
        )

    if product.latitude is None or product.longitude is None:
        return None

    transporters = (
        db.query(User)
        .filter(
            User.role == "transporter",
            User.availability_status == "available",
            User.latitude.isnot(None),
            User.longitude.isnot(None)
        )
        .all()
    )

    if not transporters:
        return None

    nearest_transporter = None
    shortest_distance = float("inf")

    for transporter in transporters:

        distance = calculate_distance(
            product.latitude,
            product.longitude,
            transporter.latitude,
            transporter.longitude
        )

        if distance < shortest_distance:
            shortest_distance = distance
            nearest_transporter = transporter

    if nearest_transporter:

        order.transporter_id = nearest_transporter.id
        order.status = "Assigned"

        nearest_transporter.availability_status = "busy"

        db.commit()
        db.refresh(order)

        return nearest_transporter

    return None