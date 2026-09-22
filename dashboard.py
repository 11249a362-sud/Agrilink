from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.product import Product
from app.models.order import Order
from app.models.user import User


def get_dashboard_stats(db: Session):
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()

    completed_deliveries = db.query(Order).filter(
        Order.status == "Delivered"
    ).count()

    pending_orders = db.query(Order).filter(
        Order.status == "Pending"
    ).count()

    accepted_orders = db.query(Order).filter(
        Order.status == "Accepted"
    ).count()

    top_crop = (
        db.query(Product.name, func.count(Product.id))
        .group_by(Product.name)
        .order_by(func.count(Product.id).desc())
        .first()
    )

    top_buyer = (
        db.query(User.name, func.count(Order.id))
        .join(Order, Order.buyer_id == User.id)
        .filter(User.role == "industry")
        .group_by(User.name)
        .order_by(func.count(Order.id).desc())
        .first()
    )

    average_ai_price = db.query(func.avg(Product.price)).scalar() or 0

    high_demand_products = db.query(Product).filter(
        Product.ai_demand == "High"
    ).count()

    # Revenue = quantity × price for delivered orders
    total_revenue = (
        db.query(func.sum(Order.quantity * Product.price))
        .join(Product, Order.product_id == Product.id)
        .filter(Order.status == "Delivered")
        .scalar()
    ) or 0

    # Delivery success rate
    delivery_success_rate = 0
    if total_orders > 0:
        delivery_success_rate = round(
            (completed_deliveries / total_orders) * 100, 2
        )

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "completed_deliveries": completed_deliveries,
        "pending_orders": pending_orders,
        "accepted_orders": accepted_orders,
        "top_crop": top_crop[0] if top_crop else None,
        "top_buyer": top_buyer[0] if top_buyer else None,
        "average_ai_price": round(float(average_ai_price), 2),
        "high_demand_products": high_demand_products,
        "total_revenue": round(float(total_revenue), 2),
        "delivery_success_rate": delivery_success_rate
    }