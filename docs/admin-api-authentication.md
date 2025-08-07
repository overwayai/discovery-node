
  The Discovery Node admin API uses Bearer token authentication with API keys. Here's how it works:

  Authentication Method: Bearer tokens in the Authorization header (Authorization: Bearer <api-key>)

  Permission System:
  - API keys have granular permissions (admin:read, admin:write)
  - Analytics endpoints require admin:read permission
  - Product management endpoints check permissions based on operation

  Organization Context:
  - Each API key is tied to a specific organization
  - Analytics endpoints automatically filter data by the API key's organization
  - Product endpoints determine organization from either the API key, X-Organization header, or
  subdomain

  Security Features:
  - All authentication attempts are logged
  - Failed attempts and permission denials are tracked
  - Strict organization-level data isolation in multi-tenant mode