from datetime import datetime
from sqlalchemy.orm import Session

from app.models.auction import Auction
from app.ai.auction_ai import select_winner


def close_expired_auctions(db: Session):
    expired_auctions = (
        db.query(Auction)
        .filter(
            Auction.status == "Open",
            Auction.end_time <= datetime.utcnow()
        )
        .all()
    )

    closed = []

    for auction in expired_auctions:
        auction.status = "Closed"
        db.commit()
        db.refresh(auction)

        # Correct parameter order: db first, auction id second
        result = select_winner(db, auction.id)

        closed.append({
            "auction_id": auction.id,
            "winner": result
        })

    return {
        "closed_auctions": closed,
        "count": len(closed)
    }