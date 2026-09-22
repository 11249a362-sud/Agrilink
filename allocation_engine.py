from sqlalchemy.orm import Session

from app.models.community_demand import CommunityDemand


def allocate_stock(
    db: Session,
    crop: str,
    quantity: float,
    location: str
):
    """
    Smart AI Allocation Engine

    Rules:
    - Reserve actual community demand + 50% buffer
    - Minimum reserve: 20 kg
    - Maximum reserve: 30% of total harvest
    """

    demands = (
        db.query(CommunityDemand)
        .filter(
            CommunityDemand.crop_name.ilike(crop),
            CommunityDemand.location == location
        )
        .all()
    )

    community_demand = sum(d.quantity for d in demands)

    reserve = max(20, community_demand * 1.5)

    max_reserve = quantity * 0.30

    community_quantity = min(reserve, max_reserve)

    industry_quantity = quantity - community_quantity

    return {
        "crop": crop,
        "location": location,
        "community_demand": community_demand,
        "industry_quantity": round(industry_quantity, 2),
        "community_quantity": round(community_quantity, 2),
        "community_ratio": round(community_quantity / quantity, 3),
        "reason": "Demand-based AI allocation with safety buffer"
    }