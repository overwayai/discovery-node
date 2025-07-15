# app/db/models/brand.py
from sqlalchemy import Column, String, Text, ForeignKey, UUID, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from app.db.base import Base
import uuid


class Brand(Base):
    """
    Brand model representing a brand in the CMP Brand Registry.
    Based on the CMP Brand Registry specification.
    """

    __tablename__ = "brands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    logo_url = Column(String)
    urn = Column(
        String, unique=True, comment="CMP-specific brand identifier (URN format)"
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    raw_data = Column(JSONB, comment="Full JSON-LD representation of the brand")

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    organization = relationship("Organization", back_populates="brands")
    products = relationship(
        "Product", back_populates="brand", cascade="all, delete-orphan"
    )
    product_groups = relationship(
        "ProductGroup", back_populates="brand", cascade="all, delete-orphan"
    )
    products = relationship("Product", back_populates="brand")

    def __repr__(self):
        return f"<Brand(id={self.id}, name='{self.name}')>"
