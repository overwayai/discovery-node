# app/schemas/product_group.py
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.schemas.category import CategoryResponse


class ProductGroupBase(BaseModel):
    """Base Pydantic model for ProductGroup data"""

    name: str
    description: Optional[str] = None
    url: Optional[str] = Field(None, description="URL to the product group page")
    category: Optional[str] = Field(None, description="Product category string")
    product_group_id: str = Field(
        ..., description="External identifier for the product group"
    )
    varies_by: List[str] = Field(
        ..., description="Dimensions that variants differ by (e.g. color, size)"
    )
    brand_id: UUID = Field(..., description="Brand this product group belongs to")
    urn: str = Field(..., description="CMP product group identifier (URN format)")
    category_id: Optional[UUID] = Field(
        None, description="Category ID for this product group"
    )
    organization_id: UUID = Field(
        ..., description="Organization this product group belongs to"
    )


class ProductGroupCreate(ProductGroupBase):
    """Schema for creating a new ProductGroup"""

    raw_data: Optional[Dict[str, Any]] = Field(
        None, description="Full JSON-LD representation"
    )


class ProductGroupUpdate(BaseModel):
    """Schema for updating a ProductGroup (all fields optional)"""

    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    product_group_id: Optional[str] = None
    varies_by: Optional[List[str]] = None
    brand_id: Optional[UUID] = None
    urn: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    category_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None


class ProductGroupInDB(ProductGroupBase):
    """Schema for ProductGroup as stored in DB (includes DB fields)"""

    id: UUID
    created_at: datetime
    updated_at: datetime
    raw_data: Optional[Dict[str, Any]] = None
    category: Optional[CategoryResponse] = None

    model_config = {"from_attributes": True}


class ProductGroupResponse(ProductGroupInDB):
    """Schema for API responses"""

    pass
