from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import traceback

from app.database.database import get_db
from app.models.user import User
from app.schemas.user_schema import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
)
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.get("/")
def auth_home():
    return {
        "message": "Authentication module is working."
    }


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        new_user = User(
            name=user.name,
            email=user.email,
            hashed_password=hash_password(user.password),
            role=user.role,
            phone=user.phone,
            address=user.address
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except HTTPException:
        raise

    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        form_data.password,
        db_user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={
            "sub": db_user.email,
            "id": db_user.id,
            "role": db_user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }