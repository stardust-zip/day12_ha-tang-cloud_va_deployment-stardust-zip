# Code Lab: Deploy Your AI Agent to Production

> **AICB-P1 · VinUniversity 2026**
> Thời gian: 3-4 giờ | Độ khó: Intermediate

## Mục Tiêu

Sau khi hoàn thành lab này, bạn sẽ:

- Hiểu sự khác biệt giữa development và production
- Containerize một AI agent với Docker
- Deploy agent lên cloud platform
- Bảo mật API với authentication và rate limiting
- Thiết kế hệ thống có khả năng scale và reliable

---

## Yêu Cầu

```bash
 Python 3.11+
 Docker & Docker Compose
 Git
 Text editor (VS Code khuyến nghị)
 Terminal/Command line
```

**Không cần:**

- OpenAI API key (dùng mock LLM)
- Credit card
- Kinh nghiệm DevOps trước đó

---

## Lộ Trình Lab

| Phần       | Thời gian | Nội dung                |
| ---------- | --------- | ----------------------- |
| **Part 1** | 30 phút   | Localhost vs Production |
| **Part 2** | 45 phút   | Docker Containerization |
| **Part 3** | 45 phút   | Cloud Deployment        |
| **Part 4** | 40 phút   | API Security            |
| **Part 5** | 40 phút   | Scaling & Reliability   |
| **Part 6** | 60 phút   | Final Project           |

---

## Part 1: Localhost vs Production (30 phút)

### Concepts

**Vấn đề:** "It works on my machine" — code chạy tốt trên laptop nhưng fail khi deploy.

**Nguyên nhân:**

- Hardcoded secrets
- Khác biệt về environment (Python version, OS, dependencies)
- Không có health checks
- Config không linh hoạt

**Giải pháp:** 12-Factor App principles

### Exercise 1.1: Phát hiện anti-patterns

```bash
cd 01-localhost-vs-production/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm ít nhất 5 vấn đề.

<details>
<summary> Gợi ý</summary>

Tìm:

- API key hardcode
- Port cố định
- Debug mode
- Không có health check
- Không xử lý shutdown

</details>

**Đáp án (5+ vấn đề tìm thấy trong code):**

1. **API key hardcode** — Line 17: `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` → Secret lộ trong code
2. **Database URL hardcode** — Line 18: `DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"` → Credentials lộ
3. **Debug mode** — Line 21: `DEBUG = True` → Không nên bật trong production
4. **Port cố định** — Line 52: `port=8000` → Nên đọc từ env variable `PORT`
5. **Host localhost** — Line 51: `host="localhost"` → Chỉ nhận kết nối local, không từ container
6. **reload=True** — Line 53: `reload=True` → Auto-reload nguy hiểm trong production
7. **Không có health check** — Không có `/health` endpoint, platform không biết khi nào restart
8. **print() logging** — Lines 33-38: Dùng `print()` thay vì structured logging

### Exercise 1.2: Chạy basic version

```bash
cd 01-localhost-vs-production/develop
pip install -r requirements.txt
python app.py
```

Test:

```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**Quan sát:** Nó chạy! Server starts trên localhost, trả về response. **Nhưng có production-ready không?**

**Trả lời:**

- Không — vì có quá nhiều vấn đề (xem Exercise 1.1)
- API key lộ trong logs khi gọi (line 34 log ra key)
- Health check không có → platform không restart được khi crash
- Port/host cố định → không deploy được lên cloud

### Exercise 1.3: So sánh với advanced version

```bash
cd ../production
cp .env.example .env
pip install -r requirements.txt
python app.py
```

**Nhiệm vụ:** So sánh 2 files `app.py`. Điền vào bảng:

| Feature      | Basic    | Advanced             | Tại sao quan trọng?                                                                |
| ------------ | -------- | -------------------- | ---------------------------------------------------------------------------------- |
| Config       | Hardcode | Env vars             | Secrets không bị lộ trong code; cùng code chạy được ở mọi môi trường               |
| Health check | Không có | `/health` + `/ready` | Platform biết khi nào cần restart; load balancer quyết định có route traffic không |
| Logging      | print()  | JSON                 | Dễ parse, search, aggregate trong production monitoring tools (Datadog, Loki...)   |
| Shutdown     | Đột ngột | Graceful (SIGTERM)   | Cho phép in-flight requests hoàn thành trước khi tắt container                     |

### Checkpoint 1

- [x] Hiểu tại sao hardcode secrets là nguy hiểm
- [x] Biết cách dùng environment variables
- [x] Hiểu vai trò của health check endpoint
- [x] Biết graceful shutdown là gì

---

## Part 2: Docker Containerization (45 phút)

### Concepts

**Vấn đề:** "Works on my machine" part 2 — Python version khác, dependencies conflict.

**Giải pháp:** Docker — đóng gói app + dependencies vào container.

**Benefits:**

- Consistent environment
- Dễ deploy
- Isolation
- Reproducible builds

### Exercise 2.1: Dockerfile cơ bản

```bash
cd ../../02-docker/develop
```

**Nhiệm vụ:** Đọc `Dockerfile` và trả lời:

1. **Base image là gì?** — `python:3.11` (full Python distribution, ~1 GB)
2. **Working directory là gì?** — `/app`
3. **Tại sao COPY requirements.txt trước?** — Để leverage Docker layer cache; nếu requirements không đổi, Docker không cần chạy lại `pip install`
4. **CMD vs ENTRYPOINT khác nhau thế nào?** — CMD cung cấp default arguments cho container, có thể override; ENTRYPOINT định đoạt command chính, khó override hơn

### Exercise 2.2: Build và run

```bash
# Build image
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

# Run container
docker run -p 8000:8000 my-agent:develop

# Test
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

**Quan sát:** Image size là bao nhiêu: 1.66GB (DISK USAGE)

```bash
docker images my-agent:develop
```

### Exercise 2.3: Multi-stage build

```bash
cd ../production
```

**Nhiệm vụ:** Đọc `Dockerfile` và tìm:

- Stage 1 làm gì? → **Builder stage**: Cài đặt pip, gcc, libpq-dev + dependencies (cần để compile packages)
- Stage 2 làm gì? → **Runtime stage**: Chỉ copy những gì cần để chạy (Python slim + site-packages + source code)
- Tàì sao image nhỏ hơn? → Dùng `python:3.11-slim` thay vì `python:3.11` đầy đủ, không có build tools, chạy non-root user

Build và so sánh:

```bash
docker build -t my-agent:advanced .
docker images | grep my-agent
```

| Image                             | DISK USAGE | CONTENT SIZE |
| --------------------------------- | ---------- | ------------ |
| `my-agent:develop` (basic)        | 1.66GB     | 424MB        |
| `my-agent:advanced` (multi-stage) | 236MB      | 56.6MB       |

→ **87% smaller** (1.66GB → 236MB)!

### Exercise 2.4: Docker Compose stack

**Nhiệm vụ:** Đọc `docker-compose.yml` và vẽ architecture diagram.

```bash
docker compose up
```

**Services được start:**

| Service  | Image                          | Purpose                                     |
| -------- | ------------------------------ | ------------------------------------------- |
| `nginx`  | nginx:alpine                   | Reverse proxy, load balancer, rate limiting |
| `agent`  | production-agent (multi-stage) | FastAPI AI agent                            |
| `redis`  | redis:7-alpine                 | Session cache, rate limiting                |
| `qdrant` | qdrant/qdrant:v1.9.0           | Vector database (RAG)                       |

**Communication:**

```
Client → Nginx (port 80) → Agent (internal network)
                     → Redis (cache/session)
                     → Qdrant (vector DB)
```

**Architecture diagram:**

```
┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Nginx     │ (LB, rate limit)
└─────────────┘     └──────┬──────┘
                           │
                    ┌────────┼────────┐
                    ▼        ▼        ▼
               ┌──────┐  Agent (scale to N)
               │Redis │  Cache
               └──────┘
               ┌──────┐
               │Qdrant│  Vector DB
               └──────┘
```

**Test:**

```bash
# Health check
curl http://localhost/health
# {"status":"ok","uptime_seconds":5.2,"version":"2.0.0"}

# Agent endpoint
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain microservices"}'
# {"answer":"Agent đang hoạt động tốt! (mock response)"}
```

### Checkpoint 2

- [x] Hiểu cấu trúc Dockerfile
- [x] Biết lợi ích của multi-stage builds
- [x] Hiểu Docker Compose orchestration
- [x] Biết cách debug container (`docker logs`, `docker exec`)

---

## Part 3: Cloud Deployment (45 phút)

### Concepts

**Vấn đề:** Laptop không thể chạy 24/7, không có public IP.

**Giải pháp:** Cloud platforms — Railway, Render, GCP Cloud Run.

**So sánh:**

| Platform  | Độ khó | Free tier   | Best for      |
| --------- | ------ | ----------- | ------------- |
| Railway   | ⭐     | $5 credit   | Prototypes    |
| Render    | ⭐⭐   | 750h/month  | Side projects |
| Cloud Run | ⭐⭐⭐ | 2M requests | Production    |

### Exercise 3.1: Deploy Railway (15 phút)

```bash
cd ../../03-cloud-deployment/railway
```

**Steps:**

1. Install Railway CLI:

```bash
npm i -g @railway/cli
```

2. Login:

```bash
railway login
```

3. Initialize project:

```bash
railway init
```

4. Set environment variables:

```bash
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key
```

5. Deploy:

```bash
railway up
```

6. Get public URL:

```bash
railway domain
```

**Nhiệm vụ:** Test public URL với curl hoặc Postman.

Sau khi deploy thành công, chạy:

```bash
# Lấy domain
 railway domain
 # → day12-production.up.railway.app

# Health check
curl https://day12-production.up.railway.app/health
 # → {"status":"ok","uptime_seconds":278.9,"platform":"Railway",...}

# Agent endpoint (POST /ask)
curl https://day12-production.up.railway.app/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
 # → {"answer":"..."}
```

- Dùng `https://` ( Railway tự cấp SSL)
- PORT trên Railway mặc định là `8080`, không phải `8000`
- Health check path là `/health` (platform dùng để kiểm tra)

### Exercise 3.2: Deploy Render (15 phút)

```bash
cd ../render
```

**Steps:**

1. Push code lên GitHub (nếu chưa có)
2. Vào [render.com](https://render.com) → Sign up
3. New → Blueprint
4. Connect GitHub repo
5. Render tự động đọc `render.yaml`
6. Set environment variables trong dashboard
7. Deploy!

**Nhiệm vụ:** So sánh `render.yaml` với `railway.toml`. Khác nhau gì?

### Exercise 3.3: (Optional) GCP Cloud Run (15 phút)

```bash
cd ../production-cloud-run
```

**Yêu cầu:** GCP account (có free tier).

**Nhiệm vụ:** Đọc `cloudbuild.yaml` và `service.yaml`. Hiểu CI/CD pipeline.

### Checkpoint 3

- [x] Deploy thành công lên ít nhất 1 platform
- [x] Có public URL hoạt động
- [x] Hiểu cách set environment variables trên cloud
- [x] Biết cách xem logs

---

## Part 4: API Security (40 phút)

### Concepts

**Vấn đề:** Public URL = ai cũng gọi được = hết tiền OpenAI.

**Giải pháp:**

1. **Authentication** — Chỉ user hợp lệ mới gọi được
2. **Rate Limiting** — Giới hạn số request/phút
3. **Cost Guard** — Dừng khi vượt budget

### Exercise 4.1: API Key authentication

```bash
cd ../../04-api-gateway/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm:

- **API key được check ở đâu?** → Hàm `verify_api_key()` (lines 39-54)
- **Điều gì xảy ra nếu sai key?** → HTTP 403 Forbidden ("Invalid API key")
- **Làm sao rotate key?** → Đổi `AGENT_API_KEY` environment variable

**Trả lời:**

- API key được check trong dependency `verify_api_key()` sử dụng `APIKeyHeader`
- Nếu không có key: HTTP 401 "Missing API key"
- Nếu sai key: HTTP 403 "Invalid API key"
- Rotate: thay đổi `AGENT_API_KEY` env var

Test:

```bash
cd ../../04-api-gateway/develop
AGENT_API_KEY=secret-key-123 uvicorn app:app --host 0.0.0.0 --port 8000

#  Không có key → 401
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
 # {"detail":"Missing API key..."}

#  Có key → 200
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
 # {"question":"Hello","answer":"..."}
```

### Exercise 4.2: JWT authentication (Advanced)

```bash
cd ../production
```

**Nhiệm vụ:**

1. Đọc `auth.py` — hiểu JWT flow
2. Lấy token:

```bash
cd ../../04-api-gateway/production
uvicorn app:app --host 0.0.0.0 --port 8000

# Lấy token (login)
curl http://localhost:8000/token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "student", "password": "demo123"}'
 # {"access_token":"eyJhbGc...","token_type":"bearer"}
```

3. Dùng token để gọi API:

```bash
TOKEN="<token_từ_bước_2>"
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
```

**JWT Flow:**

```
1. Client → POST /token (username + password)
2. Server → verify → generate JWT (secret key)
3. Client → Request + Authorization: Bearer <JWT>
4. Server → verify signature → extract user_id → process
```

**Ưu điểm so với API Key:**
- Stateless (không cần check DB mỗi request)
- Có expiry tự động
- Chứa user info (role, permissions)

### Exercise 4.3: Rate limiting

**Nhiệm vụ:** Đọc `rate_limiter.py` và trả lời:

- **Algorithm?** → **Sliding Window Counter** (line 18: `max_requests=10, window_seconds=60`)
- **Limit?** → **10 requests/60 giây** (user tier), **100 requests/60 giây** (admin tier)
- **Bypass cho admin?** → Dùng `rate_limiter_admin` thay vì `rate_limiter_user` (lines 86-87)

**Trả lời:**

- Algorithm: **Sliding Window Counter** — đếm request trong sliding window 60 giây
- User limit: 10 req/phút
- Admin limit: 100 req/phút (dùng `rate_limiter_admin` cho admin role)

Test:

```bash
# Gọi liên tục 20 lần
for i in {1..20}; do
  curl http://localhost:8000/ask -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "Test '$i'"}'
done
# Request 11+ → 429 Too Many Requests
# Response: {"error":"Rate limit exceeded","retry_after_seconds":...}
```

**Response headers khi bị limit:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1234567890
Retry-After: 45
```

### Exercise 4.4: Cost guard

**Nhiệm vụ:** Đọc `cost_guard.py` và implement logic:

**Trả lời:**

- **Budget:** $1/ngày per user, $10/ngày global (line 42-44)
- **Giá token:** $0.15/1M input, $0.60/1M output (GPT-4o-mini)
- **Khi vượt budget:** HTTP 402 Payment Required
- **Reset:** midnight UTC hàng ngày

**Code đã implement sẵn trong `cost_guard.py`:**

```python
# check_budget(user_id) - kiểm tra trước khi gọi LLM
# record_usage(user_id, input_tokens, output_tokens) - ghi sau khi gọi
# get_usage(user_id) - lấy stats hiện tại
```

Test:

```bash
# Gọi nhiều requests
curl .../ask -d '{"question": "..."}'  # Request 1-2 → OK
# Sau khi vượt $1 → 402 Payment Required
# Response:
# {"error":"Daily budget exceeded","used_usd":1.01,"budget_usd":1.0}
```

**Headers trả về:** `X-RateLimit-Limit` (budget), `X-RateLimit-Remaining`

### Checkpoint 4

- [x] Implement API key authentication
- [x] Hiểu JWT flow
- [x] Implement rate limiting
- [x] Implement cost guard với Redis

---

## Part 5: Scaling & Reliability (40 phút)

### Concepts

**Vấn đề:** 1 instance không đủ khi có nhiều users.

**Giải pháp:**

1. **Stateless design** — Không lưu state trong memory
2. **Health checks** — Platform biết khi nào restart
3. **Graceful shutdown** — Hoàn thành requests trước khi tắt
4. **Load balancing** — Phân tán traffic

### Exercise 5.1: Health checks

```bash
cd ../../05-scaling-reliability/develop
```

**Nhiệm vụ:** Implement 2 endpoints:

**Trả lời:**

- **`/health` (Liveness):** Trả về 200 nếu process còn sống → platform restart nếu fail
- **`/ready` (Readiness):** Trả về 200 nếu sẵn sàng, 503 nếu chưa → LB quyết định route traffic

**Code đã có trong `app.py`:**

```python
@app.get("/health")
def health():
    # Liveness: kiểm tra process còn chạy
    return {"status": "ok", "uptime_seconds": uptime, "version": "1.0.0"}

@app.get("/ready")
def ready():
    # Readiness: kiểm tra dependencies (Redis, DB)
    if not _is_ready:
        raise HTTPException(503, "Agent not ready")
    return {"ready": True, "in_flight_requests": _in_flight_requests}
```

**Platform dùng:**
- Railway/Render: `/health` cho health check
- Kubernetes: `/health` (liveness) + `/ready` (readiness)

Test:

```bash
curl http://localhost:8000/health
# {"status":"ok","uptime_seconds":120.5,"version":"1.0.0"}

curl http://localhost:8000/ready
# {"ready":true,"in_flight_requests":0}
```

### Exercise 5.2: Graceful shutdown

**Nhiệm vụ:** Implement signal handler:

**Trả lời:**

- **SIGTERM:** Platform gửi khi muốn restart/stop container
- **Graceful:** Chờ in-flight requests hoàn thành trước khi tắt (uvicorn tự xử lý qua `lifespan`)
- **Cần làm:** Đừng handle SIGKILL, chỉ loggraceful shutdown

**Code đã có trong `app.py`:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _is_ready = True
    yield
    # Shutdown
    _is_ready = False  # Stop accepting new requests
    while _in_flight_requests > 0:
        time.sleep(1)  # Wait for in-flight requests
    # Close connections
    logger.info("Shutdown complete")

# Track in-flight requests
@app.middleware("http")
async def track_requests(request, call_next):
    global _in_flight_requests
    _in_flight_requests += 1
    try:
        return await call_next(request)
    finally:
        _in_flight_requests -= 1

# Signal handler
signal.signal(signal.SIGTERM, handle_sigterm)  # Log only
```

Test:

```bash
# Gửi long request
curl http://localhost:8000/ask -X POST \
  -d '{"question": "Explain quantum computing"}' &

# Kill gracefully
kill -TERM <pid>

# Logs:
# 🔄 Graceful shutdown initiated...
# Waiting for 1 in-flight requests...
# ✅ Shutdown complete
```

### Exercise 5.3: Stateless design

```bash
cd ../production
```

**Nhiệm vụ:** Refactor code để stateless.

**Trả lời:**

- **Tại sao cần stateless?** Khi scale ra N instances, mỗi instance có memory riêng. User A gửi request đến Instance 1 → lưu history. Request tiếp theo đến Instance 2 → KHÔNG có history!
- **Giải pháp:** Lưu state trong Redis (shared giữa các instances)

**Anti-pattern:**

```python
# State trong memory ❌
conversation_history = {}

@app.post("/ask")
def ask(question: str, session_id: str):
    history = conversation_history.get(session_id, [])
```

**Correct:**

```python
# State trong Redis ✅
@app.post("/chat")
def chat(body: ChatRequest):
    session_id = body.session_id or uuid.uuid4()
    session = load_session(session_id)  # Redis
    # ...
    append_to_history(session_id, "user", body.question)
```

**Code đã có trong `production/app.py`:**

```python
def save_session(session_id: str, data: dict, ttl_seconds: int = 3600):
    """Lưu session vào Redis với TTL"""
    _redis.setex(f"session:{session_id}", ttl_seconds, json.dumps(data))

def load_session(session_id: str) -> dict:
    """Load session từ Redis"""
    data = _redis.get(f"session:{session_id}")
    return json.loads(data) if data else {}
```

Test:

```bash
# Request 1: Tạo session mới
curl -X POST http://localhost:8000/chat \
  -d '{"question": "Hello"}'
# {"session_id": "abc-123", "served_by": "instance-001"}

# Request 2: Cùng session_id (có thể được serve bởi instance khác)
curl -X POST http://localhost:8000/chat \
  -d '{"question": "Continue", "session_id": "abc-123"}'
# {"session_id": "abc-123", "served_by": "instance-002"}  ← Instance khác!
```

### Exercise 5.4: Load balancing

**Nhiệm vụ:** Chạy stack với Nginx load balancer:

**Trả lời:**

- **3 agent instances được start** (scale to 3)
- **Nginx phân tán** requests round-robin
- **Nếu 1 instance die**, traffic tự động chuyển sang instances khác

**Docker Compose config:**

```yaml
# docker-compose.yml
services:
  agent:
    build: .
    scale: 3  # or: docker compose up --scale agent=3
  
  nginx:
    image: nginx:alpine
    # upstream: agent → load balance
```

**Test:**

```bash
docker compose up --scale agent=3

# Gọi 10 requests
for i in {1..10}; do
  curl http://localhost/chat -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}' 2>/dev/null | jq '.served_by'
done

# Output: instance-001, instance-002, instance-003, instance-001, ...

# Check logs
docker compose logs agent --tail 30
```

**Kết quả:** Requests được phân tán đều qua 3 instances. Khi kill 1 instance, traffic tự động sang 2 instances còn lại.

### Exercise 5.5: Test stateless

```bash
cd ../../05-scaling-reliability/production
python test_stateless.py
```

**Script này:**

1. Gọi API để tạo conversation với session_id
2. Kill random instance (simulate instance crash)
3. Gọi tiếp → conversation vẫn còn (vì state trong Redis)

**Kết quả mong đợi:**

```
✅ Created session: abc-123
✅ Response from instance-001
✅ Killed instance-001
✅ Response from instance-002  ← Instance khác, nhưng vẫn có history!
✅ Conversation history preserved!
```

**Giải thích:** Session lưu trong Redis, nên bất kỳ instance nào cũng đọc được. Khi dùng in-memory → conversation bị mất sau khi kill instance.

### Checkpoint 5

- [x] Implement health và readiness checks
- [x] Implement graceful shutdown
- [x] Refactor code thành stateless
- [x] Hiểu load balancing với Nginx
- [x] Test stateless design

---

## Part 6: Final Project (60 phút)

### Objective

Build một production-ready AI agent từ đầu, kết hợp TẤT CẢ concepts đã học.

### Requirements

**Functional:**

- [ ] Agent trả lời câu hỏi qua REST API
- [ ] Support conversation history
- [ ] Streaming responses (optional)

**Non-functional:**

- [ ] Dockerized với multi-stage build
- [ ] Config từ environment variables
- [ ] API key authentication
- [ ] Rate limiting (10 req/min per user)
- [ ] Cost guard ($10/month per user)
- [ ] Health check endpoint
- [ ] Readiness check endpoint
- [ ] Graceful shutdown
- [ ] Stateless design (state trong Redis)
- [ ] Structured JSON logging
- [ ] Deploy lên Railway hoặc Render
- [ ] Public URL hoạt động

### Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Nginx (LB)     │
└──────┬──────────┘
       │
       ├─────────┬─────────┐
       ▼         ▼         ▼
   ┌──────┐  ┌──────┐  ┌──────┐
   │Agent1│  │Agent2│  │Agent3│
   └───┬──┘  └───┬──┘  └───┬──┘
       │         │         │
       └─────────┴─────────┘
                 │
                 ▼
           ┌──────────┐
           │  Redis   │
           └──────────┘
```

### Step-by-step

#### Step 1: Project setup (5 phút)

```bash
mkdir my-production-agent
cd my-production-agent

# Tạo structure
mkdir -p app
touch app/__init__.py
touch app/main.py
touch app/config.py
touch app/auth.py
touch app/rate_limiter.py
touch app/cost_guard.py
touch Dockerfile
touch docker-compose.yml
touch requirements.txt
touch .env.example
touch .dockerignore
```

#### Step 2: Config management (10 phút)

**File:** `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # TODO: Define all config
    # - PORT
    # - REDIS_URL
    # - AGENT_API_KEY
    # - LOG_LEVEL
    # - RATE_LIMIT_PER_MINUTE
    # - MONTHLY_BUDGET_USD
    pass

settings = Settings()
```

#### Step 3: Main application (15 phút)

**File:** `app/main.py`

```python
from fastapi import FastAPI, Depends, HTTPException
from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget

app = FastAPI()

@app.get("/health")
def health():
    # TODO
    pass

@app.get("/ready")
def ready():
    # TODO: Check Redis connection
    pass

@app.post("/ask")
def ask(
    question: str,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
    _budget: None = Depends(check_budget)
):
    # TODO:
    # 1. Get conversation history from Redis
    # 2. Call LLM
    # 3. Save to Redis
    # 4. Return response
    pass
```

#### Step 4: Authentication (5 phút)

**File:** `app/auth.py`

```python
from fastapi import Header, HTTPException

def verify_api_key(x_api_key: str = Header(...)):
    # TODO: Verify against settings.AGENT_API_KEY
    # Return user_id if valid
    # Raise HTTPException(401) if invalid
    pass
```

#### Step 5: Rate limiting (10 phút)

**File:** `app/rate_limiter.py`

```python
import redis
from fastapi import HTTPException

r = redis.from_url(settings.REDIS_URL)

def check_rate_limit(user_id: str):
    # TODO: Implement sliding window
    # Raise HTTPException(429) if exceeded
    pass
```

#### Step 6: Cost guard (10 phút)

**File:** `app/cost_guard.py`

```python
def check_budget(user_id: str):
    # TODO: Check monthly spending
    # Raise HTTPException(402) if exceeded
    pass
```

#### Step 7: Dockerfile (5 phút)

```dockerfile
# TODO: Multi-stage build
# Stage 1: Builder
# Stage 2: Runtime
```

#### Step 8: Docker Compose (5 phút)

```yaml
# TODO: Define services
# - agent (scale to 3)
# - redis
# - nginx (load balancer)
```

#### Step 9: Test locally (5 phút)

```bash
docker compose up --scale agent=3

# Test all endpoints
curl http://localhost/health
curl http://localhost/ready
curl -H "X-API-Key: secret" http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "user1"}'
```

#### Step 10: Deploy (10 phút)

```bash
# Railway
railway init
railway variables set REDIS_URL=...
railway variables set AGENT_API_KEY=...
railway up

# Hoặc Render
# Push lên GitHub → Connect Render → Deploy
```

### Validation

Chạy script kiểm tra:

```bash
cd 06-lab-complete
python check_production_ready.py
```

Script sẽ kiểm tra:

- Dockerfile exists và valid
- Multi-stage build
- .dockerignore exists
- Health endpoint returns 200
- Readiness endpoint returns 200
- Auth required (401 without key)
- Rate limiting works (429 after limit)
- Cost guard works (402 when exceeded)
- Graceful shutdown (SIGTERM handled)
- Stateless (state trong Redis, không trong memory)
- Structured logging (JSON format)

### Grading Rubric

| Criteria          | Points | Description                       |
| ----------------- | ------ | --------------------------------- |
| **Functionality** | 20     | Agent hoạt động đúng              |
| **Docker**        | 15     | Multi-stage, optimized            |
| **Security**      | 20     | Auth + rate limit + cost guard    |
| **Reliability**   | 20     | Health checks + graceful shutdown |
| **Scalability**   | 15     | Stateless + load balanced         |
| **Deployment**    | 10     | Public URL hoạt động              |
| **Total**         | 100    |                                   |

---

## Hoàn Thành!

Bạn đã:

- Hiểu sự khác biệt dev vs production
- Containerize app với Docker
- Deploy lên cloud platform
- Bảo mật API
- Thiết kế hệ thống scalable và reliable

### Next Steps

1. **Monitoring:** Thêm Prometheus + Grafana
2. **CI/CD:** GitHub Actions auto-deploy
3. **Advanced scaling:** Kubernetes
4. **Observability:** Distributed tracing với OpenTelemetry
5. **Cost optimization:** Spot instances, auto-scaling

### Resources

- [12-Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)

---

## Q&A

**Q: Tôi không có credit card, có thể deploy không?**
A: Có! Railway cho $5 credit, Render có 750h free tier.

**Q: Mock LLM khác gì với OpenAI thật?**
A: Mock trả về canned responses, không gọi API. Để dùng OpenAI thật, set `OPENAI_API_KEY` trong env.

**Q: Làm sao debug khi container fail?**
A: `docker logs <container_id>` hoặc `docker exec -it <container_id> /bin/sh`

**Q: Redis data mất khi restart?**
A: Dùng volume: `volumes: - redis-data:/data` trong docker-compose.

**Q: Làm sao scale trên Railway/Render?**
A: Railway: `railway scale <replicas>`. Render: Dashboard → Settings → Instances.

---

**Happy Deploying! **
