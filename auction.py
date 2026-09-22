from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("products.id"))
    farmer_id = Column(Integer, ForeignKey("users.id"))

    crop_name = Column(String)
    location = Column(String)

    quantity = Column(Float)
    unit = Column(String)

    minimum_price = Column(Float)

    current_highest_bid = Column(Float, default=0)

    # Open | Closed | Completed
    status = Column(String, default="Open")

    # industry or community
    auction_type = Column(String, default="industry")

    winner_bid_id = Column(Integer, nullable=True)

    end_time = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)