# DNS Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable open-source multi-provider DNS orchestration MVP with a Django REST Framework adapter and a table-first React dashboard; GoDaddy is the first implemented provider.

**Architecture:** The browser calls only Django REST Framework `/api/*` endpoints. Django owns provider credentials, translates provider records into stable project schemas, and falls back to deterministic demo fixtures when demo mode is enabled. React + Vite renders the approved expanded-navigation/table-first design.

**Tech Stack:** Python 3.9+, Django 4.2 LTS, Django REST Framework, django-cors-headers, httpx, pydantic, pytest; React 19, TypeScript 7, Vite 8, CSS modules-free component styles.

**Spec:** `docs/superpowers/specs/2026-09-27-godaddy-dns-manager-design.md`

## Global Constraints

- GoDaddy PAT stays server-side and is never included in frontend source or responses.
- Default local mode is deterministic demo mode; real API mode requires `GODADDY_DEMO_MODE=false` and `GODADDY_PAT`.
- Read requests may retry once on retryable transport/server failures; write requests never retry automatically.
- DNS TTL values are integers in seconds and are passed through unchanged.
- No domain purchase, renewal, payment, commerce, deployment, or user-account subsystem in this MVP.

### Task 1: Backend contracts and failing tests

**Files:**
- Create: `backend/app/models.py`
- Create: `backend/app/config.py`
- Create: `backend/app/demo_data.py`
- Create: `tests/test_models.py`
- Create: `tests/test_demo_mode.py`

**Interfaces:**
- Produces `DNSRecord`, `DomainSummary`, `RecordCreate`, `RecordUpdate`, `ActivityEntry`.
- Produces `Settings` with `godaddy_pat`, `godaddy_demo_mode`, `godaddy_api_base`, `request_timeout_seconds`.

- [ ] **Step 1: Write failing model and demo tests** asserting a valid A record, rejected empty type/name/data, and deterministic demo domain/record values.
- [ ] **Step 2: Run `pytest tests/test_models.py tests/test_demo_mode.py -q` and confirm import/implementation failures.**
- [ ] **Step 3: Implement pydantic models, environment settings, and demo fixtures.**
- [ ] **Step 4: Run the focused tests and confirm they pass.**

### Task 2: GoDaddy client and API routes

**Files:**
- Create: `backend/manage.py`
- Create: `backend/config/settings.py`
- Create: `backend/config/urls.py`
- Create: `backend/dns_api/apps.py`
- Create: `backend/dns_api/serializers.py`
- Create: `backend/dns_api/urls.py`
- Create: `backend/dns_api/views.py`
- Create: `backend/dns_api/services.py`
- Create: `backend/app/godaddy_client.py`
- Create: `backend/app/service.py`
- Create: `tests/test_client.py`
- Create: `tests/test_api.py`

**Interfaces:**
- `GoDaddyClient.list_domains() -> list[DomainSummary]`
- `GoDaddyClient.list_records(domain: str) -> list[DNSRecord]`
- `GoDaddyClient.create_record(domain: str, record: RecordCreate) -> DNSRecord`
- `GoDaddyClient.update_record(domain: str, record_id: str, record: RecordUpdate) -> DNSRecord`
- `GoDaddyClient.delete_record(domain: str, record_id: str) -> None`
- Django REST Framework routes under `/api/health`, `/api/domains`, `/api/domains/{domain}/records`, and `/api/activity`.

- [ ] **Step 1: Write failing transport tests** for Bearer header, record path, response normalization, retryable read error, and no write retry.
- [ ] **Step 2: Run `pytest tests/test_client.py -q` and verify the expected failures.**
- [ ] **Step 3: Implement the client with 15-second timeout, one read retry, and GoDaddy error translation.**
- [ ] **Step 4: Write failing FastAPI route tests** for demo reads, validation errors, and activity entries.
- [ ] **Step 5: Run `pytest tests/test_api.py -q` and verify failures are caused by missing Django routes.**
- [ ] **Step 6: Implement Django settings, serializers, service wiring, and routes.**
- [ ] **Step 7: Run `pytest tests -q` and confirm all backend tests pass.**

### Task 3: Frontend table-first dashboard

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/api.ts`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/components/Sidebar.tsx`
- Create: `frontend/src/components/RecordTable.tsx`
- Create: `frontend/src/components/RecordDrawer.tsx`

**Interfaces:**
- `api.listDomains(): Promise<DomainSummary[]>`
- `api.listRecords(domain: string): Promise<DNSRecord[]>`
- `api.createRecord(domain: string, payload: RecordDraft): Promise<DNSRecord>`
- `api.updateRecord(domain: string, id: string, payload: RecordDraft): Promise<DNSRecord>`
- `api.deleteRecord(domain: string, id: string): Promise<void>`

- [ ] **Step 1: Add package metadata and TypeScript types.**
- [ ] **Step 2: Implement API helpers with `VITE_API_BASE_URL` defaulting to `/api`.**
- [ ] **Step 3: Implement the expanded sidebar, stats, toolbar, table, drawer, confirmation state, error state, and demo-friendly empty/loading states.**
- [ ] **Step 4: Add CSS tokens matching the approved dark navigation and light table-first layout.**
- [ ] **Step 5: Run `npm install` and `npm run build`.**

### Task 4: Repository setup and documentation

**Files:**
- Create: `README.md`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `backend/requirements.txt`
- Create: `backend/run.py`
- Create: `docker-compose.yml`
- Modify: `docs/project-ledger.md`

- [ ] **Step 1: Add local setup, demo mode, real PAT mode, API routes, and security notes to README.**
- [ ] **Step 2: Add environment examples without secrets.**
- [ ] **Step 3: Add a development compose file that starts backend and frontend commands without embedding credentials.**
- [ ] **Step 4: Run a clean-file inventory and update the project ledger with writes, tests, limits, and rollback.**

### Task 5: End-to-end local verification

**Files:**
- Modify: `docs/project-ledger.md`

- [ ] **Step 1: Run `pytest tests -q`.**
- [ ] **Step 2: Run `npm run build --prefix frontend`.**
- [ ] **Step 3: Start Django in demo mode and verify `GET /api/health`, `GET /api/domains`, and `GET /api/domains/example.com/records`.**
- [ ] **Step 4: Run a production-secret scan over tracked source files.**
- [ ] **Step 5: Record real GoDaddy provider verification as not run unless a PAT is supplied.**
