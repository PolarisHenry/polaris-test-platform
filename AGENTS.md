# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目概览

前后端分离的管理平台：**FastAPI** (Python 3.11+) 后端 + **Vue3 / Naive UI / Vite** 前端，融合 RBAC 权限管理、动态路由和 JWT 鉴权。ORM 使用 Tortoise，包管理器用 `uv`（Python）和 `pnpm`（Node）。

## 常用命令

```bash
# 后端（在项目根目录执行）
uv add pyproject.toml          # 安装 Python 依赖
python run.py                  # 启动开发服务器，端口 9999，支持热重载
make lint                      # ruff 检查
make format                    # black + isort 格式化（行宽 120）
make check                     # 格式化空跑 + lint 检查
make test                      # pytest（自动加载 .env 环境变量）
make migrate                   # aerich 生成迁移文件
make upgrade                   # aerich 应用迁移

# 前端（在 web/ 目录执行）
cd web
pnpm i                         # 安装 JS 依赖
pnpm dev                       # Vite 开发服务器
pnpm build                     # 生产构建
pnpm lint                      # eslint 检查
pnpm prettier                  # prettier 格式化

# Docker
docker-compose up -d           # 启动 MySQL + 应用，端口 3100
```

## 后端架构

### 启动流程
`run.py` → `uvicorn` 加载 `app:app` → `app/__init__.py` 中的 `create_app()` → 注册中间件、异常处理器和 `/api` 路由。首次启动时，`lifespan` → `init_data()` 自动创建数据库表、初始化超级管理员（`admin` / `123456`）、默认菜单（系统管理及其子项）、基于路由元数据同步 API 权限列表并为角色分配权限。

### 分层结构

- **`app/api/v1/`** — 路由定义层。按业务域划分（users、roles、menus、apis、depts、auditlog、base），每个域一个子包。路由层很薄，仅调用 controller 方法并返回 `Success`/`SuccessExtra` schema 对象。
- **`app/controllers/`** — 业务逻辑层。每个 controller 继承 `app/core/crud.py` 中的 `CRUDBase[Model, CreateSchema, UpdateSchema]`，提供 `get`、`list`（分页）、`create`、`update`、`remove`。业务特定逻辑（认证、角色分配、密码重置等）写在这一层。
- **`app/models/`** — Tortoise ORM 模型。`admin.py` 定义了 User、Role、Api、Menu、Dept、DeptClosure（部门闭包表）、AuditLog。模型均使用 `BaseModel`（UUID 主键）和 `TimestampMixin`。`enums.py` 定义了 MethodType 和 MenuType 枚举。
- **`app/schemas/`** — Pydantic 模型，用于请求参数校验和响应数据序列化。`base.py` 定义了 `Success`、`Fail`、`SuccessExtra`（分页响应）。
- **`app/core/`** — 框架胶水层：中间件（CORS、后台任务、审计日志）、依赖注入（`AuthControl` 负责 JWT 认证、`PermissionControl` 负责接口级 RBAC）、异常处理器、上下文变量（`CTX_USER_ID`、`CTX_BG_TASKS`）。
- **`app/settings/config.py`** — 所有配置通过 `pydantic-settings` 管理。支持 SQLite（本地开发默认）和 MySQL（Docker/生产环境）。通过 `TORTOISE_ORM.apps.models.default_connection` 切换数据库（当前设为 `"mysql"`）。

### 认证与权限
- JWT 认证：登录接口 `POST /api/v1/base/access_token`，token 通过 `token` 请求头传递。
- `AuthControl.is_authed` 解码 JWT，设置 `CTX_USER_ID` 上下文变量，返回 User 对象。开发环境下 `token: "dev"` 可跳过真实认证。
- `PermissionControl.has_permission` 检查当前用户角色的 API 列表中是否包含匹配的 `(method, path)` 组合。超级管理员跳过所有权限检查。
- 前端通过 `v-permission="get/api/v1/user/list"` 指令控制按钮/元素的显隐。

### 审计日志
`HttpAuditLogMiddleware` 将每次 HTTP 请求（方法、路径、状态码、响应时间、用户、请求参数、响应体）记录到 `AuditLog` 模型。排除路径：`/api/v1/base/access_token`、`/docs`、`/openapi.json`。

### 后台任务
`BgTasks` 通过上下文变量封装 Starlette 的 `BackgroundTasks`。每个请求创建独立实例，在响应返回后执行任务。

## 前端架构

- **路由**（`web/src/router/`）：`basicRoutes`（登录、工作台、个人资料、错误页面）是静态的。`addDynamicRoutes()` 从 `GET /api/v1/base/usermenu` 获取用户菜单树，构建 Vue Router 路由——父路由使用 `Layout` 组件，子路由通过 `vueModules`（Vite glob import `src/views/**/index.vue`）懒加载视图组件。路由守卫检查认证状态。
- **状态管理**（`web/src/store/modules/`）：Pinia stores —— `user`（用户信息、登录/登出）、`permission`（动态路由 + 可访问 API 列表）、`tags`（标签页历史）、`app`（主题、侧边栏折叠状态）。
- **HTTP 请求**（`web/src/utils/http/`）：Axios 实例，拦截器自动附加 `token` 请求头，处理 401 响应跳转登录页。
- **通用组件**：`CrudTable` / `CrudModal`（`components/table/`）提供可复用的 CRUD 脚手架。`QueryBar` / `QueryBarItem` 处理搜索表单。`AppPage` / `CommonPage` 是页面布局包装组件。
- **国际化**：vue-i18n，语言文件在 `web/i18n/messages/`（`cn.json`、`en.json`）。

## 数据库

使用 Tortoise ORM + **Aerich** 管理数据库迁移。`TORTOISE_ORM` 配置支持多种数据库后端，通过 `default_connection` 设置当前使用的数据库。Docker 环境使用 MySQL，本地开发可使用 SQLite。

```bash
# 模型变更后：
make migrate    # 在 ./migrations/ 中生成迁移文件
make upgrade    # 应用迁移
make clean-db   # 删除迁移文件夹和 db.sqlite3（开发环境重置）
```

## Docker 部署

多阶段构建 Dockerfile：先在 Node 镜像中构建前端，然后在 Python 镜像中通过 nginx + uvicorn 提供服务。`docker-compose.yml` 启动 MySQL 8.0 + 应用，端口 `:3100`。

## 注意事项

- Python 和 JS 的代码行宽均设为 120。
- `settings.config` 中的 `SECRET_KEY` 是硬编码的——生产环境需要替换。
- `AuthControl` 中存在 `token: "dev"` 的开发绕过逻辑，生产环境应移除。
- API 权限数据通过 `POST /api/v1/apis/refresh` 自动刷新，该接口扫描所有已注册的 FastAPI 路由并同步到 `Api` 表用于权限管理。
