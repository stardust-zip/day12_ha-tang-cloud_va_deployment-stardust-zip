# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

1. **API key hardcode** → Secret lộ trong code
2. **Database URL hardcode** → Credentials lộ  
3. **Debug mode** → Không nên bật trong production
4. **Port cố định** → Nên đọc từ env variable
5. **Host localhost** → Chỉ nhận kết nối local
6. **reload=True** → Auto-reload nguy hiểm trong production
7. **Không có health check** → Platform không biết khi nào restart
8. **print() logging** → Dùng structured logging

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode | Env vars | Secrets không bị lộ trong code |
| Health check | Không có | /health + /ready | Platform biết khi nào cần restart |
| Logging | print() | JSON | Dễ parse, search, aggregate |
| Shutdown | Đột ngột | Graceful (SIGTERM) | Cho phép in-flight requests hoàn thành |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image:** `python:3.11` (full Python distribution, ~1 GB)
2. **Working directory:** `/app`
3. **COPY requirements.txt trước:** Để leverage Docker layer cache
4. **CMD vs ENTRYPOINT:** CMD cung cấp default arguments (có thể override), ENTRYPOINT định đoạt command chính

### Exercise 2.3: Image size comparison

- **Develop:** 1.66 GB (DISK USAGE)
- **Production:** 236 MB (multi-stage)
- **Difference:** 87% smaller!

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- **URL:** https://day12-production.up.railway.app

### Test output

```bash
# Health check
$ curl https://day12-production.up.railway.app/health
{"status":"ok","uptime_seconds":278.9,"platform":"Railway",...}

# Agent endpoint
$ curl https://day12-production.up.railway.app/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
{"answer":"..."}
```

---

## Part 4: API Security

### Exercise 4.1: API Key authentication

- API key check trong `verify_api_key()` sử dụng `APIKeyHeader`
- Không có key: HTTP 401 "Missing API key"
- Sai key: HTTP 403 "Invalid API key"

### Exercise 4.2: JWT authentication

- Flow: Client → POST /token → Server verify → generate JWT → Client gửi JWT trong header
- Ưu điểm: Stateless, có expiry tự động, chứa user info

### Exercise 4.3: Rate limiting

- Algorithm: **Sliding Window Counter**
- User limit: 10 req/phút
- Admin limit: 100 req/phút

### Exercise 4.4: Cost guard

- Budget: $1/ngày per user, $10/ngày global
- Khi vượt: HTTP 402 Payment Required
- Reset: midnight UTC hàng ngày

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

- `/health` (Liveness): Platform restart nếu fail
- `/ready` (Readiness): LB quyết định route traffic (trả 503 nếu chưa ready)

### Exercise 5.2: Graceful shutdown

- SIGTERM signal: Platform gửi khi muốn restart/stop
- uvicorn tự xử lý graceful shutdown qua `lifespan`
- Chờ in-flight requests hoàn thành trước khi tắt

### Exercise 5.3: Stateless design

- State lưu trong Redis (shared giữa các instances)
- Khi scale ra N instances, bất kỳ instance nào cũng đọc được session

### Exercise 5.4: Load balancing

- Nginx phân tán requests round-robin
- Nếu 1 instance die, traffic tự động sang instances khác

### Exercise 5.5: Test stateless

- Session lưu trong Redis, nên conversation không bị mất khi kill instance
- Khi dùng in-memory → conversation bị mất!