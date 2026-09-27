# 多提供商 DNS 账号管理设计说明

## 目标

将当前单一 GoDaddy DNS 管理台升级为可管理多个 GoDaddy 账号、并能继续扩展 Cloudflare、阿里云 DNS、腾讯云 DNS 的多提供商 DNS 管理平台。

第一阶段只实现 GoDaddy 多账号；其他提供商只建立接口、能力模型和前端展示边界，不调用它们的真实 API。

## 已确认范围

### 第一阶段包含

- 一个默认 Workspace，供当前本机用户使用；
- Workspace 下的多个 ProviderAccount；
- ProviderAccount 支持多个 GoDaddy 连接；
- GoDaddy PAT 加密保存；
- 添加、编辑、删除、启用、禁用和验证 GoDaddy 账号；
- 设置默认账号；
- 账号切换后重新读取该账号的域名和 DNS 记录；
- 账号之间的域名和解析数据隔离；
- 统一 DNS 记录模型；
- GoDaddy 适配器迁移到统一 Provider 接口；
- 保留现有 `/api/domains*` 路由，映射到当前默认 GoDaddy 账号；
- 前端账号切换器、账号管理页和连接状态；
- 单元、API、加密、账号隔离和前端构建测试。

### 第一阶段不包含

- Cloudflare、阿里云 DNS、腾讯云 DNS 的真实适配器；
- 用户注册、登录、Workspace 邀请、角色和团队权限；
- 域名购买、续费、付款、CDN、WAF、证书和云服务器管理；
- 自动后台同步、任务队列和生产部署；
- 把 PAT 或其他云厂商密钥返回给浏览器。

## 方案选择

### 方案 A：每个提供商独立实现全部业务

为 GoDaddy、Cloudflare、阿里云和腾讯云分别写账号、域名、解析页面和 API。首期实现快，但会把提供商差异散落在前端和路由中，未来添加新厂商需要重复修改多个层次。

### 方案 B：统一核心模型加 Provider Adapter

账号、Workspace、Zone、DNSRecord、操作记录和前端流程统一；每个提供商只实现认证、Zone 查询、记录读写和能力声明。GoDaddy 先接入，未来提供商复用同一套账号和 UI 流程。

### 方案 C：完整插件市场

每个提供商独立打包、安装和升级。扩展性最大，但需要插件签名、版本兼容、运行隔离和分发机制，超出当前项目范围。

本项目采用方案 B。

## 数据模型

首期使用 Django 数据库模型和 SQLite 本地数据库。以后部署到 PostgreSQL 时不改变业务接口。后端增加 `cryptography` 依赖用于 Fernet 加密。

### Workspace

```text
id
name
created_at
updated_at
```

当前创建一个默认 Workspace。模型保留 Workspace 边界，但不实现登录和成员权限。

### ProviderAccount

```text
id
workspace_id
provider              # godaddy / cloudflare / aliyun / tencent
display_name
api_base
credential_ciphertext
is_default
is_enabled
status                # unknown / active / error / disabled
last_zone_count
last_verified_at
last_error
created_at
updated_at
```

同一个 Workspace 可以拥有多个相同 `provider` 的账号。`display_name` 用于前端区分“生产 GoDaddy”和“测试 GoDaddy”。

### Credential

凭证以加密 JSON 保存，不返回明文：

```json
{
  "kind": "godaddy_pat",
  "token": "[ENCRYPTED]"
}
```

加密使用应用级 Fernet 密钥，密钥来自 `ACCOUNT_ENCRYPTION_KEY` 环境变量。验证账号成功后，把本次 Zone 数量写入 `last_zone_count`，账号列表直接读取该缓存，不为每个列表请求重复调用提供商。生产模式没有该变量时拒绝新增或修改账号，但允许服务启动并读取不需要解密的账号元数据；尝试验证或使用受影响账号时返回配置错误。演示模式可以使用内存账号和固定演示数据。

未来提供商的凭证结构由 adapter 定义：

- GoDaddy：PAT；
- Cloudflare：API Token 和 Account ID；
- 阿里云：AccessKey ID 和 AccessKey Secret；
- 腾讯云：SecretId 和 SecretKey。

### Zone 和 DNSRecord

Zone 和 DNSRecord 首期不要求持久化，读取和写入仍由 Provider Adapter 负责。接口返回统一 DTO：

```json
{
  "id": "provider-record-id",
  "zone": "example.com",
  "type": "A",
  "name": "@",
  "content": "3.0.3.205",
  "ttl": 600,
  "priority": null,
  "status": "active",
  "provider_fields": {}
}
```

`provider_fields` 用于保留提供商差异，例如 Cloudflare 的 `proxied`、阿里云和腾讯云的线路或地域字段。通用 DNS 页面只操作统一字段；提供商专属字段由能力声明决定是否显示。

## Provider Adapter 接口

```python
class DNSProviderAdapter:
    provider: str

    def verify_connection(self) -> ProviderStatus: ...
    def list_zones(self) -> list[Zone]: ...
    def list_records(self, zone: Zone) -> list[DNSRecord]: ...
    def create_record(self, zone: Zone, draft: DNSRecordDraft) -> DNSRecord: ...
    def update_record(
        self,
        zone: Zone,
        record_id: str,
        draft: DNSRecordDraft,
    ) -> DNSRecord: ...
    def delete_record(self, zone: Zone, record_id: str) -> None: ...
    def capabilities(self) -> ProviderCapabilities: ...
```

`ProviderFactory` 根据 `ProviderAccount.provider` 创建适配器，并解密对应账号的凭证。业务层只依赖 `DNSProviderAdapter`，不直接读取 GoDaddy、Cloudflare 或其他厂商的 token。

## API 设计

### 账号管理

```text
GET    /api/providers
GET    /api/accounts
POST   /api/accounts
PATCH  /api/accounts/{account_id}
DELETE /api/accounts/{account_id}
POST   /api/accounts/{account_id}/verify
POST   /api/accounts/{account_id}/set-default
```

账号 API 返回：

```json
{
  "id": "account-001",
  "provider": "godaddy",
  "display_name": "生产 GoDaddy",
  "status": "active",
  "is_default": true,
  "zone_count": 12,
  "last_verified_at": "2026-09-27T04:00:00Z",
  "last_error": null
}
```

响应中不能出现 `credential_ciphertext`、PAT、AccessKey Secret、SecretKey 或任何原始认证字段。

### 账号范围的 DNS API

```text
GET    /api/accounts/{account_id}/zones
GET    /api/accounts/{account_id}/zones/{zone}/records
POST   /api/accounts/{account_id}/zones/{zone}/records
PUT    /api/accounts/{account_id}/zones/{zone}/records/{record_id}
DELETE /api/accounts/{account_id}/zones/{zone}/records/{record_id}
```

请求先校验 `account_id` 属于当前 Workspace，再由 ProviderFactory 创建适配器。账号验证失败、Zone 不存在、权限不足和提供商限流统一转换为项目错误格式。

### 旧 API 兼容

现有路由继续可用：

```text
GET    /api/domains
GET    /api/domains/{domain}/records
POST   /api/domains/{domain}/records
PUT    /api/domains/{domain}/records/{record_id}
DELETE /api/domains/{domain}/records/{record_id}
```

这些路由解析当前 Workspace 的默认 GoDaddy 账号。没有默认账号时返回明确的 `409`，提示先选择或设置默认账号。

## 前端设计

### 账号切换器

展开式侧边栏顶部显示当前账号：

```text
生产 GoDaddy
GoDaddy · 已连接
12 个 Zone
```

下拉菜单显示所有账号，包含提供商、状态和默认标记。切换账号后清空旧 Zone 和记录状态，再加载新账号数据，避免跨账号残留。

### 账号管理页

使用表格展示：

```text
账号名称
提供商
连接状态
Zone 数量
默认账号
最近验证
操作
```

添加账号使用右侧抽屉：

```text
选择提供商
输入账号名称
输入凭证
测试连接
保存账号
```

首期只有 GoDaddy 表单可用，其他提供商显示“即将支持”，不允许提交未实现的凭证类型。

### DNS 页面

保留当前表格优先布局。页面顶部显示：

- 当前提供商；
- 当前账号；
- 当前 Zone；
- 连接状态；
- 最近验证时间。

记录编辑器只显示当前适配器能力支持的字段。删除账号时要求二次确认，并明确说明只删除本地连接配置，不删除云厂商上的域名或记录。

## 安全边界

- `ACCOUNT_ENCRYPTION_KEY` 只在后端环境读取；
- PAT、AccessKey Secret、SecretKey 不写日志，不写活动记录，不返回 JSON；
- 账号验证请求不记录完整请求头和响应体；
- 账号删除只删除本地数据库记录；
- DNS 写操作仍需要用户在页面确认；
- 生产模式没有加密密钥时拒绝新增或修改账号；使用受影响账号时返回配置错误；
- Provider Adapter 只接收解密后的短生命周期凭证对象；
- 测试使用固定假凭证和 MockTransport，不使用真实账号。

## 错误和隔离

- 每个账号单独保存验证状态和最近错误；
- 一个账号连接失败时，账号列表和其他账号仍可用；
- 账号切换时不复用上一账号的 Zone、记录或错误状态；
- Provider 不支持的字段返回能力错误，不静默丢弃；
- 写请求不自动重试；
- 读请求可按照现有 GoDaddy 客户端规则进行一次有限重试。

## 分阶段实现

### Phase 1：GoDaddy 多账号

- Django migrations 和 Workspace/ProviderAccount 模型；
- Fernet 凭证加密；
- ProviderFactory 和 GoDaddy Adapter；
- 账号 CRUD、验证和默认账号；
- 账号范围 DNS API；
- 旧 API 兼容；
- 前端账号切换和账号管理页；
- 测试、CI、README 和迁移说明。

### Phase 2：Cloudflare

- Cloudflare Adapter；
- API Token 和 Account ID 凭证表单；
- Zone 和代理状态能力；
- Cloudflare 专属字段测试。

### Phase 3：阿里云和腾讯云

- 各自 AccessKey/Secret 或 SecretId/SecretKey 认证；
- 线路、地域、权重和 MX 扩展字段；
- 各自错误码和限流策略。

## 验收标准

- 可以创建至少两个 GoDaddy 账号并分别验证；
- 默认账号兼容旧 `/api/domains*` API；
- 切换账号后只能看到当前账号的 Zone 和 DNS 记录；
- 账号列表 API 和前端永远不返回明文凭证；
- 删除账号不会调用任何云厂商删除域名或记录的 API；
- GoDaddy DNS 读写仍通过统一 Adapter；
- 没有真实 PAT 时演示模式可运行；
- `uv run pytest tests -q`、Django system check、前端构建和 CI 全部通过；
- Cloudflare、阿里云、腾讯云在第一阶段只显示未实现状态，不伪造成功。

## 限制

- 第一阶段仍是本机单 Workspace，不提供用户登录；
- 账号凭证依赖本机 `ACCOUNT_ENCRYPTION_KEY`，密钥丢失后无法解密已有账号；
- Zone 和 DNS 记录不持久化，页面刷新时从提供商读取；
- 真实多账号 provider 验收需要用户提供对应凭证；
- 后续团队模式需要增加 Django 用户、Workspace 成员和权限模型。
