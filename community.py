from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.community_demand import CommunityDemand
from app.models.user import User
from app.utils.dependencies import require_community_hub

router = APIRouter(
    prefix="/community",
    tags=["Community Hub"]
)


@router.post("/request")
def create_bulk_request(
    crop_name: str,
    quantity: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_community_hub)
):
    demand = CommunityDemand(
        community_hub_id=current_user.id,
        crop_name=crop_name,
        quantity=quantity,
        location=current_user.address
    )

    db.add(demand)
    db.commit()
    db.refresh(demand)

    return demand


@router.get("/requests")
def my_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_community_hub)
):
    return (
        db.query(CommunityDemand)
        .filter(
            CommunityDemand.community_hub_id == current_user.id
        )
        .all()
    )