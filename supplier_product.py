from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class SupplierProduct(Base):
    __tablename__ = "supplier_products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Product category
    category = Column(String, nullable=False, default="Fertilizer")

    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    unit = Column(String, default="kg")

    # Automatically detected location
    location = Column(String, nullable=True)

    # GPS coordinates
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    owner = relationship("User")