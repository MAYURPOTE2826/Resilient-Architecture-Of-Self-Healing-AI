# Security Guide - Self-Healing Engine

**Document Version:** 2.0  
**Date:** 2026-06-16  
**Status:** Production Ready  

---

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Authentication](#authentication)
3. [Authorization](#authorization)
4. [Input Validation](#input-validation)
5. [Secret Management](#secret-management)
6. [API Security](#api-security)
7. [Network Security](#network-security)
8. [Data Protection](#data-protection)
9. [Incident Response](#incident-response)
10. [Security Checklist](#security-checklist)

---

## Security Architecture

### Defense in Depth

The Self-Healing Engine implements multiple layers of security:

```
┌─────────────────────────────────────────────────────────┐
│ 1. Network Layer (TLS, VPN, Firewall)                  │
├─────────────────────────────────────────────────────────┤
│ 2. API Gateway Layer (Rate Limiting, WAF)               │
├─────────────────────────────────────────────────────────┤
│ 3. Authentication Layer (JWT, API Keys)                 │
├─────────────────────────────────────────────────────────┤
│ 4. Authorization Layer (RBAC, Permissions)              │
├─────────────────────────────────────────────────────────┤
│ 5. Validation Layer (Input, Output)                     │
├─────────────────────────────────────────────────────────┤
│ 6. Data Layer (Encryption, Access Control)              │
├─────────────────────────────────────────────────────────┤
│ 7. Audit Layer (Logging, Monitoring)                    │
└─────────────────────────────────────────────────────────┘
```

### Security Modules

- `security_utils.py` - Password hashing, API key generation, input validation
- `token_manager.py` - JWT token blacklist, API key storage, key rotation
- `error_handler.py` - Secure error responses, request tracking
- `audit_logging.py` - Security event logging, compliance tracking
- `health_checks.py` - Health and readiness probes
- `shutdown_manager.py` - Graceful shutdown with cleanup

---

## Authentication

### JWT Tokens

All API endpoints require either a JWT token or API key.

#### Token Types

- **Access Token** - Short-lived (30 minutes default), used for API requests
- **Refresh Token** - Long-lived (7 days default), used to get new access tokens

#### Token Claims

```json
{
  "sub": "username",          // Subject (user)
  "role": "admin",            // User role
  "exp": 1234567890,          // Expiration time
  "iat": 1234567800,          // Issued at time
  "type": "access"            // Token type (access|refresh)
}
```

#### Token Lifecycle

```
1. User logs in with username/password
2. Server validates credentials
3. Server returns access_token + refresh_token
4. Client uses access_token in Authorization header
5. When access_token expires:
   - Client uses refresh_token to get new access_token
   - Server validates refresh_token
   - Server returns new access_token
6. User logs out or refresh_token expires
   - Token is added to blacklist
   - Server rejects token
```

#### Token Blacklist

Revoked tokens are stored in an in-memory blacklist (Redis in production):

```python
# Revoke token on logout
revoke_token(token, reason="logout")

# Check if token is blacklisted
if is_token_blacklisted(token):
    return "Token revoked"
```

### API Keys

API keys are used for automated/system access.

#### API Key Format

- Prefix: `sk_`
- Length: 32+ bytes (base64 encoded)
- Example: `sk_qpxw7mY9Hj2kL8vB5tRz0nF3aD6sE9cG`

#### API Key Storage

- Keys are never stored in plaintext
- Only SHA-256 hashes are stored
- Keys must be rotated every 90 days

#### API Key Usage

```bash
curl -X GET https://api.example.com/api/metrics \
  -H "X-API-Key: sk_qpxw7mY9Hj2kL8vB5tRz0nF3aD6sE9cG"
```

#### API Key Rotation

```python
# Rotate key
store.rotate_key(old_key_id, new_key_id, new_key_hash)

# Old key remains valid for 30 days (grace period)
# Then it's automatically revoked
```

---

## Authorization

### Role-Based Access Control (RBAC)

Currently, two roles are supported:

- **admin** - Full access to all endpoints
- **user** - Limited access (defined per endpoint)

### Permission Checks

```python
@app.route("/api/admin/users")
@require_jwt
@require_role("admin")
def get_users():
    return jsonify(users)
```

### Future Extensions

- Fine-grained permissions (e.g., `read:metrics`, `write:config`)
- Resource-level authorization
- Attribute-based access control (ABAC)

---

## Input Validation

### Request Validation

All API requests are validated using Pydantic schemas:

```python
from schemas import LoginRequest

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Invalid username format')
        return v
```

### Validation Rules

- All string inputs are truncated to max length
- Email addresses are validated against RFC 5322
- URLs are validated for proper format
- JSON payloads are parsed and validated
- Invalid requests return 422 (Unprocessable Entity)

### Sanitization

Input sanitization prevents XSS and injection attacks:

```python
from security_utils import InputValidator

# Sanitize HTML input
clean_html = InputValidator.sanitize_html(user_input)

# Remove null bytes
clean_string = InputValidator.sanitize_string(user_input)

# Validate password strength
is_valid, error = InputValidator.validate_password_strength(password)
```

---

## Secret Management

### Environment Variables

All secrets are stored in `.env` file (never committed to git):

```bash
# Required in production
SECRET_KEY=<64+ char hex string>
JWT_SECRET=<64+ char hex string>
ADMIN_API_KEY=<32+ char base64 string>
ADMIN_PASSWORD=<strong password>

# Optional
DATABASE_URL=postgres://user:pass@host/db
SENDER_EMAIL=noreply@example.com
SENDER_PASSWORD=<app specific password>
```

### Secret Validation

Production deployment fails if:

- `SECRET_KEY` is less than 32 characters
- `JWT_SECRET` is less than 32 characters
- `ADMIN_PASSWORD` is a weak default value
- Required secrets are missing

### Secret Rotation

```bash
# 1. Generate new secret
python -c "import secrets; print(secrets.token_hex(32))"

# 2. Update .env file
# 3. Restart service (blue-green deployment)
# 4. Verify new secret is active
# 5. Decommission old secret after grace period
```

### Password Management

Passwords are hashed using bcrypt:

```python
from security_utils import PasswordManager

# Hash password (never store plaintext)
hashed = PasswordManager.hash_password(password)

# Verify password
if PasswordManager.verify_password(password, hashed):
    # Password is correct
    pass
```

---

## API Security

### Security Headers

All responses include security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### Rate Limiting

Global rate limit: 100 requests per minute per IP.

Per-endpoint overrides:

```python
@limiter.limit("10 per minute")
def sensitive_endpoint():
    pass
```

### CORS Policy

CORS is restricted to specific origins:

```python
CORS_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com"
]
```

**Never use wildcard (`*`) in production.**

### Request Validation

All requests are validated:

- Content-Type must be `application/json`
- Content-Length is limited (default 10MB)
- Request size > limit returns 413 (Payload Too Large)

### Response Validation

Responses are validated to prevent information leakage:

```python
# ❌ Don't expose internal details
return jsonify({
    "error": "Database connection failed",
    "query": "SELECT ...",
    "traceback": "..."
})

# ✅ Return generic error
return jsonify({
    "error": "An internal error occurred",
    "request_id": "req_abc123"
})
```

---

## Network Security

### TLS/SSL

All production traffic must use HTTPS/TLS 1.3:

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# In production, use certificates from trusted CAs
```

### Firewall Rules

```
Inbound:
  - Port 443 (HTTPS)  - All traffic
  - Port 80 (HTTP)    - Redirect to HTTPS only
  - Port 9090 (Prom)  - Trusted networks only
  - Port 3000 (Grafana) - Trusted networks only

Outbound:
  - Port 5432 (PostgreSQL) - Database servers
  - Port 587 (SMTP)   - Email servers
```

### Network Segmentation

```
Public Subnet:
  - Load Balancer
  - API Gateway

Private Subnet:
  - Application Servers
  - Database Servers
  - Cache Layer

Monitoring Subnet:
  - Prometheus
  - Grafana
  - Loki
```

---

## Data Protection

### Encryption at Rest

- Database: Use encrypted storage backends
- Files: Encrypt sensitive data with AES-256
- Backups: Encrypt with separate key

### Encryption in Transit

- All communication: HTTPS/TLS 1.3
- Client → Server: TLS
- Server → Database: TLS
- Server → External Services: TLS

### Data Retention

- Audit logs: 1 year minimum (adjustable)
- Application logs: 30 days minimum
- User data: Per GDPR/retention policies
- Backups: Keep for 7+ years (compliance)

### PII Handling

- Never log passwords or API keys
- Mask PII in logs (use `***` for sensitive fields)
- Encrypt PII in database
- Minimize PII collection

Example:

```python
# ❌ Don't do this
logger.info("Login", username=username, password=password)

# ✅ Do this
logger.info("Login", username=username, ip_address=ip)
```

---

## Incident Response

### Security Incident Process

1. **Detection**
   - Monitoring alerts fire
   - Anomaly detector identifies issues
   - Manual report received

2. **Assessment**
   - Gather logs and evidence
   - Determine scope and impact
   - Classify severity

3. **Containment**
   - Isolate affected systems
   - Revoke compromised tokens/keys
   - Scale down if under attack

4. **Eradication**
   - Fix the root cause
   - Patch vulnerabilities
   - Remove malicious code

5. **Recovery**
   - Restore from clean backups
   - Verify system integrity
   - Restore to production

6. **Post-Incident**
   - Conduct root cause analysis
   - Implement preventive measures
   - Update security policies

### Incident Response Team

- **Incident Commander**: Coordinates response
- **Security Lead**: Investigates security aspects
- **Operations Lead**: Manages system changes
- **Communications Lead**: Notifies stakeholders

### Communication Plan

- **Stakeholders**: Email within 1 hour
- **Customers**: Status page within 4 hours
- **Authorities**: Per regulatory requirements

### Key Contacts

```
Security Hotline: security@example.com
On-Call: +1-XXX-XXX-XXXX
Incident Response: incident@example.com
```

---

## Security Checklist

### Pre-Deployment

- [ ] All secrets are strong (32+ characters)
- [ ] No hardcoded secrets in code
- [ ] Database is encrypted
- [ ] TLS certificates are valid
- [ ] Firewall rules are configured
- [ ] Security headers are enabled
- [ ] Rate limiting is configured
- [ ] CORS origins are whitelisted

### Ongoing

- [ ] Security patches are applied
- [ ] Audit logs are monitored
- [ ] API keys are rotated (90-day cycle)
- [ ] Certificates are renewed
- [ ] Access is reviewed quarterly
- [ ] Penetration testing is performed
- [ ] Security training is current
- [ ] Incident response plan is tested

### Post-Incident

- [ ] Root cause analysis completed
- [ ] Fixes are deployed
- [ ] All systems verified secure
- [ ] Team debriefing completed
- [ ] Documentation updated
- [ ] Preventive measures implemented
- [ ] Stakeholders notified

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [GDPR Compliance](https://gdpr-info.eu/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## Security Contacts

- **Report Security Issues**: security@example.com
- **Security Lead**: [Contact Information]
- **On-Call**: [Phone/Pager]

---

**Last Updated:** 2026-06-16  
**Next Review:** 2026-09-16  
**Classification:** Internal Use
