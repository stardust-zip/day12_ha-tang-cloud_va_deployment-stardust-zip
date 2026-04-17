# Student Guide - Day 12 Lab

> **Deadline:** 17/4/2026  
> **Max Score:** 100 points

---

## How to Use This Guide

1. **START HERE**: Read [CODE_LAB.md](./CODE_LAB.md) first to understand the concepts
2. **Follow phases in order**: Phase 1 → Phase 2 → Phase 3 → Phase 4
3. **Check off items** as you complete them
4. **Reference** [QUICK_START.md](./QUICK_START.md) for quick testing
5. ** Troubleshooting**: Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) if stuck

---

## Todo List

### Phase 1: Complete Mission Answers (40 points)

**Goal:** Document your learning and findings from exercises

#### Part 1: Localhost vs Production

- [ ] **Exercise 1.1: Identify anti-patterns found**
  
  **How:**
  1. Go to `01-localhost-vs-production/develop/`
  2. Read the code and identify what's wrong
  3. Compare with `01-localhost-vs-production/production/`
  4. List anti-patterns in MISSION_ANSWERS.md

- [ ] **Exercise 1.3: Create comparison table**
  
  **How:**
  1. Study both develop/ and production/ code
  2. Compare these aspects:
     - Config (dev vs prod settings)
     - Logging (debug vs info/error)
     - Error Handling (verbose vs safe)
     - Database (dev DB vs prod DB)
     - Caching (none vs Redis)
     - Scaling (manual vs auto)
  3. Write table explaining why each matters

#### Part 2: Docker

- [ ] **Exercise 2.1: Dockerfile questions**
  
  **How:**
  1. Check files in `02-docker/develop/` and `02-docker/production/`
  2. Answer in MISSION_ANSWERS.md:
     - Base image used
     - Working directory set
     - Dependencies installed
     - Start command

- [ ] **Exercise 2.3: Image size comparison**
  
  **How:**
  1. Run both Dockerfiles:
     ```bash
     cd 02-docker/develop
     docker build -t agent-dev . && docker images agent-dev
     
     cd 02-docker/production  
     docker build -t agent-prod . && docker images agent-prod
     ```
  2. Compare sizes and calculate % difference
  3. Record in MISSION_ANSWERS.md

#### Part 3: Cloud Deployment

- [ ] **Exercise 3.1: Deploy to Railway**
  
  **How:**
  1. Install Railway CLI: `npm install -g @railway/cli`
  2. Login: `railway login`
  3. Init project: `railway init` → select "Create new project"
  4. Deploy from `03-cloud-deployment/railway/`:
     ```bash
     cd 03-cloud-deployment/railway
     railway up
     ```
  5. Get URL: `railway domain`
  6. Take screenshot of deployment dashboard

#### Part 4: API Security

- [ ] **Exercise 4.1-4.3: Test authentication & rate limiting**
  
  **How:**
  1. Go to `04-api-gateway/production/`
  2. Run: `docker-compose up -d`
  3. Test without key (should return 401):
     ```bash
     curl http://localhost:8000/ask -X POST -d '{"user_id":"test","question":"Hi"}'
     ```
  4. Test with key (should return 200):
     ```bash
     curl -H "X-API-Key: your-api-key" http://localhost:8000/ask \
       -X POST -d '{"user_id":"test","question":"Hi"}'
     ```
  5. Test rate limiting (15 requests, should get 429 after 10):
     ```bash
     for i in {1..15}; do curl -H "X-API-Key: your-api-key" \
       http://localhost:8000/ask -X POST -d '{"user_id":"test","question":"test"}'; done
     ```
  6. Copy output to MISSION_ANSWERS.md

- [ ] **Exercise 4.4: Cost guard implementation**
  
  **How:**
  1. Study `cost_guard.py` in `04-api-gateway/production/`
  2. Explain how it limits requests to $10/month
  3. Document approach in MISSION_ANSWERS.md

#### Part 5: Scaling & Reliability

- [ ] **Exercise 5.1-5.5: Implementation notes**
  
  **How:**
  1. Go to `05-scaling-reliability/production/`
  2. Study implementation of:
     - Health check (`/health`)
     - Readiness check (`/ready`)
     - Graceful shutdown
     - Stateless sessions
     - Load balancing
  3. Test each feature
  4. Write notes in MISSION_ANSWERS.md

**Create file:** `MISSION_ANSWERS.md`

---

### Phase 2: Build Full Source Code (60 points)

**Goal:** Build production-ready agent from scratch

#### Step 1: Create app/ directory

**How:**
```bash
mkdir -p app
touch app/__init__.py
```

Create files:
```
app/
├── main.py              # Main application
├── config.py            # Configuration
├── auth.py              # Authentication
├── rate_limiter.py      # Rate limiting
└── cost_guard.py        # Cost protection
```

#### Step 2: Implement core features

**How - API key authentication (auth.py):**
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("AGENT_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True
```

**How - Rate limiting (rate_limiter.py):**
```python
import redis
from datetime import datetime

class RateLimiter:
    def __init__(self, redis_url, limit=10, window=60):
        self.r = redis.from_url(redis_url)
        self.limit = limit
        self.window = window
    
    async def is_allowed(self, user_id: str) -> bool:
        key = f"rate:{user_id}"
        count = self.r.get(key)
        if not count:
            self.r.setex(key, self.window, 1)
            return True
        if int(count) >= self.limit:
            return False
        self.r.incr(key)
        return True
```

**How - Cost guard (cost_guard.py):**
```python
class CostGuard:
    def __init__(self, redis_url, monthly_limit=10.0):
        self.r = redis.from_url(redis_url)
        self.limit = monthly_limit
    
    async def check_limit(self, user_id: str, cost: float) -> bool:
        key = f"cost:{user_id}"
        current = float(self.r.get(key) or 0)
        if current + cost > self.limit:
            return False
        self.r.incrbyfloat(key, cost)
        return True
```

**How - Health endpoints (main.py):**
```python
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/ready")
async def ready():
    # Check Redis connection
    try:
        r.ping()
        return {"status": "ready"}
    except:
        raise HTTPException(status_code=503, detail="Not ready")
```

**How - Graceful shutdown:**
```python
import signal
import sys

def shutdown(sig, frame):
    print("Shutting down gracefully...")
    r.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
```

#### Step 3: Create Docker setup

**How - Multi-stage Dockerfile:**
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/bin/python /usr/local/bin/python
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY app /app/app
COPY requirements.txt .
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**How - docker-compose.yml:**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - AGENT_API_KEY=${AGENT_API_KEY}
      - LOG_LEVEL=info
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**How - .dockerignore:**
```
__pycache__
*.pyc
.env
.git
*.md
```

#### Step 4: Create configuration files

**How - .env.example:**
```
PORT=8000
REDIS_URL=redis://localhost:6379
AGENT_API_KEY=your-secret-key-here
LOG_LEVEL=info
```

**How - railway.toml:**
```toml
[build]
builder = "docker"
buildCommand = "python -m pip install -r requirements.txt"
startCommand = "python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"

[deploy]
numReplicas = 1
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 10
```

---

### Phase 3: Deploy to Cloud

**Goal:** Get live public URL

#### Step 1: Deploy to Railway

**How:**
```bash
# Login to Railway
railway login

# Init project (follow prompts)
railway init

# Set environment variables
railway variables set AGENT_API_KEY=your-secret-key
railway variables set REDIS_URL=redis://...

# Deploy
railway up
```

#### Step 2: Get public URL

**How:**
```bash
railway domain
# Output: https://your-app.railway.app
```

#### Step 3: Create screenshots folder

**How:**
```bash
mkdir screenshots
# Take screenshots of:
# - Dashboard showing deployed service
# - Service running (no errors)
# - Test results (curl commands)
```

#### Step 4: Create DEPLOYMENT.md

**How - Create file with:**
```markdown
# Deployment Information

## Public URL
https://your-app.railway.app

## Platform
Railway

## Test Commands

### Health Check
curl https://your-app.railway.app/health
# Expected: {"status": "ok"}

### API Test (with authentication)
curl -X POST https://your-app.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Dashboard](screenshots/dashboard.png)
- [Running](screenshots/running.png)
- [Test Results](screenshots/test.png)
```

---

### Phase 4: Pre-Submission Verification

**Goal:** Ensure everything works before submit

#### Run self-tests

**How - Test 1: Health check**
```bash
curl https://your-app.railway.app/health
# Expected: {"status": "ok"}
```

**How - Test 2: Auth required (no key)**
```bash
curl https://your-app.railway.app/ask
# Expected: 401 Unauthorized
```

**How - Test 3: With API key**
```bash
curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
  -X POST -d '{"user_id":"test","question":"Hello"}'
# Expected: 200 OK
```

**How - Test 4: Rate limiting**
```bash
for i in {1..15}; do 
  curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
    -X POST -d '{"user_id":"test","question":"test"}'; 
done
# Expected: 429 after 10 requests
```

#### Final checklist

**How:**
- [ ] Repository is public (or instructor has access)
- [ ] MISSION_ANSWERS.md completed with all exercises
- [ ] DEPLOYMENT.md has working public URL
- [ ] All source code in app/ directory
- [ ] README.md has clear setup instructions
- [ ] No .env file committed (only .env.example)
- [ ] No hardcoded secrets in code
- [ ] Public URL is accessible and working
- [ ] Screenshots included in screenshots/ folder
- [ ] Repository has clear commit history

---

## Submission

**Submit your GitHub repository URL:**
```
https://github.com/your-username/day12-agent-deployment
```

---

## Quick Tips

1. **Test from different device** - Use your phone to test the URL
2. **Make repo public** - Or add instructor as collaborator
3. **Screenshot everything** - Dashboard, running service, tests
4. **Write clear commits** - "Add auth middleware", not "update"
5. **Test DEPLOYMENT.md commands** - Run them locally first
6. **No secrets** - Never commit .env or API keys
7. **Reference [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** for commands
8. **Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** if errors occur