from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.auction import Auction
from app.models.bid import Bid


def get_live_auctions(db: Session):
    auctions = (
        db.query(Auction)
        .filter(Auction.status == "Open")
        .all()
    )

    result = []

    for auction in auctions:
        bid_count = (
            db.query(func.count(Bid.id))
            .filter(Bid.auction_id == auction.id)
            .scalar()
        ) or 0

        remaining = auction.end_time - datetime.utcnow()

        if remaining.total_seconds() < 0:
            remaining_str = "Expired"
        else:
            remaining_str = str(remaining).split(".")[0]

        result.append({
            "auction_id": auction.id,
            "crop": auction.crop_name,
            "location": auction.location,
            "quantity": auction.quantity,
            "unit": auction.unit,
            "minimum_price": auction.minimum_price,
            "highest_bid": auction.current_highest_bid,
            "time_remaining": remaining_str,
            "total_bids": bid_count
        })

    return result