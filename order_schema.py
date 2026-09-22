from datetime import datetime
from pydantic import BaseModel


class OrderCreate(BaseModel):
    product_id: int
    quantity: int


class AssignTransporterRequest(BaseModel):
    transporter_id: int


class OrderResponse(BaseModel):
    id: int
    product_id: int
    buyer_id: int
    transporter_id: int | None = None
    quantity: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderStatusResponse(BaseModel):
    message: str
    order: OrderResponse