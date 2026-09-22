from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class FertilizerProduct(Base):
    __tablename__ = "fertilizer_products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    description = Column(String)

    quantity = Column(Float, nullable=False)

    price = Column(Float, nullable=False)

    unit = Column(String, nullable=False)

    location = Column(String, nullable=False)

    supplier_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    supplier = relationship("User")