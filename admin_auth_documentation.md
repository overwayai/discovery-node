# Admin API Authentication Documentation

## Overview
The Discovery Node admin API uses **Bearer token authentication** with API keys that have specific permissions. Authentication is handled through the `APIKeyAuth` class in `app/core/auth.py`.

## Authentication Flow

### 1. API Key Storage
- API keys are stored in the database with associated organization IDs and permissions
- Keys are validated through the `APIKeyService` class
- Each key is tied to a specific organization for multi-tenant support

### 2. Request Authentication
Admin endpoints require Bearer token authentication:
```
Authorization: Bearer <api-key>
```

### 3. Permission Levels
Three pre-configured authentication levels exist:
- **api_key_auth_read**: Requires `admin:read` permission
- **api_key_auth_write**: Requires `admin:write` permission  
- **api_key_auth_admin**: Requires both `admin:read` and `admin:write` permissions

### 4. Organization Context
Organization context is determined in two ways:

#### For Analytics Endpoints (`/admin/analytics/*`)
- Organization ID comes directly from the authenticated API key
- Each API key is associated with a single organization
- Analytics data is automatically filtered to show only that organization's metrics

#### For Product/Organization Endpoints (`/admin/products/*`, `/admin/organizations/*`)
- Uses the `OrganizationId` dependency from `app/core/dependencies.py`
- Organization determined by (in priority order):
  1. Organization ID set by API key authentication (if present)
  2. X-Organization header (subdomain value)
  3. Subdomain from Host header (e.g., "acme" from "acme.discovery.com")

## Implementation Details

### Authentication Middleware (`app/core/auth.py`)
- Validates Bearer token against database
- Checks required permissions for the endpoint
- Logs authentication attempts and outcomes
- Sets `request.state.organization_id` for downstream use

### Audit Logging
All API key usage is logged including:
- Successful authentications
- Failed authentication attempts
- Permission denials
- IP address, user agent, and request path

### Multi-Tenant Support
- In multi-tenant mode: Organization context is required and enforced
- In single-tenant mode: Falls back to `DEFAULT_ORGANIZATION_ID` from config
- Products and data are strictly isolated by organization

## Security Considerations
1. API keys should be kept secure and rotated regularly
2. All admin endpoints require authentication - no public access
3. Permissions are granular (read vs write) for principle of least privilege
4. All authentication attempts are logged for security auditing