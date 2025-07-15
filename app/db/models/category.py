# app/db/models/category.py
from sqlalchemy import Column, String, Text, UUID, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from app.db.base import Base
import uuid


class Category(Base):
    """
    Category model representing product or organization categories in CMP.
    """

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Category(id={self.id}, slug='{self.slug}')>"
