from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    buyer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    transporter_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    status = Column(
        String,
        default="Pending"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    product = relationship("Product")

    buyer = relationship(
        "User",
        foreign_keys=[buyer_id]
    )

    transporter = relationship(
        "User",
        foreign_keys=[transporter_id]
    )