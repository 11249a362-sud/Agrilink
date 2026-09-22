from pydantic import BaseModel
from datetime import datetime

class SupplierOrderCreate(BaseModel):
    product_id: int
    quantity: float

class SupplierOrderResponse(BaseModel):
    id: int
    product_id: int
    farmer_id: int
    quantity: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True