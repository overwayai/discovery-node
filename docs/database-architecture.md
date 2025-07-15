# Database Architecture Guide

This document outlines the responsibilities, patterns, and best practices for the database-related components in the discovery-node project.

## 📁 Directory Structure

```
app/
├── db/
│   ├── models/          # SQLAlchemy ORM models
│   ├── repositories/    # Data access layer
│   └── base.py         # Database configuration
├── schemas/             # Pydantic schemas
└── services/           # Business logic layer
```

## 🏗️ Architecture Overview

The database layer follows a **layered architecture** pattern:

```
┌─────────────────┐
│   API Routes    │  ← HTTP endpoints
├─────────────────┤
│   Services      │  ← Business logic
├─────────────────┤
│   Repositories  │  ← Data access
├─────────────────┤
│   Models        │  ← Database schema
├─────────────────┤
│   Database      │  ← PostgreSQL
└─────────────────┘
```

## 📊 Database Models (`app/db/models/`)

### Responsibilities

Database models define the **database schema** and **relationships** between entities.

#### ✅ Do's

- **Define clear table structure** with appropriate column types
- **Use meaningful table and column names** following SQL conventions
- **Define relationships** using SQLAlchemy relationship() decorators
- **Add indexes** for frequently queried columns
- **Include timestamps** (created_at, updated_at) for audit trails
- **Use UUIDs** for primary keys to avoid sequential ID issues
- **Add comments** to document complex fields
- **Handle JSONB fields** for flexible data storage

#### ❌ Don'ts

- **Don't put business logic** in models
- **Don't add validation logic** (use Pydantic schemas instead)
- **Don't hardcode values** in models
- **Don't create circular imports** between models
- **Don't use string IDs** for primary keys

#### Example: Product Model

```python
class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    urn = Column(String, unique=True, nullable=False, comment="CMP-specific product identifier")
    name = Column(String, nullable=False, index=True)
    
    # Relationships
    product_group = relationship("ProductGroup", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
```

## 🔄 Repositories (`app/db/repositories/`)

### Responsibilities

Repositories handle **data access operations** and provide a clean interface for database queries.

#### ✅ Do's

- **Implement CRUD operations** (Create, Read, Update, Delete)
- **Use type hints** for all method parameters and return values
- **Handle database sessions** properly
- **Implement pagination** for list operations
- **Add search functionality** with flexible filters
- **Use eager loading** (selectinload) for related data
- **Handle bulk operations** efficiently
- **Add proper error handling** for database operations

#### ❌ Don'ts

- **Don't put business logic** in repositories
- **Don't expose raw SQL** to services
- **Don't handle transactions** (let services manage transactions)
- **Don't cache data** in repositories
- **Don't validate data** (use Pydantic schemas)

#### Example: Product Repository

```python
class ProductRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        return self.db_session.query(Product).filter(Product.id == product_id).first()
    
    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Product]:
        search_term = f"%{query}%"
        return (
            self.db_session.query(Product)
            .filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
```

## 📋 Schemas (`app/schemas/`)

### Responsibilities

Pydantic schemas define **data validation**, **serialization**, and **API contracts**.

#### ✅ Do's

- **Create separate schemas** for different operations (Create, Update, Response)
- **Use descriptive field names** and add field descriptions
- **Implement proper validation** with Pydantic validators
- **Handle optional fields** appropriately
- **Use aliases** for JSON-LD compatibility
- **Add examples** in schema documentation
- **Implement custom serializers** for complex data types
- **Use inheritance** to avoid code duplication

#### ❌ Don'ts

- **Don't mix database models** with Pydantic schemas
- **Don't put business logic** in schemas
- **Don't expose internal fields** in response schemas
- **Don't use raw dictionaries** instead of proper schemas
- **Don't skip validation** for performance reasons

#### Example: Product Schemas

```python
class ProductBase(BaseModel):
    name: str
    urn: str = Field(..., description="CMP product identifier")
    brand_id: UUID = Field(..., description="Brand this product belongs to")

class ProductCreate(ProductBase):
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Full JSON-LD representation")
    offers: Optional[OfferBase] = Field(None, description="Offer information")

class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None
    offers: List[OfferResponse] = []
    
    model_config = {"from_attributes": True}
```

## 🎯 Services (`app/services/`)

### Responsibilities

Services contain **business logic** and orchestrate operations between repositories.

#### ✅ Do's

- **Implement business rules** and validation logic
- **Coordinate between multiple repositories** when needed
- **Handle transactions** and rollbacks
- **Implement caching** strategies
- **Add logging** for important operations
- **Handle errors** gracefully with proper error messages
- **Validate business constraints** before database operations
- **Use dependency injection** for repositories

#### ❌ Don'ts

- **Don't put data access logic** in services (use repositories)
- **Don't expose database models** directly to API layer
- **Don't handle HTTP concerns** (let API routes handle that)
- **Don't skip error handling** for database operations
- **Don't create tight coupling** between services

#### Example: Product Service

```python
class ProductService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.product_repo = ProductRepository(db_session)
    
    def create_product(self, product_data: ProductCreate) -> ProductInDB:
        # Business logic validation
        existing = self.product_repo.get_by_urn(product_data.urn)
        if existing:
            logger.warning(f"Product with URN {product_data.urn} already exists")
            raise ValueError("Product URN already exists")
        
        # Create the product
        product = self.product_repo.create(product_data)
        return ProductInDB.model_validate(product)
    
    def process_product(self, product_data: Dict[str, Any], brand_id: UUID) -> UUID:
        # Complex business logic for processing CMP product data
        # Coordinate between multiple repositories
        # Handle validation and error cases
        pass
```

## 🔄 Data Flow Patterns

### 1. Create Operation
```
API Route → Service → Repository → Database
     ↑         ↑         ↑
  Validation  Business  Data Access
```

### 2. Read Operation
```
API Route → Service → Repository → Database
     ↑         ↑         ↑
  Response   Business  Data Access
   Schema     Logic
```

### 3. Update Operation
```
API Route → Service → Repository → Database
     ↑         ↑         ↑
  Validation  Business  Data Access
```

## 🛠️ Best Practices

### 1. Error Handling

```python
# In repositories
def get_by_id(self, product_id: UUID) -> Optional[Product]:
    try:
        return self.db_session.query(Product).filter(Product.id == product_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting product {product_id}: {e}")
        raise

# In services
def get_product(self, product_id: UUID) -> Optional[ProductInDB]:
    try:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None
        return ProductInDB.model_validate(product)
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise
```

### 2. Transaction Management

```python
# In services
def create_product_with_offers(self, product_data: ProductCreate, offers_data: List[OfferCreate]):
    try:
        # Start transaction
        product = self.product_repo.create(product_data)
        
        # Create offers
        for offer_data in offers_data:
            offer_data.product_id = product.id
            self.offer_repo.create(offer_data)
        
        # Commit transaction
        self.db_session.commit()
        return ProductInDB.model_validate(product)
    except Exception as e:
        # Rollback on error
        self.db_session.rollback()
        logger.error(f"Error creating product with offers: {e}")
        raise
```

### 3. Pagination

```python
# In repositories
def list(self, skip: int = 0, limit: int = 100) -> List[Product]:
    return (
        self.db_session.query(Product)
        .offset(skip)
        .limit(limit)
        .all()
    )

# In services
def list_products(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
    skip = (page - 1) * page_size
    products = self.product_repo.list(skip, page_size)
    
    return {
        "items": [ProductInDB.model_validate(p) for p in products],
        "page": page,
        "page_size": page_size,
        "total": self.product_repo.count()
    }
```

### 4. Search and Filtering

```python
# In repositories
def search(self, query: str, filters: Dict[str, Any], skip: int = 0, limit: int = 100):
    search_term = f"%{query}%"
    query = self.db_session.query(Product)
    
    # Add search conditions
    query = query.filter(
        or_(
            Product.name.ilike(search_term),
            Product.description.ilike(search_term)
        )
    )
    
    # Add filters
    if "brand_id" in filters:
        query = query.filter(Product.brand_id == filters["brand_id"])
    if "category_id" in filters:
        query = query.filter(Product.category_id == filters["category_id"])
    
    return query.offset(skip).limit(limit).all()
```

## 🔍 Common Patterns

### 1. Repository Pattern
- **Purpose**: Abstract data access logic
- **Benefits**: Testable, maintainable, database-agnostic
- **Usage**: One repository per model

### 2. Service Layer Pattern
- **Purpose**: Encapsulate business logic
- **Benefits**: Reusable, testable, transaction management
- **Usage**: One service per domain entity

### 3. Schema Pattern
- **Purpose**: Data validation and serialization
- **Benefits**: Type safety, API documentation, validation
- **Usage**: Separate schemas for Create, Update, Response

### 4. Dependency Injection
- **Purpose**: Loose coupling between components
- **Benefits**: Testable, maintainable, flexible
- **Usage**: Inject repositories into services

## 🧪 Testing Guidelines

### 1. Model Testing
- Test relationships and constraints
- Test field validations
- Test database migrations

### 2. Repository Testing
- Test CRUD operations
- Test search and filtering
- Test pagination
- Use test database

### 3. Service Testing
- Test business logic
- Test error handling
- Test transaction management
- Mock repositories for unit tests

### 4. Schema Testing
- Test validation rules
- Test serialization
- Test field constraints

## 📚 Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🔧 Migration Guidelines

### Creating Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "Add product table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Migration Best Practices
- **Test migrations** in development first
- **Backup production data** before applying migrations
- **Use transactions** for data migrations
- **Document breaking changes**
- **Version control** migration files

This architecture ensures a clean separation of concerns, maintainable code, and scalable database operations for the discovery-node project. 