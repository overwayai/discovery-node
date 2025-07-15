# app/schemas/brand.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.schemas.category import CategoryResponse


class BrandBase(BaseModel):
    """Base Pydantic model for Brand data"""

    name: str
    logo_url: Optional[str] = Field(None, description="URL to brand logo")
    urn: Optional[str] = Field(None, description="CMP Brand identifier (URN format)")
    organization_id: UUID = Field(..., description="Organization this brand belongs to")


class BrandCreate(BrandBase):
    """Schema for creating a new Brand"""

    raw_data: Optional[Dict[str, Any]] = Field(
        None, description="Full JSON-LD representation"
    )
    category_ids: Optional[List[UUID]] = Field(None, description="List of category IDs")


class BrandUpdate(BaseModel):
    """Schema for updating a Brand (all fields optional)"""

    name: Optional[str] = None
    logo_url: Optional[str] = None
    urn: Optional[str] = None
    organization_id: Optional[UUID] = None
    raw_data: Optional[Dict[str, Any]] = None
    category_ids: Optional[List[UUID]] = None


class BrandInDB(BrandBase):
    """Schema for Brand as stored in DB (includes DB fields)"""

    id: UUID
    created_at: datetime
    updated_at: datetime
    raw_data: Optional[Dict[str, Any]] = None
    categories: List[CategoryResponse] = []

    model_config = {"from_attributes": True}


class BrandResponse(BrandInDB):
    """Schema for API responses"""

    pass
