from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.utils.security import SECRET_KEY, ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None:
        raise credentials_exception

    return user


# ---------------------------------
# Farmer access
# ---------------------------------
def require_farmer(
    current_user: User = Depends(get_current_user)
):
    if str(current_user.role).lower() != "farmer":
        raise HTTPException(
            status_code=403,
            detail="Only farmers can access this endpoint."
        )

    return current_user


# ---------------------------------
# Transporter access
# ---------------------------------
def require_transporter(
    current_user: User = Depends(get_current_user)
):
    if str(current_user.role).lower() != "transporter":
        raise HTTPException(
            status_code=403,
            detail="Only transporters can access this endpoint."
        )

    return current_user


# ---------------------------------
# Industry access
# ---------------------------------
def require_industry(
    current_user: User = Depends(get_current_user)
):
    if str(current_user.role).lower() != "industry":
        raise HTTPException(
            status_code=403,
            detail="Only industries can access this endpoint."
        )

    return current_user


# ---------------------------------
# Supplier access
# ---------------------------------
def require_supplier(
    current_user: User = Depends(get_current_user)
):
    if str(current_user.role).lower() != "supplier":
        raise HTTPException(
            status_code=403,
            detail="Only suppliers can access this endpoint."
        )

    return current_user


# ---------------------------------
# Community Hub access
# ---------------------------------
def require_community_hub(
    current_user: User = Depends(get_current_user)
):
    if str(current_user.role).lower() != "community_hub":
        raise HTTPException(
            status_code=403,
            detail="Community Hub access required"
        )

    return current_user