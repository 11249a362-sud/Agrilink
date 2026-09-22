from pydantic import BaseModel
from typing import Optional, Literal


SupplierCategory = Literal[
    "Fertilizer",
    "Seed",
    "Pesticide",
    "Organic",
    "Equipment"
]


class SupplierProductCreate(BaseModel):
    name: str
    description: Optional[str] = None

    category: SupplierCategory = "Fertilizer"

    quantity: float
    price: float
    unit: str = "kg"

    # GPS coordinates from frontend
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SupplierProductResponse(BaseModel):
    id: int

    name: str
    description: Optional[str] = None

    category: str

    quantity: float
    price: float
    unit: str

    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    owner_id: int

    class Config:
        from_attributes = True