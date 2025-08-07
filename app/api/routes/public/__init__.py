from .health import health_router
from .organizations import organization_router
from .feed import feed_router

public_routers = [
    ("health", health_router),
    ("organizations", organization_router),
    ("feed",feed_router)
]

__all__ = ["public_routers"]