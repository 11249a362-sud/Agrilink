from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.database import Base

class SupplierOrder(Base):
    __tablename__ = "supplier_orders"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("supplier_products.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    quantity = Column(Float, nullable=False)
    status = Column(String, default="Pending")

    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("SupplierProduct")
    farmer = relationship("User")