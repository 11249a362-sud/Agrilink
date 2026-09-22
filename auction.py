from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from app.services.stock_reallocation import reallocate_unsold_stock
from app.ai.allocation_engine import allocate_stock
from app.ai.auction_ai import select_winner
from app.database.database import get_db
from app.models.auction import Auction
from app.models.bid import Bid
from app.models.product import Product
from app.models.user import User
from app.schemas.auction_schema import (
    BidCreate,
    AuctionWinnerResponse,
)
from app.services.auction_details import get_live_auction_details
from app.services.auction_scheduler import close_expired_auctions
from app.services.websocket_manager import manager
from app.utils.dependencies import (
    require_farmer,
    get_current_user,
)


router = APIRouter(
    prefix="/auctions",
    tags=["Auctions"],
)


# ----------------------------------------------------
# Industry OR Community Hub Access
# ----------------------------------------------------

def require_industry_or_community(
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["industry", "community_hub"]:
        raise HTTPException(
            status_code=403,
            detail="Industry or Community Hub access required",
        )

    return current_user


# ----------------------------------------------------
# Farmer creates auctions using AI allocation
# ----------------------------------------------------

@router.post("/")
def create_auction(
    product_id: int,
    minimum_price: float,
    duration_hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_farmer),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    if product.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create auctions for your own products",
        )

    # Prevent duplicate open auctions
    existing = (
        db.query(Auction)
        .filter(
            Auction.product_id == product.id,
            Auction.status == "Open",
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="An open auction already exists for this product",
        )

    # AI Allocation
    allocation = allocate_stock(
        db=db,
        crop=product.name,
        quantity=product.quantity,
        location=product.location,
    )

    end_time = datetime.utcnow() + timedelta(
        hours=duration_hours
    )

    # Industry Auction
    industry_auction = Auction(
        product_id=product.id,
        farmer_id=current_user.id,
        crop_name=product.name,
        location=product.location,
        quantity=allocation["industry_quantity"],
        unit=product.unit,
        minimum_price=minimum_price,
        auction_type="industry",
        end_time=end_time,
        status="Open",
    )

    # Community Auction
    community_auction = Auction(
        product_id=product.id,
        farmer_id=current_user.id,
        crop_name=product.name,
        location=product.location,
        quantity=allocation["community_quantity"],
        unit=product.unit,
        minimum_price=minimum_price,
        auction_type="community",
        end_time=end_time,
        status="Open",
    )

    db.add(industry_auction)
    db.add(community_auction)
    db.commit()

    db.refresh(industry_auction)
    db.refresh(community_auction)

    return {
        "message": "AI allocation completed",
        "allocation": allocation,
        "industry_auction": {
            "auction_id": industry_auction.id,
            "quantity": industry_auction.quantity,
        },
        "community_auction": {
            "auction_id": community_auction.id,
            "quantity": community_auction.quantity,
        },
    }


# ----------------------------------------------------
# Live Auction Dashboard
# ----------------------------------------------------

@router.get("/live")
def live_auctions(
    db: Session = Depends(get_db),
):
    close_expired_auctions(db)

    auctions = (
        db.query(Auction)
        .filter(Auction.status == "Open")
        .all()
    )

    result = []

    for auction in auctions:
        bids = (
            db.query(Bid)
            .filter(Bid.auction_id == auction.id)
            .count()
        )

        remaining = auction.end_time - datetime.utcnow()

        result.append({
            "auction_id": auction.id,
            "crop": auction.crop_name,
            "location": auction.location,
            "quantity": auction.quantity,
            "unit": auction.unit,
            "auction_type": auction.auction_type,
            "minimum_price": auction.minimum_price,
            "highest_bid": auction.current_highest_bid,
            "time_remaining": str(remaining).split(".")[0],
            "total_bids": bids,
        })

    return result


# ----------------------------------------------------
# View all open auctions
# ----------------------------------------------------

@router.get("/open")
def get_open_auctions(
    db: Session = Depends(get_db),
):
    return (
        db.query(Auction)
        .filter(Auction.status == "Open")
        .all()
    )


# ----------------------------------------------------
# View crop categories
# ----------------------------------------------------

@router.get("/crops")
def get_crop_categories(
    db: Session = Depends(get_db),
):
    crops = (
        db.query(Auction.crop_name)
        .filter(Auction.status == "Open")
        .distinct()
        .all()
    )

    return {
        "crop_categories": [c[0] for c in crops]
    }


# ----------------------------------------------------
# Industry Auctions
# ----------------------------------------------------

@router.get("/industry")
def get_industry_auctions(
    db: Session = Depends(get_db),
):
    return (
        db.query(Auction)
        .filter(
            Auction.status == "Open",
            Auction.auction_type == "industry",
        )
        .all()
    )


# ----------------------------------------------------
# Community Auctions
# ----------------------------------------------------

@router.get("/community")
def get_community_auctions(
    db: Session = Depends(get_db),
):
    return (
        db.query(Auction)
        .filter(
            Auction.status == "Open",
            Auction.auction_type == "community",
        )
        .all()
    )


# ----------------------------------------------------
# View auctions for a crop
# ----------------------------------------------------

@router.get("/crop/{crop_name}")
def get_crop_auctions(
    crop_name: str,
    db: Session = Depends(get_db),
):
    return (
        db.query(Auction)
        .filter(
            Auction.crop_name.ilike(f"%{crop_name}%"),
            Auction.status == "Open",
        )
        .all()
    )


# ----------------------------------------------------
# Place Bid
# ----------------------------------------------------

@router.post("/{auction_id}/bid")
async def place_bid(
    auction_id: int,
    bid: BidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_industry_or_community
    ),
):
    auction = (
        db.query(Auction)
        .filter(
            Auction.id == auction_id,
            Auction.status == "Open",
        )
        .first()
    )

    if not auction:
        raise HTTPException(
            status_code=404,
            detail="Auction not found or closed",
        )

    # Role restriction
    if (
        auction.auction_type == "industry"
        and current_user.role != "industry"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only industries can bid on industry auctions",
        )

    if (
        auction.auction_type == "community"
        and current_user.role != "community_hub"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only community hubs can bid on community auctions",
        )

    if bid.quantity > auction.quantity:
        raise HTTPException(
            status_code=400,
            detail="Bid quantity exceeds available auction quantity",
        )

    if bid.bid_price < auction.minimum_price:
        raise HTTPException(
            status_code=400,
            detail="Bid is below minimum price",
        )

    if bid.bid_price <= auction.current_highest_bid:
        raise HTTPException(
            status_code=400,
            detail="Bid must be higher than current highest bid",
        )

    new_bid = Bid(
        auction_id=auction.id,
        bidder_id=current_user.id,
        bid_price=bid.bid_price,
        quantity=bid.quantity,
    )

    auction.current_highest_bid = bid.bid_price

    db.add(new_bid)
    db.commit()
    db.refresh(new_bid)

    # Real-time broadcast
    await manager.broadcast(
        auction.id,
        {
            "auction_id": auction.id,
            "auction_type": auction.auction_type,
            "highest_bid": auction.current_highest_bid,
            "bidder_id": current_user.id,
            "bid_price": new_bid.bid_price,
            "quantity": new_bid.quantity,
        },
    )

    return new_bid


# ----------------------------------------------------
# AI selects winner
# ----------------------------------------------------

@router.post("/{auction_id}/select-winner")
def select_auction_winner(
    auction_id: int,
    db: Session = Depends(get_db),
):
    result = select_winner(db, auction_id)

    auction = (
        db.query(Auction)
        .filter(Auction.id == auction_id)
        .first()
    )

    if auction:
        auction.status = "Closed"
        db.commit()

        reallocation = reallocate_unsold_stock(
            db,
            auction,
        )

        result["reallocation"] = reallocation

    return result


# ----------------------------------------------------
# Close expired auctions
# ----------------------------------------------------

@router.post("/close-expired")
def close_expired(
    db: Session = Depends(get_db),
):
    return close_expired_auctions(db)


# ----------------------------------------------------
# Live auction details
# ----------------------------------------------------

@router.get("/{auction_id}/live")
def auction_live_details(
    auction_id: int,
    db: Session = Depends(get_db),
):
    return get_live_auction_details(
        db,
        auction_id,
    )


# ----------------------------------------------------
# WebSocket for live bidding
# ----------------------------------------------------

@router.websocket("/ws/{auction_id}")
async def auction_websocket(
    websocket: WebSocket,
    auction_id: int,
):
    await manager.connect(
        auction_id,
        websocket,
    )

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(
            auction_id,
            websocket,
        )


# ----------------------------------------------------
# Get auction winner
# ----------------------------------------------------

@router.get(
    "/{auction_id}/winner",
    response_model=AuctionWinnerResponse,
)
def get_auction_winner(
    auction_id: int,
    db: Session = Depends(get_db),
):
    auction = (
        db.query(Auction)
        .filter(Auction.id == auction_id)
        .first()
    )

    if not auction:
        raise HTTPException(
            status_code=404,
            detail="Auction not found",
        )

    if auction.winner_bid_id is None:
        raise HTTPException(
            status_code=404,
            detail="No winning bid found for this auction",
        )

    winning_bid = (
        db.query(Bid)
        .filter(
            Bid.id == auction.winner_bid_id,
            Bid.auction_id == auction_id,
        )
        .first()
    )

    if not winning_bid:
        raise HTTPException(
            status_code=404,
            detail="Winning bid not found",
        )

    return {
        "auction_id": auction.id,
        "winner_bid_id": winning_bid.id,
        "winner_bidder_id": winning_bid.bidder_id,
        "winning_bid": winning_bid.bid_price,
        "winning_quantity": winning_bid.quantity,
    }


# ----------------------------------------------------
# View single auction
# ----------------------------------------------------

@router.get("/{auction_id}")
def get_auction(
    auction_id: int,
    db: Session = Depends(get_db),
):
    auction = (
        db.query(Auction)
        .filter(Auction.id == auction_id)
        .first()
    )

    if not auction:
        raise HTTPException(
            status_code=404,
            detail="Auction not found",
        )

    return auction