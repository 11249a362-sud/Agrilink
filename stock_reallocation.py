from sqlalchemy.orm import Session

from app.models.auction import Auction
from app.models.bid import Bid
from app.ai.reallocation_ai import decide_reallocation


def reallocate_unsold_stock(
    db: Session,
    closed_auction: Auction
):
    """
    AI-powered stock reallocation engine.

    When an auction closes, calculate the unsold quantity and transfer only a
    portion of it to the paired auction (industry ↔ community) based on AI
    demand analysis.
    """

    # Determine paired auction type
    if closed_auction.auction_type == "industry":
        target_type = "community"
    else:
        target_type = "industry"

    # Highest winning bid
    highest_bid = (
        db.query(Bid)
        .filter(Bid.auction_id == closed_auction.id)
        .order_by(Bid.bid_price.desc())
        .first()
    )

    sold_quantity = highest_bid.quantity if highest_bid else 0

    unsold_quantity = max(
        closed_auction.quantity - sold_quantity,
        0
    )

    if unsold_quantity == 0:
        return {
            "unsold_quantity": 0,
            "reallocated": False,
            "reason": "All stock sold"
        }

    # Find paired auction
    target_auction = (
        db.query(Auction)
        .filter(
            Auction.product_id == closed_auction.product_id,
            Auction.auction_type == target_type,
            Auction.status == "Open"
        )
        .first()
    )

    if not target_auction:
        return {
            "unsold_quantity": unsold_quantity,
            "reallocated": False,
            "reason": "No paired open auction found"
        }

    # ----------------------------------------------------
    # AI decides how much stock to transfer
    # ----------------------------------------------------
    # You can later replace "High" with a real demand prediction from your AI.
    decision = decide_reallocation(
        unsold_quantity=unsold_quantity,
        demand_level="High"
    )

    transfer_quantity = decision["transfer_quantity"]
    reserve_quantity = decision["reserve_quantity"]

    # Transfer stock
    target_auction.quantity += transfer_quantity

    db.commit()
    db.refresh(target_auction)

    return {
        "unsold_quantity": round(unsold_quantity, 2),
        "reallocated": True,
        "transferred_quantity": round(transfer_quantity, 2),
        "reserved_quantity": round(reserve_quantity, 2),
        "target_auction_id": target_auction.id,
        "new_quantity": round(target_auction.quantity, 2),
        "ai_ratio": decision["ratio"],
        "ai_reason": decision["reason"]
    }