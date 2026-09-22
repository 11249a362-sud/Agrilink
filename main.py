from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.fertilizer import FertilizerProduct
from app.models.fertilizer_order import FertilizerOrder
# Database
from app.database.database import Base, engine
from app.routers import fertilizer
from app.models.rotten_crop import RottenCropRequest
# Models
from app.models.community_demand import CommunityDemand
from app.models.supplier_product import SupplierProduct
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.supplier_order import SupplierOrder
from app.models.location import Location
from app.models.auction import Auction
from app.models.bid import Bid
from app.routers import rotten_crop
# Routers
from app.routers import auth
from app.routers import users
from app.routers import products
from app.routers import orders
from app.routers import supplier
from app.routers import transporter
from app.routers import auction
from app.routers import community
from app.routers import ai
from app.routers import ai_grade


# Create FastAPI application
app = FastAPI(
    title="AgriLinkAI API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create database tables
Base.metadata.create_all(bind=engine)


# Home
@app.get("/")
def home():
    return {
        "message": "Welcome to AgriLinkAI API"
    }


# Health check
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# Register routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(transporter.router)
app.include_router(supplier.router)
app.include_router(auction.router)
app.include_router(community.router)

# Keep these backend routers for now.
# They should NOT be exposed as user-facing frontend features.
app.include_router(ai.router)
app.include_router(ai_grade.router)
app.include_router(fertilizer.router)
app.include_router(rotten_crop.router)