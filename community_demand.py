from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime

from app.database.database import Base


class CommunityDemand(Base):
    __tablename__ = "community_demands"

    id = Column(Integer, primary_key=True, index=True)

    community_hub_id = Column(Integer, ForeignKey("users.id"))

    crop_name = Column(String)

    quantity = Column(Float)

    location = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)