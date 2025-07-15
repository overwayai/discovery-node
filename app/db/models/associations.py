# app/db/models/associations.py
from sqlalchemy import Table, Column, ForeignKey, UUID
from app.db.base import Base

# Organization to Category many-to-many association
organization_category = Table(
    'organization_category',
    Base.metadata,
    Column('organization_id', UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', UUID(as_uuid=True), ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)
