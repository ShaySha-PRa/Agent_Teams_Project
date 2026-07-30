# Agent 智能文档审核系统 — 部署与发布规范 v1.0

> **版本**: v1.0
> **发布日期**: 2026-07-30
> **适用版本**: v1.4.x
> **文档性质**: 交付封装 — 覆盖 Docker 部署、环境变量、启动顺序、异常排查

---

## 目录

1. [项目架构概览](#一项目架构概览)
2. [环境变量配置](#二环境变量配置)
3. [本地开发环境部署](#三本地开发环境部署)
4. [Docker 容器化部署](#四docker-容器化部署)
5. [Docker Compose 一键部署](#五docker-compose-一键部署)
6. [外部依赖服务](#六外部依赖服务)
7. [服务启动顺序与健康检查](#七服务启动顺序与健康检查)
8. [常见异常与排查](#八常见异常与排查)
9. [生产环境检查清单](#九生产环境检查清单)
10. [附录](#十附录)

---

## 一、项目架构概览

```
┌─────────────────────────────────────────────────────┐
│                    用户浏览器                          │
│                  http://localhost:3000                │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              Frontend (Nginx + React SPA)             │
│              Port: 3000                               │
│              /api/* → proxy → backend:8000            │
└──────────────────────┬──────────────────────────────┘
                       │ /api/*
                       ▼
┌─────────────────────────────────────────────────────┐
│              Backend (FastAPI + Uvicorn)              │
│              Port: 8000                               │
│              ├── SQLite (dev) / PostgreSQL (prod)      │
│              ├── LangGraph Workflow                    │
│              └── ReportLab PDF Engine                  │
└──────────────────────┬──────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
      ┌──────────┐        ┌──────────────┐
      │ DeepSeek  │        │   PostgreSQL   │
      │   API     │        │   (可选, 生产)  │
      └──────────┘        └──────────────┘
```

| 组件 | 技术栈 | 端口 | 说明 |
|------|--------|:--:|------|
| 前端 | React 18 + Vite + Nginx | 3000 | SPA，Nginx 反向代理 `/api/` 到后端 |
| 后端 | FastAPI + Uvicorn + SQLAlchemy | 8000 | REST API + SSE 事件流 |
| 数据库 | SQLite (dev) / PostgreSQL (prod) | — | SQLite 适合开发，PG 适合生产 |
| AI 引擎 | DeepSeek (ChatOpenAI 兼容) | — | 外部 API，需 API Key |

---

## 二、环境变量配置

### 2.1 完整环境变量清单

| 变量名 | 必填 | 默认值 | 说明 |
|--------|:--:|------|------|
| `APP_NAME` | 否 | `Agent Document Review` | 应用名称 |
| `APP_ENV` | 否 | `development` | 运行环境：`development` / `staging` / `production` |
| `APP_PORT` | 否 | `8000` | 后端监听端口 |
| `DEBUG` | 否 | `true` | 调试模式；生产必须 `false` |
| **`DATABASE_URL`** | 否 | `sqlite+aiosqlite:///./docreview.db` | 数据库连接串。开发用 SQLite，生产必须换 PostgreSQL |
| **`DEEPSEEK_API_KEY`** | **是** | `""` | DeepSeek API Key。空值时 LangGraph Agent 无法调用 |
| `DEEPSEEK_MODEL` | 否 | `deepseek-chat` | DeepSeek 模型名称 |
| `DEEPSEEK_BASE_URL` | 否 | `https://api.deepseek.com/v1` | DeepSeek API 地址 |
| **`JWT_SECRET_KEY`** | **是** | `dev-secret-...` | JWT 签名密钥。生产环境**必须**更换为随机字符串 |
| `JWT_ALGORITHM` | 否 | `HS256` | JWT 签名算法 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 否 | `1440` | Token 过期时间（分钟） |
| `STORAGE_BACKEND` | 否 | `local` | 文件存储后端：`local` / `s3` |
| `STORAGE_LOCAL_PATH` | 否 | `./storage` | 本地存储路径 |
| `MAX_FILE_SIZE_MB` | 否 | `50` | 文件大小上限（MB） |
| `MAX_PAGE_COUNT` | 否 | `200` | PDF 最大页数 |
| `CORS_ORIGINS` | 否 | `["http://localhost:3000"]` | 允许跨域的来源列表 |

### 2.2 .env 文件示例

在项目根目录创建 `.env` 文件：

```bash
# 最小生产配置
APP_ENV=production
DEBUG=false
DEEPSEEK_API_KEY=sk-your-real-key
JWT_SECRET_KEY=使用随机生成器生成一个长字符串
CORS_ORIGINS=["https://your-domain.com"]
```

---

## 三、本地开发环境部署

### 3.1 环境要求

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | >= 3.12 | 后端运行时 |
| Node.js | >= 18 | 前端构建 |
| npm | >= 9 | 包管理器 |
| Git | >= 2.x | 版本控制 |

### 3.2 第一步：克隆项目

```bash
git clone https://github.com/ShaySha-PRa/Agent_Teams_Project.git
cd Agent_Teams_Project
```

### 3.3 第二步：启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
source .venv/Scripts/activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install fastapi "uvicorn[standard]" sse-starlette python-multipart \
    "sqlalchemy[asyncio]>=2.0.35" aiosqlite pydantic pydantic-settings \
    python-dotenv "python-jose[cryptography]" reportlab \
    langchain-openai langchain langgraph

# 启动 (从 backend/src/ 目录启动)
cd src
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

后端启动成功标志：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 3.4 第三步：启动前端

```bash
# 新终端，从项目根目录进入
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动成功标志：
```
VITE v5.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

### 3.5 第四步：验证

浏览器打开 `http://localhost:3000/dashboard`，应能看到工作台页面。

### 3.6 快速验证命令

```bash
# 检查后端
curl -s -H "Authorization: Bearer dev-token" http://localhost:8000/api/v1/dashboard/stats

# 检查前端
curl -s http://localhost:3000/
```

---

## 四、Docker 容器化部署

### 4.1 构建后端镜像

```bash
# 从项目根目录执行
docker build -t agent-review-backend:latest -f backend/Dockerfile .
```

### 4.2 构建前端镜像

```bash
docker build -t agent-review-frontend:latest -f frontend/Dockerfile .
```

### 4.3 启动后端容器

```bash
docker run -d \
    --name agent-review-backend \
    -p 8001:8000 \
    -v agent_data:/app/data \
    -v agent_storage:/app/storage \
    -e DEEPSEEK_API_KEY=sk-your-key \
    -e JWT_SECRET_KEY=your-production-secret \
    agent-review-backend:latest
```

### 4.4 启动前端容器

```bash
docker run -d \
    --name agent-review-frontend \
    -p 3000:3000 \
    --link agent-review-backend:backend \
    agent-review-frontend:latest
```

### 4.5 查看容器状态

```bash
docker ps --filter "name=agent-review"
docker logs agent-review-backend
docker logs agent-review-frontend
```

### 4.6 停止与清理

```bash
docker stop agent-review-frontend agent-review-backend
docker rm agent-review-frontend agent-review-backend
docker volume rm agent_data agent_storage
```

---

## 五、Docker Compose 一键部署

### 5.1 前置准备

1. 安装 [Docker](https://docs.docker.com/get-docker/) 和 [Docker Compose](https://docs.docker.com/compose/install/)
2. 确保 `docker` 和 `docker-compose` 命令可用

### 5.2 启动

```bash
# 从项目根目录执行（docker-compose.yml 所在目录）
docker-compose up -d
```

首次启动会自动构建镜像（约 2-5 分钟），后续启动使用缓存镜像（约 10 秒）。

### 5.3 查看状态

```bash
# 容器状态
docker-compose ps

# 后端日志
docker-compose logs backend

# 前端日志
docker-compose logs frontend

# 实时日志
docker-compose logs -f
```

### 5.4 停止

```bash
# 停止但不删除
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器 + 数据卷
docker-compose down -v
```

### 5.5 环境变量注入

Docker Compose 会自动读取项目根目录的 `.env` 文件。创建 `.env` 并填入必需的 Key：

```bash
echo 'DEEPSEEK_API_KEY=sk-your-real-key' > .env
echo 'JWT_SECRET_KEY=your-random-secret-string' >> .env
```

或者直接在 `docker-compose.yml` 的 `environment` 段落中修改。

### 5.6 验证服务

```bash
# 后端健康检查
curl -s -H "Authorization: Bearer dev-token" http://localhost:8001/api/v1/dashboard/stats

# 前端健康检查
curl -s http://localhost:3000/
```

---

## 六、外部依赖服务

### 6.1 DeepSeek API（必需 - 生产）

| 项 | 值 |
|------|------|
| 用途 | LLM Agent 调用（条款提取、风险识别、合规检查、报告生成） |
| API 地址 | `https://api.deepseek.com/v1` |
| 鉴权方式 | `Authorization: Bearer <API_KEY>` |
| 获取 API Key | [DeepSeek 开放平台](https://platform.deepseek.com/) |
| 环境变量 | `DEEPSEEK_API_KEY` |
| 故障时影响 | AI 审核功能不可用；上传、解析、审批仍可使用 Mock 数据 |

### 6.2 PostgreSQL（可选 - 生产）

| 项 | 值 |
|------|------|
| 用途 | 替代 SQLite 作为生产数据库 |
| 版本要求 | >= 14 |
| 默认端口 | 5432 |
| 连接串格式 | `postgresql+asyncpg://user:password@host:5432/dbname` |
| 环境变量 | `DATABASE_URL` |

**PostgreSQL 启用方式**：修改 `.env` 或 docker-compose.yml 中的 `DATABASE_URL` 为 PG 连接串即可，应用会自动创建表。

### 6.3 S3 兼容存储（可选）

| 项 | 值 |
|------|------|
| 用途 | 替代本地文件系统存储上传的文档 |
| 需设置 | `STORAGE_BACKEND=s3` + 对应的 S3 凭证环境变量 |

---

## 七、服务启动顺序与健康检查

### 7.1 正确的启动顺序

```
1. 外部依赖服务 (DeepSeek API、PostgreSQL、S3)
       │
       ▼
2. Backend (FastAPI)
       │  等待 /api/v1/dashboard/stats 返回 200
       ▼
3. Frontend (Nginx)
```

**Docker Compose 已通过 `depends_on` + `condition: service_healthy` 自动保证此顺序。**

### 7.2 健康检查端点

| 服务 | 检查地址 | 预期返回 | 超时 |
|------|---------|---------|:--:|
| Backend | `GET /api/v1/dashboard/stats` | `{"code":0, ...}` | 5s |
| Frontend | `GET /` | HTTP 200 | 5s |

### 7.3 启动超时与重试

| 项目 | 值 |
|------|------|
| 后端就绪等待 | 最多 30s |
| 后端健康检查间隔 | 30s |
| 失败重试次数 | 3 次 |
| 前端依赖后端就绪 | 是（`depends_on` healthcheck） |

---

## 八、常见异常与排查

### 8.1 后端无法启动

**现象**：`docker-compose up` 后 backend 容器反复重启

**排查步骤**：

```bash
# 1. 查看后端日志
docker-compose logs backend | tail -50

# 2. 常见错误
```

| 错误信息 | 原因 | 解决 |
|---------|------|------|
| `ModuleNotFoundError: No module named 'core'` | 启动路径错误 | 确保从 `backend/src/` 目录启动，或 `uvicorn src.main:app` |
| `sqlite3.OperationalError: no such table` | 数据库未初始化 | 应用启动时自动创建表，检查 `DATABASE_URL` 路径是否有写入权限 |
| `ConnectionRefusedError` on PostgreSQL | PG 未启动或连接串错误 | 检查 `DATABASE_URL`，确保 PG 已启动，网络可达 |
| `port 8000 already in use` | 端口冲突 | 修改 `APP_PORT` 或 `docker-compose.yml` 的 ports 映射 |
| SSL/TLS handshake failed | pip 安装依赖网络问题 | 配置镜像源或代理 |

### 8.2 前端无法加载数据

**现象**：浏览器访问 `localhost:3000`，Dashboard 页面白屏或显示错误

**排查步骤**：

```bash
# 1. 确认后端是否正常
curl -s -H "Authorization: Bearer dev-token" http://localhost:8001/api/v1/dashboard/stats

# 2. 确认前端代理是否正常
curl -s http://localhost:3000/api/v1/dashboard/stats
```

| 错误信息 | 原因 | 解决 |
|---------|------|------|
| `Authorization header required` | 前端请求无 Token | 检查 `frontend/src/api/client.ts` 中 `localStorage.getItem('auth_token')` 的逻辑 |
| `Unexpected end of JSON input` | 代理指向错误的端口 | 检查 `vite.config.ts`（开发）或 `nginx.conf`（Docker）的 proxy target |
| `CORS error` | 跨域策略不对 | 检查 `CORS_ORIGINS` 环境变量是否包含前端地址 |
| 页面白屏 | JS 加载失败 | 打开浏览器 DevTools → Console 查看错误 |

### 8.3 AI 审核功能不工作

**现象**：上传文档后，点击"开始解析"或"启动审核"无响应

| 原因 | 排查方法 | 解决 |
|------|---------|------|
| `DEEPSEEK_API_KEY` 未设置或无效 | `echo $DEEPSEEK_API_KEY` | 设置有效的 API Key |
| DeepSeek API 返回 401/403 | 查看后端日志 | 检查 API Key 是否有效、余额是否充足 |
| LangGraph workflow 抛出异常 | `docker-compose logs backend | grep -i error` | 检查后端日志 |

> **MVP 说明**：v1.4.x 版本的 AI 审核使用 Mock 数据，即使不配置 DeepSeek API Key，审批工作流也能正常运行。

### 8.4 PDF 导出文件损坏

**现象**：点击"导出 PDF 报告"后下载的文件无法打开

| 原因 | 解决 |
|------|------|
| reportlab 字体依赖缺失 | 确认系统有中文字体，或 `reportlab` 正确安装 |
| 磁盘空间不足 | `df -h` 检查磁盘 |
| 报告数据未生成 | 确保文档已完成提交（status=COMPLETED）并已签署 |

### 8.5 数据库连接问题

**现象**：后端报 `sqlite3.OperationalError` 或 `asyncpg` 连接错误

| 数据库类型 | 常见问题 | 解决 |
|-----------|---------|------|
| SQLite | 文件权限不足 | `chmod 777 /app/data/` |
| SQLite | 文件被锁定 | 确保只有一个进程访问 |
| PostgreSQL | 连接超时 | 检查网络、防火墙、PG 监听地址 |
| PostgreSQL | 认证失败 | 检查用户名、密码、`pg_hba.conf` |

### 8.6 Docker 构建失败

| 现象 | 原因 | 解决 |
|------|------|------|
| `COPY failed: file not found` | Docker context 路径不对 | 构建命令从项目根目录执行：`docker build -f backend/Dockerfile .` |
| `npm ci` 失败 | `package-lock.json` 过期 | 本地先 `npm install` 更新 lock 文件 |
| `pip install` 超时 | 网络问题 | 配置 pip 镜像源或增加 `--timeout` |
| 镜像体积过大 | 未使用 multi-stage | 已使用多阶段构建，最终镜像 <300MB |

### 8.7 Docker Compose 端口冲突

**现象**：`Error starting userland proxy: port is already allocated`

| 原因 | 解决 |
|------|------|
| 本地已有进程占用 3000 或 8001 | `netstat -ano | grep 3000` 找到进程并停止 |
| 上次 `docker-compose down` 未完全清理 | `docker-compose down -v && docker-compose up -d` |

---

## 九、生产环境检查清单

部署到生产环境前，逐项确认：

- [ ] `APP_ENV=production` 且 `DEBUG=false`
- [ ] `JWT_SECRET_KEY` 已更换为随机长字符串（≥32 字符）
- [ ] `DEEPSEEK_API_KEY` 已配置且有效
- [ ] `DATABASE_URL` 指向 PostgreSQL（非 SQLite）
- [ ] `CORS_ORIGINS` 只包含生产域名
- [ ] PostgreSQL 数据库已创建且可连接
- [ ] PostgreSQL 备份策略已配置
- [ ] 文件存储后端已选择（本地 / S3）
- [ ] SSL/TLS 证书已配置（HTTPS）
- [ ] 日志收集方案已部署（如 ELK / Loki）
- [ ] 监控告警已配置（如 Prometheus + Grafana）
- [ ] `backend/.env` 和 `.env` 文件已从公开仓库中排除
- [ ] 后端测试已通过（`pytest tests/`）
- [ ] 前端已用生产构建（`npm run build`）

---

## 十、附录

### 10.1 项目目录结构

```
Agent_Teams_Project/
├── docker-compose.yml            # Docker Compose 编排文件
├── .env                           # 环境变量（不提交 Git）
├── backend/
│   ├── Dockerfile                 # 后端 Docker 镜像定义
│   ├── src/                       # 后端源码
│   ├── .env.example               # 环境变量模板
│   └── pyproject.toml
├── frontend/
│   ├── Dockerfile                 # 前端 Docker 镜像定义
│   ├── src/                       # 前端源码
│   └── package.json
├── docs/
│   └── 12_deployment/
│       └── deployment_sec-v1.0.md  # 本文档
└── README.md
```

### 10.2 关键端口映射

| 服务 | 容器端口 | 宿主机端口 | 说明 |
|------|:--:|:--:|------|
| Backend | 8000 | 8001 | FastAPI 主服务 |
| Frontend | 3000 | 3000 | Nginx + React SPA |

### 10.3 快速启动检查脚本

```bash
#!/bin/bash
echo "=== 检查后端 ==="
curl -s -o /dev/null -w "后端状态码: %{http_code}\n" \
    -H "Authorization: Bearer dev-token" \
    http://localhost:8001/api/v1/dashboard/stats

echo "=== 检查前端 ==="
curl -s -o /dev/null -w "前端状态码: %{http_code}\n" http://localhost:3000/

echo "=== 检查 Docker 容器 ==="
docker ps --filter "name=agent-review"
```

### 10.4 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.4.1 | 2026-07-30 | 当前发布版本。32 API 端点，7 页面，HITL 审批工作流 |
| v1.0.0 | 2026-07-29 | 初始 MVP |

---

> **上游文档**:
> - `docs/06_system_architecture/frontend_backend_boundary_spec-v1.0.md` — 前后端边界规范
> - `docs/08_api_specification/api_spec-v1.0.md` — API 规范
> - `../CLAUDE.md` — 项目级 AI 指引
