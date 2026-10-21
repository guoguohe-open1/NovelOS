# NovelOS · 小说大王

面向个人作者的 AI 长篇小说创作工作台。AI 协助规划、写作与审阅，作者决定哪些内容成为正式剧情。

当前 **T00 已按原生运行路径验收完成**：Next.js 空页面、FastAPI 配置与健康检查、原生 PostgreSQL 和 Alembic 基线迁移可运行。业务任务 T01–T10 均未开始；实际结果与可选容器路径限制见 [T00 验证记录](docs/t00-validation.md)。历史样稿已退出仓库，审阅结论与设计决策继续保留，`docs/` 是唯一设计基线。

第一阶段聚焦玄幻题材和单章闭环：创建小说、维护设定与大纲、生成候选章节、人工修改与验收、同步正式记忆、导出正文。10 万字是后续长篇实验的验收规模；百万字是远期目标。

| 入口 | 用途 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 仓库协作规则与实现约束 |
| [文档导航](docs/README.md) | 阅读路径、权威文档与术语 |
| [产品范围](docs/product.md) | 用户任务、MVP 边界和成功条件 |
| [实施计划](docs/implementation-plan.md) | 有依赖和验收标准的开发任务 |
| [样稿审阅](docs/sample-review.md) | 8 份原始资料的问题、处理方式和覆盖关系 |
| [本地数据库运行](docs/local-development.md) | 原生 PostgreSQL 默认路径及可选 Compose |
| [Git 工作流](docs/git-workflow.md) | 提交身份、验证后提交、首次推送与后续同步 |

## 环境与安装

基准环境为 Node.js **24.12.0**、npm **11.6.2**、Python **3.13.5**、uv **0.12.3** 和 PostgreSQL **17.11**。默认直接运行 Web、API 和数据库，**不需要 Docker 或应用镜像**。Node 与 Python 版本分别记录在 [.node-version](.node-version) 和 [apps/api/.python-version](apps/api/.python-version)。Windows、Linux、macOS 使用相同锁文件；本轮实际验证的平台是 Windows，其他平台尚未实测。

Web 使用 Next.js 16.4.2、React 19.3.1、TypeScript 5.9.3；后端使用 FastAPI 0.156.4、SQLAlchemy 2.1.5、psycopg 3.3.6、Alembic 1.20.0。完整依赖以 [package-lock.json](apps/web/package-lock.json)、[uv.lock](apps/api/uv.lock) 为准。版本兼容依据与检查结果见验证记录。

在仓库根目录执行：

```powershell
npm --prefix apps/web ci
Set-Location apps/api
uv sync --locked
Set-Location ../..
```

后续更新依赖需要有意更新清单和锁文件；日常安装继续使用 `npm ci` 和 `uv sync --locked`。

## 数据库与迁移

本地示例只含公开的开发账号，服务默认绑定回环地址。以下命令显式使用 [.env.example](.env.example)，不需要复制或改写现有 `.env`。API 的配置类不自动加载 dotenv；`uv run --env-file` 负责显式加载文件。Shell 中已设置的同名变量优先。修改数据库端口或账号时，让 Compose 配置与 `NOVELOS_DATABASE_URL` 保持一致；实际密码不要写进文档或前端。

首次按 [本地数据库运行](docs/local-development.md) 安装或解压 PostgreSQL、初始化集群并创建 `novelos` 数据库。下例使用该文档的原生便携目录，在根目录启动数据库；已有系统服务时使用对应的服务启动方式：

```powershell
& ./.local/pgsql/bin/pg_ctl.exe -D .local/postgres-dev -l .local/postgres-dev.log -o '-h 127.0.0.1 -p 5432' -w start
& ./.local/pgsql/bin/pg_isready.exe -h 127.0.0.1 -p 5432
```

在后端目录执行迁移；启动 API 不会自动迁移：

```powershell
Set-Location apps/api
uv run --locked --env-file ../../.env.example alembic upgrade head
uv run --locked --env-file ../../.env.example alembic current
uv run --locked --env-file ../../.env.example alembic check
```

初始修订为 `0001_baseline`，只建立 Alembic 版本记录，没有小说业务表。它的 `upgrade` / `downgrade` 没有业务数据变换；`alembic downgrade base` 清除版本行，版本表仍可保留；之后可重新 `upgrade head`，无业务数据需要恢复。后续任务新增表时必须附迁移和恢复说明。

也可以使用现有的原生 PostgreSQL 服务，通过运行环境设置 `NOVELOS_DATABASE_URL`，使用 `uv run --locked --no-env-file ...` 执行同样的迁移与启动命令。不能用 SQLite 替代 PostgreSQL 验收。

Docker Compose 只提供可选的 PostgreSQL 容器，不打包 Web/API。选择该方式才需要 Docker Engine / Docker Desktop 和 Compose 2.20+；命令见本地数据库运行文档。原生运行不依赖容器验证。

## 启动空应用

终端一，在后端目录：

```powershell
uv run --locked --env-file ../../.env.example uvicorn novelos.api.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

终端二，在仓库根目录：

```powershell
npm --prefix apps/web run dev
```

访问 Web：<http://127.0.0.1:3000>；API 文档：<http://127.0.0.1:8000/docs>。当前 Web 是独立空页面，没有业务接口调用。

| 端点 | 响应含义 |
| --- | --- |
| `GET /health/live` | 进程存活：`200 {"status":"ok"}`，不依赖数据库 |
| `GET /health/ready` | 实际数据库查询成功：`200 {"status":"ready"}`；不可用：`503 {"status":"not_ready"}` |

健康端点是基础设施接口，不使用未来业务接口的 `/api/v1` 成功封装。就绪检查只确认数据库可查询，迁移状态通过 `alembic current` / `alembic check` 单独验证。数据库断开不应使存活检查失败。

Ctrl+C 停止 Web/API。便携数据库在根目录执行以下命令停止，数据目录保留：

```powershell
& ./.local/pgsql/bin/pg_ctl.exe -D .local/postgres-dev -m fast -w stop
```

## 检查与最小测试

在根目录执行 Web 格式、Biome 静态检查、类型检查和生产构建：

```powershell
npm --prefix apps/web run check
npm --prefix apps/web run build
```

在后端目录执行 Python 格式、静态检查和最小测试：

```powershell
uv lock --check
uv run --locked --no-env-file ruff format --check .
uv run --locked --no-env-file ruff check .
uv run --locked --no-env-file mypy
uv run --locked --no-env-file pytest
```

默认测试实际连接一个不可用的本地端口，检查数据库故障时存活仍成功、就绪返回 503，以及配置校验、显式来源允许和敏感错误不外泄。没有指定临时数据库时，PostgreSQL 集成测试明确跳过。

迁移往返测试只允许使用**空的专用测试数据库**。在根目录创建独立数据库（与开发库分离）：

```powershell
& ./.local/pgsql/bin/createdb.exe -h 127.0.0.1 -p 5432 -U novelos -W novelos_test
Set-Location apps/api
$env:NOVELOS_TEST_DATABASE_URL = 'postgresql+psycopg://novelos:novelos_local_only@127.0.0.1:5432/novelos_test'
uv run --locked --no-env-file pytest -m integration
Remove-Item Env:NOVELOS_TEST_DATABASE_URL
```

集成测试验证首次迁移、重复升级、真实数据库就绪、降级、再升级及元数据无漂移；测试后数据库留在 head。重跑前使用另一个空测试数据库，或明确删除并重建专用测试库，勿指向开发数据。

已启动 Web/API 时进行 HTTP 检查：

```powershell
npm --prefix apps/web run smoke
curl.exe --fail http://127.0.0.1:8000/health/live
curl.exe --fail http://127.0.0.1:8000/health/ready
```

验证数据库断开与恢复（根目录；测试时保持 API 启动）：

```powershell
& ./.local/pgsql/bin/pg_ctl.exe -D .local/postgres-dev -m fast -w stop
curl.exe -i http://127.0.0.1:8000/health/ready
curl.exe --fail http://127.0.0.1:8000/health/live
& ./.local/pgsql/bin/pg_ctl.exe -D .local/postgres-dev -l .local/postgres-dev.log -o '-h 127.0.0.1 -p 5432' -w start
curl.exe --fail http://127.0.0.1:8000/health/ready
```

预期依次为 503、200、恢复后 200。测试不调用模型；模型网关、worker、小说表与正式记忆都属于后续任务。任务状态见实施计划；下一业务任务为 [T01：项目生命周期与隔离](docs/implementation-plan.md#t01项目生命周期与隔离)。

本地 Git 已初始化为 `main`，`origin` 已配置为 [guoguohe-open1/NovelOS](https://github.com/guoguohe-open1/NovelOS)。提交与首次远程同步按 [Git 工作流](docs/git-workflow.md) 执行；提交署名、连接器权限与本机 Git 认证分开判断，实际推送由用户执行。
