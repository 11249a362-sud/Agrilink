from sqlalchemy.orm import Session

from app.models.auction import Auction
from app.models.bid import Bid
from app.models.order import Order
from app.models.user import User


def calculate_distance_score(
    farmer_location: str,
    bidder_location: str
):
    """
    Simple distance scoring.

    Same location = 100
    Different location = 70
    """

    if not farmer_location or not bidder_location:
        return 50

    if farmer_location.lower() == bidder_location.lower():
        return 100

    return 70


def calculate_reliability(user: User):
    """
    Mock reliability score.

    Later this can use:
    - completed orders
    - cancellations
    - delivery delays
    - ratings
    """

    return 90


def select_winner(db: Session, auction_id: int):

    auction = (
        db.query(Auction)
        .filter(Auction.id == auction_id)
        .first()
    )

    if not auction:
        return {
            "error": "Auction not found"
        }

    if auction.status in ["Winner Selected", "Closed"]:
        return {
            "message": "Auction has already been processed",
            "auction_id": auction.id,
            "auction_status": auction.status
        }

    bids = (
        db.query(Bid)
        .filter(Bid.auction_id == auction_id)
        .all()
    )

    if not bids:

        auction.status = "Closed"

        db.commit()
        db.refresh(auction)

        return {
            "message": "Auction closed with no bids",
            "auction_id": auction.id,
            "auction_status": auction.status
        }

    best_bid = None
    best_score = -1

    for bid in bids:

        bidder = (
            db.query(User)
            .filter(User.id == bid.bidder_id)
            .first()
        )

        if not bidder:
            continue

        reliability = calculate_reliability(bidder)

        distance_score = calculate_distance_score(
            auction.location,
            bidder.address
        )

        ai_score = (
            bid.bid_price * 0.60
            + reliability * 0.20
            + distance_score * 0.20
        )

        if ai_score > best_score:

            best_score = ai_score
            best_bid = bid

    if best_bid is None:

        auction.status = "Closed"

        db.commit()
        db.refresh(auction)

        return {
            "message": "No valid bids found",
            "auction_id": auction.id,
            "auction_status": auction.status
        }

    winner = best_bid

    auction.status = "Winner Selected"
    auction.winner_bid_id = winner.id
    auction.current_highest_bid = winner.bid_price

    for bid in bids:

        if bid.id == winner.id:
            bid.status = "Accepted"
        else:
            bid.status = "Rejected"

    db.commit()
    db.refresh(auction)

    order = Order(
        product_id=auction.product_id,
        buyer_id=winner.bidder_id,
        quantity=winner.quantity,
        status="Pending"
    )

    db.add(order)

    db.commit()
    db.refresh(order)

    return {
        "auction_id": auction.id,
        "winner_bidder_id": winner.bidder_id,
        "winning_bid": winner.bid_price,
        "winning_quantity": winner.quantity,
        "ai_score": round(best_score, 2),
        "reason": (
            "Selected based on bid price, "
            "reliability, and distance"
        ),
        "order_id": order.id,
        "order_status": order.status,
        "transporter_assigned": False,
        "auction_status": auction.status
    }