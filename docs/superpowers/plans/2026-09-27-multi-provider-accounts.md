# Multi-Provider Account Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add encrypted multi-account GoDaddy management behind a provider-neutral DNS adapter boundary while preserving the existing default-account API and table-first UI.

**Architecture:** Django stores a default Workspace and encrypted ProviderAccount rows. A ProviderFactory creates a provider adapter from an account row; Phase 1 implements only GoDaddy, while Cloudflare, Aliyun DNS, and Tencent Cloud DNS appear as explicit unsupported provider metadata. Account-scoped REST endpoints drive a React account switcher and account-management drawer, and legacy `/api/domains*` endpoints resolve the default GoDaddy account.

**Tech Stack:** Django 4.2.30, Django REST Framework 3.16.1, SQLite migrations, `cryptography` Fernet, httpx, Pydantic DTOs, pytest; React 19, TypeScript 5.9, Vite 7.

**Spec:** `docs/superpowers/specs/2026-09-27-multi-provider-accounts-design.md`

## Global Constraints

- 第一阶段只实现 GoDaddy 多账号；其他提供商只建立接口、能力模型和前端展示边界，不调用它们的真实 API。
- 当前创建一个默认 Workspace。模型保留 Workspace 边界，但不实现登录和成员权限。
- PAT、AccessKey Secret、SecretKey 不写日志，不写活动记录，不返回 JSON。
- 生产模式没有加密密钥时拒绝新增或修改账号；使用受影响账号时返回配置错误。
- 旧 `/api/domains*` 路由映射到当前 Workspace 的默认 GoDaddy 账号。
- 写请求不自动重试；读请求可按照现有 GoDaddy 客户端规则进行一次有限重试。
- `.idea/` 是现有未跟踪目录，不加入、删除或修改。

### Task 1: Dependency, encryption, and account DTO contracts

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `.env.example`
- Create: `backend/app/crypto.py`
- Create: `backend/app/accounts.py`
- Create: `tests/test_crypto.py`
- Create: `tests/test_account_contracts.py`

**Interfaces:**
- `encrypt_secret(value: str, key: str) -> str`
- `decrypt_secret(ciphertext: str, key: str) -> str`
- `AccountCredential(provider: str, values: dict[str, str])`
- `ProviderAccountSummary(id: str, provider: str, display_name: str, status: str, is_default: bool, zone_count: int, last_verified_at: Optional[str], last_error: Optional[str])`

- [ ] **Step 1: Write the failing encryption tests.**

```python
def test_secret_round_trip_does_not_store_plaintext():
    ciphertext = encrypt_secret("pat-value", "test-encryption-key")
    assert ciphertext != "pat-value"
    assert decrypt_secret(ciphertext, "test-encryption-key") == "pat-value"

def test_wrong_key_is_rejected():
    ciphertext = encrypt_secret("pat-value", "test-encryption-key")
    with pytest.raises(CredentialError):
        decrypt_secret(ciphertext, "different-key")
```

- [ ] **Step 2: Run `uv run pytest tests/test_crypto.py tests/test_account_contracts.py -q` and confirm the imports fail because the new modules do not exist.**
- [ ] **Step 3: Add `cryptography` to `pyproject.toml`, regenerate `uv.lock`, implement Fernet key normalization and account summary DTOs, and add `ACCOUNT_ENCRYPTION_KEY=[REDACTED_SECRET]` to `.env.example`.**
- [ ] **Step 4: Run the focused tests and confirm encryption, provider validation, and secret redaction pass.**
- [ ] **Step 5: Commit `feat: add encrypted account contracts`.**

### Task 2: Django Workspace and ProviderAccount persistence

**Files:**
- Create: `backend/accounts/__init__.py`
- Create: `backend/accounts/apps.py`
- Create: `backend/accounts/models.py`
- Create: `backend/accounts/repository.py`
- Create: `backend/accounts/migrations/0001_initial.py`
- Modify: `backend/config/settings.py`
- Modify: `backend/config/urls.py`
- Create: `tests/test_account_models.py`

**Interfaces:**
- `Workspace.get_default() -> Workspace`
- `ProviderAccountRepository.list(workspace: Workspace) -> list[ProviderAccount]`
- `ProviderAccountRepository.create(workspace: Workspace, provider: str, display_name: str, credential: AccountCredential) -> ProviderAccount`
- `ProviderAccountRepository.set_default(account: ProviderAccount) -> ProviderAccount`
- `ProviderAccountRepository.delete(account_id: UUID) -> None`

- [ ] **Step 1: Write failing Django model tests** for one default Workspace, multiple GoDaddy accounts, unique default behavior, stored encrypted credential, disabled account status, and cached `last_zone_count`.
- [ ] **Step 2: Run `uv run pytest tests/test_account_models.py -q` and verify failure because the app and migration do not exist.**
- [ ] **Step 3: Add `backend.accounts` to `INSTALLED_APPS`, implement `Workspace` and `ProviderAccount`, and write the initial migration with UUID primary keys, provider choices, encrypted credential text, status, timestamps, and `last_zone_count`.**
- [ ] **Step 4: Implement repository operations so `set_default` clears the previous default in the same Workspace before setting the requested account.**
- [ ] **Step 5: Run `uv run python backend/manage.py makemigrations --check --dry-run`, `uv run python backend/manage.py migrate --run-syncdb`, and the focused model tests.**
- [ ] **Step 6: Commit `feat: persist provider accounts`.**

### Task 3: Provider adapter boundary and GoDaddy implementation

**Files:**
- Create: `backend/providers/__init__.py`
- Create: `backend/providers/base.py`
- Create: `backend/providers/factory.py`
- Create: `backend/providers/godaddy.py`
- Modify: `backend/app/godaddy_client.py`
- Modify: `backend/app/service.py`
- Create: `tests/test_provider_factory.py`
- Create: `tests/test_godaddy_adapter.py`

**Interfaces:**
- `DNSProviderAdapter.verify_connection() -> ProviderStatus`
- `DNSProviderAdapter.list_zones() -> list[Zone]`
- `DNSProviderAdapter.list_records(zone: Zone) -> list[DNSRecord]`
- `DNSProviderAdapter.create_record(zone: Zone, draft: DNSRecordDraft) -> DNSRecord`
- `DNSProviderAdapter.update_record(zone: Zone, record_id: str, draft: DNSRecordDraft) -> DNSRecord`
- `DNSProviderAdapter.delete_record(zone: Zone, record_id: str) -> None`
- `DNSProviderAdapter.capabilities() -> ProviderCapabilities`
- `ProviderFactory.for_account(account: ProviderAccount) -> DNSProviderAdapter`

- [ ] **Step 1: Write failing adapter tests** for unsupported provider rejection, GoDaddy account token injection, normalized zone/record output, and capability metadata.
- [ ] **Step 2: Run `uv run pytest tests/test_provider_factory.py tests/test_godaddy_adapter.py -q` and verify failures.**
- [ ] **Step 3: Implement Pydantic `Zone`, `DNSRecord`, `DNSRecordDraft`, `ProviderStatus`, and `ProviderCapabilities` contracts in `backend/providers/base.py`.**
- [ ] **Step 4: Wrap `GoDaddyClient` in `GoDaddyAdapter`, decrypt the account credential only inside adapter construction, and map its existing domain/record methods into the adapter interfaces.**
- [ ] **Step 5: Implement `ProviderFactory` with `godaddy` support and explicit `cloudflare`, `aliyun`, and `tencent` unsupported errors.**
- [ ] **Step 6: Update `DNSService` to accept an adapter instead of global settings while keeping deterministic demo mode for tests without persisted accounts.**
- [ ] **Step 7: Run all backend tests and commit `feat: add provider adapter boundary`.**

### Task 4: Account and account-scoped DNS API

**Files:**
- Modify: `backend/dns_api/serializers.py`
- Modify: `backend/dns_api/services.py`
- Modify: `backend/dns_api/views.py`
- Modify: `backend/dns_api/urls.py`
- Modify: `backend/config/urls.py`
- Create: `tests/test_accounts_api.py`
- Modify: `tests/test_api.py`

**Interfaces:**
- `GET /api/providers`
- `GET /api/accounts`
- `POST /api/accounts`
- `PATCH /api/accounts/{account_id}`
- `DELETE /api/accounts/{account_id}`
- `POST /api/accounts/{account_id}/verify`
- `POST /api/accounts/{account_id}/set-default`
- `GET|POST /api/accounts/{account_id}/zones/{zone}/records`
- `PUT|DELETE /api/accounts/{account_id}/zones/{zone}/records/{record_id}`

- [ ] **Step 1: Write failing API tests** for provider metadata, account creation with a fake PAT, redacted account response, connection verification, default switching, account-scoped records, cross-account isolation, unsupported provider response, and legacy default-account routes.
- [ ] **Step 2: Run `uv run pytest tests/test_accounts_api.py tests/test_api.py -q` and confirm the new routes fail.**
- [ ] **Step 3: Implement serializers that accept credentials only on write and never serialize encrypted or plaintext credential fields.**
- [ ] **Step 4: Implement account views and services with `Workspace.get_default()`, repository operations, adapter factory calls, `last_zone_count` updates after successful verification, and explicit 409 errors when no default GoDaddy account exists.**
- [ ] **Step 5: Add account-scoped URL routes and keep existing `/api/domains*` routes mapped to the default GoDaddy account.**
- [ ] **Step 6: Run `uv run pytest tests -q` and verify every account isolation and redaction assertion passes.**
- [ ] **Step 7: Commit `feat: expose multi-account DNS API`.**

### Task 5: React account switcher and account management UI

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`
- Create: `frontend/src/components/AccountSwitcher.tsx`
- Create: `frontend/src/components/AccountDrawer.tsx`
- Create: `frontend/src/components/AccountTable.tsx`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- `api.listProviders(): Promise<ProviderMetadata[]>`
- `api.listAccounts(): Promise<ProviderAccountSummary[]>`
- `api.createAccount(payload: AccountCreate): Promise<ProviderAccountSummary>`
- `api.updateAccount(id: string, payload: AccountUpdate): Promise<ProviderAccountSummary>`
- `api.deleteAccount(id: string): Promise<void>`
- `api.verifyAccount(id: string): Promise<ProviderAccountSummary>`
- `api.setDefaultAccount(id: string): Promise<ProviderAccountSummary>`
- `api.listZones(accountId: string): Promise<Zone[]>`
- `api.listAccountRecords(accountId: string, zone: string): Promise<DNSRecord[]>`

- [ ] **Step 1: Add failing frontend type/build usage for provider metadata, account summaries, selected account state, and account-scoped record methods.**
- [ ] **Step 2: Run `npm run build --prefix frontend` and record the expected missing type/API failures.**
- [ ] **Step 3: Implement account API helpers and types without exposing credential values in response types.**
- [ ] **Step 4: Add `AccountSwitcher` to the expanded sidebar, show provider/status/default markers, clear selected Zone and record state on account change, and load the selected account’s zones.**
- [ ] **Step 5: Add `AccountTable` and `AccountDrawer` with GoDaddy-only credential fields, connection verification, default selection, disabled unsupported providers, and delete confirmation copy that states no cloud DNS data is deleted.**
- [ ] **Step 6: Update the DNS table page to use account-scoped records while retaining the existing table-first layout and legacy demo fallback.**
- [ ] **Step 7: Run `npm run build --prefix frontend` and browser-check account switching, account drawer validation, redacted status, and empty/error states.**
- [ ] **Step 8: Commit `feat: add multi-account DNS management UI`.**

### Task 6: Documentation, CI, and final verification

**Files:**
- Modify: `README.md`
- Modify: `.env.example`
- Modify: `docs/project-ledger.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/superpowers/specs/2026-09-27-multi-provider-accounts-design.md`

- [ ] **Step 1: Document `ACCOUNT_ENCRYPTION_KEY`, migrations, account API routes, default-account compatibility, provider support matrix, and the fact that Cloudflare/Aliyun/Tencent adapters are not implemented in Phase 1.**
- [ ] **Step 2: Add CI dependency installation for `cryptography`, Django migrations, account tests, and frontend build.**
- [ ] **Step 3: Run `uv sync --locked`, `uv run python backend/manage.py migrate`, `uv run python backend/manage.py check`, `uv run pytest tests -q`, and `npm run build --prefix frontend`.**
- [ ] **Step 4: Start Django and Vite in demo mode; verify account list, account-scoped records, legacy default-account routes, and frontend account switching with browser evidence.**
- [ ] **Step 5: Run a secret scan over tracked files and assert no PAT, encrypted credential, or private key is present.**
- [ ] **Step 6: Record local, browser, CI, and real-provider boundaries in the ledger; keep real provider acceptance `not-run` without credentials.**
- [ ] **Step 7: Commit `docs: document multi-provider account management`, push `main`, and verify GitHub Actions run status and SHA parity.**
