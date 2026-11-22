# Operations Runbook: Multi-Document RAG with Citations

**Author:** Vinit Kale  
**Context:** MIT-ADT University, MIT School of Computing, Pune – Agentic AI Course

---

## 1. Local Development Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional for local full-stack run)

### Running Backend Standalone
```bash
cd backend
python3 -m pip install -r requirements.txt
python3 app/main.py
```
Backend will serve at: `http://localhost:8000` (OpenAPI docs at `http://localhost:8000/docs`).

### Running Frontend Standalone
```bash
cd frontend
npm install
npm run dev
```
Frontend will serve at: `http://localhost:3000`.

---

## 2. Docker Compose Deployment
To launch the full stack (PostgreSQL with pgvector, Redis, MinIO, Backend, Frontend):
```bash
docker compose up --build -d
```
Check health:
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
```

---

## 3. Seeding Demo Data
To populate demo tenant, users, and ingest sample contracts, security runbooks, and SLA spreadsheets:
```bash
python3 scripts/seed_data.py
```
- Admin User: `admin@rag.local` / `AdminPass123!`
- Researcher: `researcher@rag.local` / `MemberPass123!`

---

## 4. Running Quality & Security Benchmark Suites
```bash
# 1. Run core unit tests
cd backend && python3 -m pytest tests/

# 2. Run red-team prompt injection suite
python3 scripts/test_prompt_injection.py

# 3. Run golden dataset RAG evaluation benchmark
python3 scripts/run_eval.py
```

---

## 5. Troubleshooting & FAQ

### Issue: "SSRF_PROTECTION_TRIGGERED" during URL ingestion
- Cause: Target URL resolved to loopback (127.0.0.1), private RFC 1918 subnet, or cloud metadata IP (169.254.169.254).
- Resolution: Only public HTTP/HTTPS URLs are permitted.

### Issue: Low citation coverage or answer abstention
- Cause: Query has no high-confidence evidence in the selected document collection.
- Behavior: Designed behavior. The system refuses to answer when evidence is insufficient instead of hallucinating.
