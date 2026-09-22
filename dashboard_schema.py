from pydantic import BaseModel

class DashboardResponse(BaseModel):
    total_products: int
    total_orders: int
    pending_orders: int
    accepted_orders: int
    completed_orders: int
    average_ai_price: float
    top_crop: str