from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(String, unique=True, index=True, nullable=False)

    hashed_password = Column(String, nullable=False)

    role = Column(String, nullable=False)

    phone = Column(String)

    address = Column(String)

    # Transporter location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Transporter availability
    availability_status = Column(
        String,
        default="available",
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )