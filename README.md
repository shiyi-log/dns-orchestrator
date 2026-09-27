# GoDaddy DNS Manager

[![CI](https://github.com/shiyi-log/godaddy-dns-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/shiyi-log/godaddy-dns-manager/actions/workflows/ci.yml)

一个使用 Django、Django REST Framework、React 和 Vite 构建的 GoDaddy 域名解析可视化管理台。

当前版本聚焦 DNS 记录管理：

- 查看 GoDaddy 账户中的域名和 DNS 记录；
- 新增、修改、删除 A、AAAA、CNAME、MX、TXT、NS 等记录；
- 表格优先的解析管理界面；
- 展开式导航和当前域名上下文；
- 提交前预览、成功提示、错误状态和本地操作记录；
- 没有 PAT 时使用确定性的本地演示数据。

## 快速启动

项目使用 `uv` 管理 Python 环境，Node 负责前端依赖。

```bash
uv sync
cp .env.example .env

uv run python backend/manage.py check
uv run python backend/manage.py runserver 127.0.0.1:8000
```

另开一个终端启动前端：

```bash
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`。默认演示模式会显示 `example.com` 和示例解析记录，不需要 GoDaddy 凭证。

如果本机 npm 缓存权限异常，可以指定一个临时缓存目录：

```bash
npm_config_cache=/tmp/godaddy-npm-cache npm install
```

## 接入真实 GoDaddy API

在 `.env` 中设置：

```dotenv
GODADDY_DEMO_MODE=false
GODADDY_PAT=[REDACTED_SECRET]
GODADDY_API_BASE=https://api.godaddy.com
```

PAT 应只保存于后端环境。前端不会读取或打包 `GODADDY_PAT`。

当前客户端使用 GoDaddy Domains v3 DNS 接口：

```text
GET    /v3/domains/zones/{zone}/dns-records
POST   /v3/domains/zones/{zone}/dns-records
PUT    /v3/domains/zones/{zone}/dns-records/{recordId}
DELETE /v3/domains/zones/{zone}/dns-records/{recordId}
```

真实 API 模式需要为 PAT 配置域名读取和 DNS 更新权限。GoDaddy 的新增记录请求不是幂等操作，项目不会自动重试写请求；读取请求遇到临时错误最多重试一次。

## 项目接口

```text
GET    /api/health
GET    /api/domains
GET    /api/domains/{domain}/records
POST   /api/domains/{domain}/records
PUT    /api/domains/{domain}/records/{record_id}
DELETE /api/domains/{domain}/records/{record_id}
GET    /api/activity
```

## 目录结构

```text
backend/
  app/                  # GoDaddy 客户端、数据结构和演示数据
  config/               # Django 配置、URL、WSGI/ASGI
  dns_api/              # Django REST Framework API
  manage.py
frontend/
  src/                  # React 页面、表格、侧边栏和编辑抽屉
docs/
  superpowers/specs/    # 设计说明
  superpowers/plans/    # 实现计划
  project-ledger.md     # 追加式项目台账
tests/                  # 后端单元和 API 测试
```

## 测试和构建

```bash
uv run pytest tests -q
uv run python backend/manage.py check
npm run build --prefix frontend
```

当前验证覆盖本地演示模式和模拟 GoDaddy HTTP 响应；没有配置真实 PAT 时，不会宣称真实 GoDaddy 账号或生产域名已经验收。

GitHub Actions 会在 pull request、`main` 分支推送和手动 dispatch 时运行同样的后端检查、pytest 和前端构建。CI 使用 `uv.lock` 和 `frontend/package-lock.json` 的锁定依赖，并缓存两套依赖目录。

## 参考

- [GoDaddy API 文档](https://developer.godaddy.com/en/docs/api-users)
- [GoDaddy DNS 管理文档](https://developer.godaddy.com/en/docs/api-users/domains/manage/dns)
