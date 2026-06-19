# API Documentation

## Overview

The Self-Healing System provides a REST API for monitoring, querying system state, and accessing metrics. All endpoints use JSON for responses.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently no authentication is required. **This should be addressed before production deployment** - see [Security Recommendations](#security-recommendations).

## Endpoints

### Health & Status

#### GET /api/status
Health check endpoint for Docker and monitoring systems.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

**Status Codes:**
- `200 OK` - System is healthy
- `503 Service Unavailable` - System is degraded

---

#### GET /health
Kubernetes/Docker health probe endpoint. Used by Docker HEALTHCHECK.

**Response:**
```json
{"status": "ok"}
```

**HTTP Status:**
- `200` - Healthy
- `503` - Unhealthy

---

### System State

#### GET /api/state
Get current system state in the self-healing lifecycle.

**Response:**
```json
{
  "state": "NORMAL",
  "timestamp": "2026-04-23T18:13:40Z",
  "description": "System operating normally"
}
```

**Possible States:**
- `NORMAL` - Baseline operation, no anomalies detected
- `DEGRADED` - Anomalies detected, evaluating severity
- `HEALING` - Recovery action in progress
- `RECOVERED` - System recovered from anomaly
- `UNKNOWN` - Initial state or error condition

---

### Metrics

#### GET /metrics
Prometheus metrics endpoint. Used by Prometheus scraper.

**Response:** Plain text Prometheus format
```
# HELP anomalies_total Total number of anomalies detected
# TYPE anomalies_total counter
anomalies_total 42

# HELP healings_total Total number of healing actions executed
# TYPE healings_total counter
healings_total 12

# HELP system_state Current system state (0=NORMAL, 1=DEGRADED, 2=HEALING, 3=RECOVERED)
# TYPE system_state gauge
system_state 0
```

**Content-Type:** `text/plain; version=0.0.4`

---

### Events & History

#### GET /api/events
Retrieve historical events from the database.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum events to return (1-10000) |
| `offset` | integer | 0 | Skip first N events |
| `event_type` | string | (all) | Filter by type: ANOMALY, HEALING, NORMAL |
| `fault_type` | string | (all) | Filter by fault: HIGH_CPU, HIGH_MEMORY, HIGH_DISK_IO, HIGH_LATENCY |

**Example Requests:**
```bash
# Get last 50 events
GET /api/events?limit=50

# Get healing events only
GET /api/events?event_type=HEALING

# Get high CPU events with pagination
GET /api/events?fault_type=HIGH_CPU&limit=20&offset=40
```

**Response:**
```json
{
  "events": [
    {
      "id": 1,
      "event_type": "ANOMALY",
      "fault_type": "HIGH_CPU",
      "confidence": 0.95,
      "timestamp": "2026-04-23T18:10:30Z"
    },
    {
      "id": 2,
      "event_type": "HEALING",
      "fault_type": "HIGH_CPU",
      "confidence": 0.95,
      "timestamp": "2026-04-23T18:10:32Z"
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

**HTTP Status Codes:**
- `200 OK` - Events retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `500 Internal Server Error` - Database error

---

#### GET /api/events/{event_id}
Get a specific event by ID.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | integer | Event ID |

**Response:**
```json
{
  "id": 1,
  "event_type": "ANOMALY",
  "fault_type": "HIGH_CPU",
  "confidence": 0.95,
  "timestamp": "2026-04-23T18:10:30Z"
}
```

**HTTP Status Codes:**
- `200 OK` - Event found
- `404 Not Found` - Event does not exist

---

### Statistics

#### GET /api/stats
Get aggregate statistics.

**Response:**
```json
{
  "total_anomalies": 42,
  "total_healings": 12,
  "fault_distribution": {
    "HIGH_CPU": 20,
    "HIGH_MEMORY": 15,
    "HIGH_DISK_IO": 5,
    "HIGH_LATENCY": 2
  },
  "avg_confidence": 0.82,
  "last_anomaly": "2026-04-23T18:10:30Z",
  "last_healing": "2026-04-23T18:10:32Z",
  "uptime_seconds": 3600
}
```

---

### System Information

#### GET /api/version
Get application version and component information.

**Response:**
```json
{
  "app_version": "1.0.0",
  "python_version": "3.12.1",
  "flask_version": "3.1.2",
  "scikit_learn_version": "1.8.0",
  "build_date": "2026-04-23",
  "git_commit": "a1b2c3d4"
}
```

---

#### GET /api/config
Get non-sensitive configuration information.

**Response:**
```json
{
  "window_size": 5,
  "min_anomalies": 3,
  "confidence_threshold": 0.6,
  "healing_cooldown_seconds": 60,
  "max_db_events": 10000,
  "prometheus_scrape_interval": 5,
  "email_alerts_enabled": true
}
```

**Note:** Sensitive values (passwords, email addresses) are not included.

---

## Error Responses

All error responses follow a consistent format:

```json
{
  "error": "Bad Request",
  "message": "Invalid limit parameter",
  "status": 400,
  "timestamp": "2026-04-23T18:13:40Z"
}
```

### Common Error Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `400` | Bad Request | Invalid query parameters, missing required fields |
| `404` | Not Found | Resource doesn't exist |
| `429` | Too Many Requests | Rate limit exceeded (60/minute) |
| `500` | Internal Server Error | Database errors, ML model issues |
| `503` | Service Unavailable | System degraded, critical component down |

---

## Rate Limiting

All endpoints are rate limited to **60 requests per minute** per IP address.

**Rate limit headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1682265600
```

If limit is exceeded:
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Remaining: 0
Retry-After: 45
```

---

## Response Formats

### Timestamps

All timestamps are in **ISO 8601 UTC format**:
```
2026-04-23T18:13:40Z
```

### Numeric Precision

- **Confidence scores**: 0.0 to 1.0 (4 decimal places)
- **CPU/Memory percentages**: 0 to 100
- **Latency (ms)**: Positive decimal
- **Disk I/O (MB/s)**: Positive decimal

---

## Examples

### Python Client
```python
import requests

# Get current system state
response = requests.get("http://localhost:5000/api/state")
print(response.json())

# Get last 10 anomalies
response = requests.get(
    "http://localhost:5000/api/events",
    params={
        "event_type": "ANOMALY",
        "limit": 10
    }
)
events = response.json()["events"]
for event in events:
    print(f"{event['timestamp']}: {event['fault_type']} (confidence: {event['confidence']})")
```

### cURL
```bash
# Health check
curl http://localhost:5000/api/status

# Get current state
curl http://localhost:5000/api/state | jq .

# Get events with filter
curl "http://localhost:5000/api/events?fault_type=HIGH_CPU&limit=20" | jq .

# Get Prometheus metrics
curl http://localhost:5000/metrics
```

### JavaScript/Node.js
```javascript
// Get statistics
fetch('http://localhost:5000/api/stats')
  .then(res => res.json())
  .then(data => {
    console.log(`Total anomalies: ${data.total_anomalies}`);
    console.log(`Total healings: ${data.total_healings}`);
  });
```

---

## Webhooks & Integrations

**Not yet implemented.** Planned features:
- Slack webhook notifications
- PagerDuty incident creation
- Custom webhook triggers
- Email digest summaries

---

## Security Recommendations

### Before Production Deployment

1. **Add API Authentication**
   - Implement JWT tokens or API keys
   - Protect all endpoints except /health
   - Example: `Authorization: Bearer {token}`

2. **Enable HTTPS/TLS**
   - Use self-signed certificates in dev
   - Production: Valid certificates (Let's Encrypt)
   - Configure reverse proxy (nginx, Traefik)

3. **Input Validation**
   - Validate all query parameters
   - Sanitize filter strings
   - Limit pagination (max 10,000 events)

4. **API Gateway**
   - Centralized authentication
   - Rate limiting per user
   - Request logging and monitoring
   - IP whitelisting if needed

5. **Secrets Management**
   - Use environment variables for API keys
   - Rotate credentials regularly
   - Never log sensitive data

---

## Versioning

API version is **v1** (implicit). When backwards-incompatible changes are introduced, endpoints will migrate to `/api/v2/`, etc.

---

## Support

For issues or questions:
- Check application logs: `src/logs/system.log`
- Review Prometheus metrics: http://localhost:9090
- Check Grafana dashboards: http://localhost:3000
