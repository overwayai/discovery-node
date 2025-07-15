# app/db/models/product.py
from sqlalchemy import Column, String, Text, ForeignKey, UUID, ARRAY, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from app.db.base import Base
import uuid

class ProductGroup(Base):
    """
    ProductGroup model representing a group of related products (product variants)
    in the CMP Product Feed specification.
    """
    __tablename__ = "product_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    urn = Column(String, unique=True, nullable=False, comment="CMP-specific product group identifier (URN format)")
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    url = Column(String)
    category = Column(String, index=True)
    product_group_id = Column(String, nullable=False, unique=True, comment="External identifier for the product group")
    varies_by = Column(ARRAY(String), nullable=False, comment="Array of variant dimensions (e.g., color, size)")
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    raw_data = Column(JSONB, comment="Full JSON-LD representation of the product group")
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    brand = relationship("Brand", back_populates="product_groups")
    products = relationship("Product", back_populates="product_group", cascade="all, delete-orphan")
    # Removed categories relationship and product_group_category association table references
    category = relationship("Category", backref="product_groups", foreign_keys=[category_id])
    organization = relationship("Organization", back_populates="product_groups")
    
    def __repr__(self):
        return f"<ProductGroup(id={self.id}, name='{self.name}')>"