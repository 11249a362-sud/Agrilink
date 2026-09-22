from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    description = Column(String)

    quantity = Column(Float, nullable=False)

    price = Column(Float, nullable=False)

    unit = Column(String, nullable=False)

    # Human-readable pickup location
    location = Column(String, nullable=False)

    # Pickup coordinates
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    ai_demand = Column(String)

    # AI Image Grading
    image_path = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    grade_confidence = Column(Float, nullable=True)
    recommendation = Column(String, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    owner = relationship("User")