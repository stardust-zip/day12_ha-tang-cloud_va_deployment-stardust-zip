# Deployment Information

## Public URL
https://day12-production.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
$ curl https://day12-production.up.railway.app/health
# Expected: {"status":"ok","uptime_seconds":278.9,"platform":"Railway","timestamp":"2026-04-17T07:32:11.621602+00:00"}
```

### API Test (with authentication)
```bash
$ curl -X POST https://day12-production.up.railway.app/ask \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Expected: {"answer":"..."}
```

### Without API key (should fail)
```bash
$ curl -X POST https://day12-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}
# Expected: 401 or 403 error
```

## Environment Variables Set
- `PORT` (Railway default: 8080)
- `ENVIRONMENT=production`
- `AGENT_API_KEY` (set via Railway dashboard)

## Features Implemented
- [x] Multi-stage Dockerfile (image < 500MB)
- [x] API key authentication
- [x] Rate limiting (10 req/min)
- [x] Cost guard ($10/month)
- [x] Health check endpoint
- [x] Readiness check endpoint
- [x] Graceful shutdown
- [x] Stateless design (Redis)
- [x] No hardcoded secrets

## Deployment Screenshot
![Railway Deployment](screenshots/deployment.png)