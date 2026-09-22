from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    ForeignKey,
    DateTime
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class FertilizerOrder(Base):
    __tablename__ = "fertilizer_orders"

    id = Column(Integer, primary_key=True, index=True)

    fertilizer_id = Column(
        Integer,
        ForeignKey("fertilizer_products.id"),
        nullable=False
    )

    farmer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    quantity = Column(Float, nullable=False)

    status = Column(
        String,
        default="Pending"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    fertilizer = relationship("FertilizerProduct")

    farmer = relationship(
        "User",
        foreign_keys=[farmer_id]
    )