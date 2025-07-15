import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parents[2].absolute()
sys.path.insert(0, str(project_root))

# Now try importing your application modules
from app.core.config import settings

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import Base from your app
try:
    from app.db.base import Base

    print("Successfully imported Base")
    # Import all models to ensure they're registered with Base.metadata
    from app.db.models import (
        Organization,
        Category,
        Brand,
        ProductGroup,
        Product,
        Offer,
    )

    print("Successfully imported all models")
    print("Base.metadata.tables keys:", list(Base.metadata.tables.keys()))
except ImportError as e:
    print(f"Error importing models: {e}")
    print(f"Python path: {sys.path}")
    raise

# This is the Alembic Config object
config = context.config

# Update sqlalchemy.url value from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
# from logging.config import fileConfig
# fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detects column type changes
            compare_server_default=True,  # Detects default value changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
