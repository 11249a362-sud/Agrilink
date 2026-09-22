from pydantic import BaseModel
from datetime import datetime


class AuctionCreate(BaseModel):
    product_id: int
    minimum_price: float
    duration_hours: int = 24


class AuctionResponse(BaseModel):
    id: int
    crop_name: str
    location: str
    quantity: float
    unit: str
    minimum_price: float
    current_highest_bid: float
    status: str
    end_time: datetime

    class Config:
        from_attributes = True


class BidCreate(BaseModel):
    bid_price: float
    quantity: float


class BidResponse(BaseModel):
    id: int
    auction_id: int
    industry_id: int
    bid_price: float
    quantity: float

    class Config:
        from_attributes = True


class AuctionWinnerResponse(BaseModel):
    auction_id: int
    winner_bid_id: int
    winner_bidder_id: int
    winning_bid: float
    winning_quantity: float