"""
Database Schemas for ESL (Electronic Shelf Labels) Management

Each Pydantic model represents a MongoDB collection. Collection name is the lowercase of the class name.

Use these models in your endpoints for validation. The helper functions in database.py
handle connection and basic CRUD helpers.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TobaccoProduct(BaseModel):
    """
    Products available in the tobacconist catalog
    Collection: "tobaccoproduct"
    """
    name: str = Field(..., description="Product name (e.g., Marlboro Gold 20)")
    sku: str = Field(..., description="Internal SKU or code")
    brand: Optional[str] = Field(None, description="Brand name")
    category: Optional[str] = Field("Tabacco", description="Category")
    barcode: Optional[str] = Field(None, description="EAN/UPC barcode")
    price: float = Field(..., ge=0, description="Current price")
    tax_class: Optional[str] = Field("AAMS", description="Tax class / regime")
    esl_id: Optional[str] = Field(None, description="Assigned ESL identifier")
    stock: Optional[int] = Field(0, ge=0, description="Stock quantity")
    active: bool = Field(True, description="Whether the item is active")


class Store(BaseModel):
    """Tobacconist store profile. Collection: "store"""
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = "IT"


class Label(BaseModel):
    """Physical ESL labels. Collection: "label"""
    esl_id: str = Field(..., description="Unique ESL device ID")
    status: Optional[str] = Field("idle", description="idle|assigned|error")
    battery: Optional[int] = Field(None, ge=0, le=100)
    last_sync: Optional[datetime] = None
    product_sku: Optional[str] = Field(None, description="Linked product SKU if assigned")


class PriceUpdate(BaseModel):
    """Scheduled or executed price changes. Collection: "priceupdate"""
    product_sku: str
    old_price: float = Field(..., ge=0)
    new_price: float = Field(..., ge=0)
    scheduled_at: Optional[datetime] = None
    status: str = Field("done", description="pending|done|failed")
    note: Optional[str] = None


# This lightweight schema is used for partial product updates from the UI
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    tax_class: Optional[str] = None
    esl_id: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None


class BulkProducts(BaseModel):
    items: List[TobaccoProduct]
