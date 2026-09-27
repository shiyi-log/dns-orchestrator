# GoDaddy DNS Manager 开发文档设计说明

## 目标

补充一份面向本地开发者、贡献者和维护者的开发文档，解释当前仓库的真实运行方式、模块边界、接口契约、验证命令和已知限制。文档应能让新贡献者在不阅读全部源码的情况下完成本地启动、修改、测试和问题定位。

## 当前缺口

`README.md` 已覆盖项目简介、快速启动、真实 GoDaddy PAT 配置、API 路由和基础测试命令，但仍缺少以下开发者需要的上下文：

- 浏览器、Django REST Framework、`DNSService` 和 GoDaddy API 之间的数据流；
- 后端模块与前端组件的职责、扩展位置和依赖方向；
- 演示模式与真实 API 模式的行为差异；
- DNS 记录模型、校验范围、TTL 单位和可选字段；
- 读取请求重试与写入请求不重试的原因和边界；
- API 错误格式、活动记录和前端刷新行为；
- CI 与本地验证的对应关系；
- 真实 GoDaddy、持久化、认证和生产部署尚未覆盖的范围。

## 文档方案

新增 `docs/DEVELOPMENT.md`，采用“先运行、再理解、后扩展”的顺序：

1. **文档定位与事实边界**：说明文档基于当前代码，明确演示数据、模拟 HTTP 测试与真实 GoDaddy 验收不是同一层级证据。
2. **技术栈与目录地图**：列出 Django、DRF、Pydantic、httpx、React、TypeScript、Vite 的用途，并映射到实际目录。
3. **架构和请求链路**：用文本流程描述浏览器 → `/api/*` → `DNSService` → `GoDaddyClient`/演示内存状态的调用路径，强调 PAT 只在后端读取。
4. **本地开发流程**：分别说明 `uv` 后端、npm 前端、Docker Compose 的启动方式，包含 `DJANGO_DEBUG`、CORS 和端口前提。
5. **配置矩阵**：解释 `.env.example` 中每个变量、默认值、演示/真实模式要求和敏感值保存规则。
6. **后端开发指南**：说明模型、序列化、视图、服务层、客户端的职责，记录新增接口或 GoDaddy 字段时应修改的边界。
7. **API 合约**：列出健康检查、域名、记录 CRUD、活动记录的请求/响应示例、状态码和错误格式。
8. **DNS 记录与可靠性规则**：说明记录类型、TTL 秒数范围、URL 编码、GET 最多一次重试、写操作不自动重试及其恢复策略。
9. **前端开发指南**：说明 API 封装、状态管理、表格/抽屉/侧边栏组件，以及新增字段和交互状态时的同步位置。
10. **测试、构建和 CI**：把本地 pytest、Django check、Vite build 与 `.github/workflows/ci.yml` 的 job 对齐，并标明尚未运行的外部验证。
11. **故障排查和安全边界**：覆盖 PAT 缺失、CORS、端口占用、依赖缓存、GoDaddy 错误和演示数据重启丢失；禁止把 PAT 放进前端或提交到仓库。
12. **扩展路线与限制**：说明持久化活动日志、登录授权、部署、真实 provider 验收等后续方向，但不将其伪装成当前能力。

## 事实来源与写作约束

- 以 `backend/app/*`、`backend/dns_api/*`、`backend/config/*`、`frontend/src/*`、测试、配置文件和 CI 工作流为事实来源。
- 不凭空增加当前不存在的鉴权、数据库持久化、后台任务、部署平台或 GoDaddy 能力。
- 示例中的 PAT 一律使用 `[REDACTED_SECRET]`。
- 所有时间示例使用带偏移的 ISO 8601；文档只描述当前代码实际使用的 UTC 活动时间和秒数 TTL。
- 明确区分静态检查、本地测试、浏览器运行、模拟 provider 响应和真实 GoDaddy/生产 DNS 验收。
- 文档以中文为主，代码命令、路径、接口和环境变量保持原样。

## 变更范围

范围内：

- 新增 `docs/DEVELOPMENT.md`；
- 在 `README.md` 增加开发文档入口；
- 在 `docs/project-ledger.md` 追加读取、写入、验证、限制和复用记录。

范围外：

- 不修改 Python、TypeScript、CSS、依赖锁文件或 CI 行为；
- 不配置或使用真实 GoDaddy PAT；
- 不执行生产 DNS 写入、部署或远程仓库操作；
- 不把现有设计说明和实现计划改写成开发文档的替代品。

## 验收标准

- 新开发者可根据开发文档完成后端检查、后端测试和前端构建；
- 文档中的目录、命令、路由、字段和默认值与当前代码一致；
- 文档明确指出真实 GoDaddy 和生产 DNS 验收尚未运行；
- README 能链接到开发文档；
- `uv run pytest tests -q`、`uv run python backend/manage.py check`、`npm run build --prefix frontend` 通过；
- 文档不包含真实密钥、私有令牌或未经验证的成功声明。

## 回滚与后续利用

文档变更均为可逆的 Git 文件变更；回滚时删除 `docs/DEVELOPMENT.md` 并撤销 README 链接即可，不影响运行时。后续新增 API、记录类型或部署方式时，应先更新开发文档的事实章节，再同步测试和 README 的入口说明。
