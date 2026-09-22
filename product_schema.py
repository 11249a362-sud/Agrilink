from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    quantity: float
    unit: str
    location: str

    # Pickup coordinates
    latitude: float | None = None
    longitude: float | None = None


class ProductUpdate(BaseModel):
    name: str
    description: str | None = None
    quantity: float
    unit: str
    location: str

    # Pickup coordinates
    latitude: float | None = None
    longitude: float | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    quantity: float
    price: float
    unit: str
    location: str

    # Pickup coordinates
    latitude: float | None = None
    longitude: float | None = None

    ai_demand: str | None = None

    # AI Image Grading
    image_path: str | None = None
    condition: str | None = None
    grade_confidence: float | None = None
    recommendation: str | None = None

    owner_id: int

    class Config:
        from_attributes = True