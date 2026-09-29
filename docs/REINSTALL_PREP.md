# 重装系统准备与恢复

本文记录本项目在重装 macOS 前需要保留的内容，以及重装后的最短恢复路径。源码和锁文件已经推送到公开仓库，敏感配置和本机账号数据库不会提交到 Git。

## 当前基线

- 仓库：`https://github.com/shiyi-log/dns-orchestrator.git`
- 分支：`main`
- 最终提交以远程 `main` 和快照 `manifest.txt` 中的 HEAD 为准；不要依赖本文的固定 SHA。
- 本地路径：`/Users/a399/Desktop/data/godaddy`
- 本地时区：`Asia/Shanghai`（UTC+08:00）

重装前应确认 `git status` 只包含已知的本地文件，并再次执行：

```bash
git push origin main
git ls-remote origin refs/heads/main
```

远程 SHA 应与本地 `git rev-parse HEAD` 一致。

## 已准备的本机快照

本次准备会在仓库外创建权限为 `700` 的目录：

```text
/Users/a399/Desktop/data/godaddy-reinstall-backup-20260929/
```

快照包含：

- `git-repo.bundle`：当前 Git refs 的离线恢复包；
- `runtime/.env`：本机 Django/GoDaddy 配置，含敏感值；
- `runtime/pat`：GoDaddy PAT 文件；
- `runtime/backend-db.sqlite3`：本机账号和加密凭证数据库；
- `runtime/.idea/`：JetBrains 项目设置，可选恢复；
- `runtime/.superpowers/`：本机开发会话状态，可选恢复；
- `checksums.sha256`：快照完整性校验；
- `manifest.txt`：文件、提交和排除项清单，不包含密钥内容。

请把整个快照目录复制到加密的外置盘或密码管理的安全文件区。不要把它上传到公开仓库或未加密网盘。`runtime/.env`、`runtime/pat` 和 `runtime/backend-db.sqlite3` 应保持仅本人可读。

复制后在快照目录中运行 `shasum -a 256 -c checksums.sha256`；所有文件都应显示 `OK`。在已克隆的项目仓库中运行 `git bundle verify /path/to/godaddy-reinstall-backup-20260929/git-repo.bundle` 检查离线 Git 包（该命令需要 Git 仓库上下文）。

以下目录没有复制，因为它们可以从锁文件重建：`.venv/`、`frontend/node_modules/`、`frontend/dist/`、`.pytest_cache/`。`.env` 中的 `ACCOUNT_ENCRYPTION_KEY` 必须和 SQLite 中已保存账号的加密密钥保持一致；丢失该密钥后，数据库中的已保存 PAT 无法解密。

## 重装后的恢复顺序

1. 安装 Git、`uv`、Node.js/npm，并完成 GitHub CLI 登录（如需使用 `gh`）。
2. 克隆仓库并进入目录：

   ```bash
   git clone https://github.com/shiyi-log/dns-orchestrator.git
   cd dns-orchestrator
   git switch main
   ```

   如果需要精确恢复快照当时的版本，再按快照 `manifest.txt` 中的 HEAD 检出对应提交。

3. 从快照恢复本机状态。将快照目录替换为实际保存位置：

   ```bash
   cp /path/to/godaddy-reinstall-backup-20260929/runtime/.env .env
   cp /path/to/godaddy-reinstall-backup-20260929/runtime/pat pat
   mkdir -p backend
   cp /path/to/godaddy-reinstall-backup-20260929/runtime/backend-db.sqlite3 backend/db.sqlite3
   chmod 600 .env pat backend/db.sqlite3
   ```

   需要 JetBrains 设置时，再复制 `runtime/.idea/`；`.superpowers/` 只用于恢复本机开发会话，不影响应用运行。

4. 重建依赖并检查数据库：

   ```bash
   uv sync --locked
   cd frontend && npm ci && cd ..
   uv run python backend/manage.py migrate
   uv run python backend/manage.py check
   uv run pytest tests -q
   npm run build --prefix frontend
   ```

5. 启动服务并做本地冒烟检查：

   ```bash
   uv run python backend/manage.py runserver 127.0.0.1:8000
   # 另一个终端：
   cd frontend && npm run dev
   ```

   浏览器访问 `http://localhost:5173`，确认 `/api/health` 返回服务状态；真实 GoDaddy 模式下先确认账号列表和域名读取，再进行任何 DNS 写操作。

## 没有快照时的降级恢复

可以从 `.env.example` 创建演示环境并重新执行 `migrate`。真实 GoDaddy 模式需要重新生成 PAT，并设置新的 `ACCOUNT_ENCRYPTION_KEY`；这不会恢复旧 SQLite 中的账号记录。DNS 记录以 GoDaddy 远端为准，重装不会删除远端记录。

## 恢复与回滚边界

- Git 源码可从 `main` 或 `git-repo.bundle` 恢复；当前提交不会修改远端 DNS。
- `.env`、`pat` 和 SQLite 属于本机敏感状态，只能从受保护快照恢复或重新配置。
- 依赖目录和构建产物可删除后重建，不作为恢复依据。
- 本文不包含任何 PAT、Fernet 密钥、Cookie 或管理员密码。
