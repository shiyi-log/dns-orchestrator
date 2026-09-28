# 解析中枢 / DNS Orchestrator 设计说明

## 目标

从空目录创建一个可开源、可本地运行的 Django DNS 管理项目。第一版以 GoDaddy 为首个 Provider，聚焦域名解析：读取域名和 DNS 记录，新增、修改、删除记录，展示同步状态和最近操作。

## 范围

包含：

- Django + Django REST Framework 后端；
- GoDaddy REST API 的 Bearer PAT 认证适配；
- 域名列表和 DNS 记录读取；
- A、AAAA、CNAME、MX、TXT、NS 等记录的新增、修改和删除；
- 前端展开式导航和表格优先 DNS 管理台；
- 默认演示数据，避免没有凭证时页面无法运行；
- 变更前确认、错误展示和本地操作日志；
- 单元测试、前端构建和运行文档。

第一版不包含域名购买、续费、付款、商城、用户权限系统和生产部署。

## 架构

浏览器只访问项目自己的 Django REST Framework `/api/*` 接口。GoDaddy PAT 只由后端读取环境变量并添加到出站请求中，绝不发送到前端。后端把 GoDaddy 的响应转换为稳定的项目数据结构，前端不依赖 GoDaddy 的原始字段。

```text
React + Vite
    │
    ▼
Django REST Framework /api/domains/*
    │
    ▼
GoDaddy REST API
```

没有 PAT 时，Django 默认启用演示模式，返回固定的本地 DNS 数据；设置 `GODADDY_DEMO_MODE=false` 后必须提供 PAT，否则启动检查失败。

## 后端接口

```text
GET    /api/health
GET    /api/domains
GET    /api/domains/{domain}/records
POST   /api/domains/{domain}/records
PUT    /api/domains/{domain}/records/{record_id}
DELETE /api/domains/{domain}/records/{record_id}
GET    /api/activity
```

记录数据使用项目统一格式：

```json
{
  "id": "rec-001",
  "type": "A",
  "name": "@",
  "data": "3.0.3.205",
  "ttl": 600,
  "priority": null,
  "status": "active"
}
```

后端把 GoDaddy HTTP 错误转换为包含 `status_code`、`message` 和 `retryable` 的 JSON 错误。请求超时固定为 15 秒；仅对连接错误和 429、500、502、503、504 做一次短退避重试，写操作不会自动重复提交。

## 前端设计

采用 A 方案“表格优先”：

- 展开式深色侧边栏，显示概览、域名、解析记录、变更记录、设置；
- 当前域名上下文面板显示域名和同步状态；
- 顶部显示域名选择、搜索、记录类型筛选和刷新；
- 主区域使用 DNS 记录表格，不把记录转换成卡片；
- 新增和编辑使用右侧抽屉；
- 提交前显示变更摘要，确认后调用后端；
- 删除操作要求二次确认；
- 页面包含加载、空数据、错误、同步中和成功状态；
- 窄屏时侧边栏收缩为图标栏，表格支持横向滚动。

## 安全和配置

`.env` 只在后端使用，提交 `.env.example`，示例值使用 `[REDACTED_SECRET]`。前端不读取 `GODADDY_PAT`，不在构建产物中注入 PAT。默认只监听本机地址。

## 验收标准

- `pytest` 覆盖演示模式、认证头、记录读取、写操作错误和不重复重试；
- `npm run build` 成功；
- `GET /api/health` 返回 Django 服务状态和 `demo_mode`；
- 无 PAT 时页面仍能看到演示域名和解析记录；
- 有 PAT 时后端可以把请求发送到 GoDaddy API；
- 新增、修改、删除操作都经过后端确认，浏览器没有 GoDaddy 密钥；
- README 能指导用户安装、配置、启动和切换演示/真实 API 模式。

## 参考

- GoDaddy API 文档：`https://developer.godaddy.com/en/docs/api-users`
- GoDaddy 认证文档：`https://developer.godaddy.com/en/docs/api-users/auth`
