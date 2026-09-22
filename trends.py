from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.product import Product
from app.models.order import Order

MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]


def get_trends(db: Session):
    # Monthly revenue from delivered orders
    revenue_rows = (
        db.query(
            extract("month", Order.created_at).label("month"),
            func.sum(Order.quantity * Product.price).label("revenue")
        )
        .join(Product, Order.product_id == Product.id)
        .filter(Order.status == "Delivered")
        .group_by(extract("month", Order.created_at))
        .all()
    )

    monthly_revenue = []

    for month_num, revenue in revenue_rows:
        monthly_revenue.append({
            "month": MONTHS[int(month_num) - 1],
            "revenue": round(float(revenue), 2)
        })

    # Crop distribution
    crop_rows = (
        db.query(
            Product.name,
            func.count(Product.id)
        )
        .group_by(Product.name)
        .all()
    )

    crop_distribution = []

    for crop, count in crop_rows:
        crop_distribution.append({
            "crop": crop,
            "count": count
        })

    return {
        "monthly_revenue": monthly_revenue,
        "crop_distribution": crop_distribution
    }