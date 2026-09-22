from datetime import datetime
from sqlalchemy.orm import Session

from app.models.auction import Auction
from app.models.bid import Bid
from app.models.user import User


def get_live_auction_details(
    db: Session,
    auction_id: int
):
    auction = (
        db.query(Auction)
        .filter(Auction.id == auction_id)
        .first()
    )

    if not auction:
        return {"error": "Auction not found"}

    bids = (
        db.query(Bid, User)
        .join(User, Bid.bidder_id == User.id)
        .filter(Bid.auction_id == auction_id)
        .order_by(Bid.bid_price.desc())
        .all()
    )

    remaining = auction.end_time - datetime.utcnow()

    if remaining.total_seconds() < 0:
        remaining_str = "Expired"
    else:
        remaining_str = str(remaining).split(".")[0]

    bid_history = []

    for bid, user in bids:
        bid_history.append({
            "bidder": user.name,
            "bidder_id": user.id,
            "role": user.role,
            "bid_price": bid.bid_price,
            "quantity": bid.quantity,
            "created_at": bid.created_at
        })

    return {
        "auction_id": auction.id,
        "crop": auction.crop_name,
        "location": auction.location,
        "quantity": auction.quantity,
        "unit": auction.unit,
        "auction_type": auction.auction_type,
        "minimum_price": auction.minimum_price,
        "highest_bid": auction.current_highest_bid,
        "status": auction.status,
        "time_remaining": remaining_str,
        "total_bids": len(bid_history),
        "bids": bid_history
    }