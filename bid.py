from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from datetime import datetime
from app.database.database import Base


class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)

    auction_id = Column(Integer, ForeignKey("auctions.id"))

    # Can be Industry or Community Hub
    bidder_id = Column(Integer, ForeignKey("users.id"))

    bid_price = Column(Float)

    quantity = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)