from fastapi import APIRouter, Depends

from app.models.user import User
from app.utils.dependencies import (
    get_current_user,
    require_farmer,
    require_industry
)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "phone": current_user.phone,
        "address": current_user.address,
    }


@router.get("/farmer-dashboard")
def farmer_dashboard(
    current_user: User = Depends(require_farmer)
):
    return {
        "message": f"Welcome Farmer {current_user.name}"
    }


@router.get("/industry-dashboard")
def industry_dashboard(
    current_user: User = Depends(require_industry)
):
    return {
        "message": f"Welcome Industry {current_user.name}"
    }