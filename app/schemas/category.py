# app/schemas/category.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class CategoryBase(BaseModel):
    """Base Pydantic model for Category data"""
    slug: str = Field(..., description="Unique identifier for the category")
    name: str = Field(..., description="Display name of the category")
    description: Optional[str] = Field(None, description="Optional description of the category")
    parent_id: Optional[UUID] = Field(None, description="Parent category ID for hierarchical categories")

class CategoryCreate(CategoryBase):
    """Schema for creating a new Category"""
    pass

class CategoryUpdate(BaseModel):
    """Schema for updating a Category (all fields optional)"""
    slug: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None

class CategoryInDB(CategoryBase):
    """Schema for Category as stored in DB (includes DB fields)"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

class CategoryResponse(CategoryInDB):
    """Schema for API responses"""
    pass