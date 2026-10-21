# T00 工程初始化验证记录

日期：2026-10-21。状态：**T00 / M0 按默认原生 PostgreSQL 路径验收完成**。首次初始化时曾因 Compose 容器启动未通过而保持待验收；用户随后明确要求不依赖 Docker，[D10](decisions.md#d10原生数据库为默认docker-compose-改为可选) 将其调整为可选路径，并补充验证了默认配置。原容器失败记录保留，不宣称容器运行通过。

## 交付与边界

- 建立 `apps/web`、单个 `apps/api` Python 工程、默认原生 PostgreSQL 运行路径、可选 Compose、显式配置示例、依赖锁文件与检查入口。
- Alembic `0001_baseline` 只建立版本历史，没有业务表；业务领域、worker、模型和规则包未实现。
- 开始时样稿目录已经不存在；移除其失效链接，保留 R01–R13 审阅结论、8 份文档的名称与替代入口、D01–D08 设计决策。
- 初次工程初始化未读取或覆盖用户 `.env`，也未创建 Git 提交、推送或部署；当时工作目录没有 `.git`，无法提供 Git 差异基线。随后按用户要求初始化本地 Git，提交流程见 [Git 工作流](git-workflow.md)；没有执行远程推送或部署。

## 版本与兼容依据

实测运行时：Windows、Node 24.12.0、npm 11.6.2、Python 3.13.5、uv 0.12.3。

- [Next.js 安装要求](https://nextjs.org/docs/app/getting-started/installation)：Node 最低 20.9、TypeScript 最低 5.1；选定运行时与 TypeScript 5.9.3 高于要求。npm registry 核实 Next.js 16.4.2 的 React peer 范围接受 React 19。Web 检查使用 Biome 2.5.15，避免 Next.js ESLint 工具链当时经 braces 引入的未修复漏洞；不使用强制审计降级。
- [FastAPI 配置](https://fastapi.tiangolo.com/advanced/settings/)：使用 Pydantic Settings。PyPI 核实 FastAPI 0.156.4、pydantic-settings 2.16.1、SQLAlchemy 2.1.5、Alembic 1.20.0、psycopg 3.3.6 的 Python 要求均接受 Python 3.13；uv 解算锁文件确认传递依赖兼容。按已安装 Starlette 1.9.0 的 TestClient 要求选用 httpx2 2.15.1，消除旧 httpx 的弃用告警；最终测试启用 `-W error`。
- [PostgreSQL 版本支持](https://www.postgresql.org/support/versioning/)与 [Windows 官方下载入口](https://www.postgresql.org/download/windows/)：选用 17.11，容器固定 `postgres:17.11-bookworm` 并按 Docker Hub 官方镜像元数据锁定多平台清单摘要 `sha256:3645570cccdfa447589da9f57dd740faa29b30938e861289a5574b6ca6b03826`；本机验证使用官方入口指向的 EDB Windows 二进制包。它不替代容器运行验证。
- [Alembic 教程](https://alembic.sqlalchemy.org/en/latest/tutorial.html)：迁移与应用使用同一 Python 环境，从配置取得数据库 URL。

精确版本和传递依赖分别保存在 `apps/web/package-lock.json` 和 `apps/api/uv.lock`；原生平台产物由安装工具按平台选取，不提交 node_modules、虚拟环境或临时数据库。

## 实际检查

以下命令均已实际执行。Web 命令从根目录执行（或在 `apps/web` 使用等价脚本）；Python 命令在 `apps/api` 执行。

| 检查 | 实际命令 / 条件 | 结果 |
| --- | --- | --- |
| Web 锁文件重装 | `npm --prefix apps/web ci` | 从锁文件重新安装成功，审计 0 漏洞 |
| Web 格式、静态、类型 | `npm --prefix apps/web run check` | Biome 检查 9 个文件通过；Next 类型生成与 `tsc --noEmit` 通过 |
| Web 生产构建 | `npm --prefix apps/web run build` | Next.js 16.4.2 构建成功，首页静态生成成功 |
| Web 开发启动 | `npm --prefix apps/web run dev` | 回环地址 3000 端口启动成功 |
| Web 生产启动 | `npm --prefix apps/web run start` | 本地生产服务器启动成功 |
| Web HTTP 冒烟 | 两种启动方式下分别运行 `npm --prefix apps/web run smoke` | 均为 HTTP 200，页面包含中文文档、main 与 NovelOS |
| Python 锁文件 | `uv lock --check`、`uv sync --locked` | 解算一致、安装成功；另以 `UV_PROJECT_ENVIRONMENT` 指向新的 `.local/api-clean` 并使用 `--link-mode copy` 重装成功 |
| Python 格式 | `uv run --locked --no-env-file ruff format --check .` | 10 个 Python 文件通过 |
| Python 静态 | `uv run --locked --no-env-file ruff check .`、`uv run --locked --no-env-file mypy` | 全部通过，mypy 检查 10 个源文件无问题 |
| 默认最小测试 | `uv run --locked --no-env-file pytest -W error` | 9 passed，1 skipped；跳过的是未指定专用数据库的集成测试 |
| 真实 PostgreSQL 集成 | 设置 `NOVELOS_TEST_DATABASE_URL` 指向新的空测试库后执行 `uv run --locked --no-env-file pytest -W error` | 10 passed；在新虚拟环境与另一个新测试库中再次执行亦为 10 passed，无告警 |
| 显式配置示例 | `uv run --locked --env-file ../../.env.example` 下实例化 Settings 并执行默认 pytest | 环境名与 CORS 列表正确；9 passed、1 按预期跳过 |
| 初始迁移 | 对 `novelos_t00` 执行 `alembic upgrade head`、`alembic current`、`alembic check` | 修订为 `0001_baseline (head)`，无新迁移操作 |
| Compose 配置 | `.local/docker-compose.exe --env-file .env.example -f infrastructure/compose.yaml config --quiet`，Compose v2.39.4 | 通过；最终镜像摘要与配置示例修正后重验通过 |
| Compose 容器启动 | 同一工具执行 `up -d --wait` | 失败：`//./pipe/docker_engine` 不存在，本机没有可用 Docker 引擎；没有宣称容器启动成功 |
| 文档引用 | 标准库脚本检查根目录与 `docs/` 的 Markdown 本地文件、标题锚点，并检索样稿路径 | 85 个本地链接与锚点有效，无失效样稿路径；R01–R13 和 D01–D08 保留 |

独立 PostgreSQL 通过 EDB `postgresql-17.11-1-windows-x64-binaries.zip` 运行，`postgres --version` 确认为 17.11；临时集群只监听 `127.0.0.1:55432`，开发验证库 `novelos_t00` 与空的专用集成库分离。API 用运行环境覆盖数据库 URL，没有访问用户 `.env`。集成测试验证首次升级、重复升级、降级、再次升级及 `alembic check`，初始迁移只有版本记录。

HTTP 级验证启动真实 Uvicorn 后执行：正常情况下 `/health/live` 和 `/health/ready` 均为 200；`pg_ctl ... stop` 后就绪为 503、存活仍为 200；`pg_ctl ... start` 后，API 无需重启，就绪恢复为 200。另使用显式 `.env.example` 加运行环境数据库覆盖启动 Uvicorn，两个端点均返回 200。

检查中已修复：数据库查询的 mypy 返回类型、配置示例中 JSON 列表的 dotenv 引号、测试客户端弃用依赖，以及 Next.js 自动生成额外协作文件的行为（`agentRules: false`）。最初 Web ESLint 工具链审计发现的 5 项高危依赖已随改用 Biome 消除，最终 `npm ci` 审计为 0。

## 默认原生路径补验与 Git 初始化

用户调整运行要求后，按 [原生操作说明](local-development.md)新增独立集群 `.local/postgres-dev`，绑定 `127.0.0.1:5432`，不覆盖此前 `.local/pgdata` 的临时验证数据。初始化使用公开本地示例密码和临时密码文件替代手工输入，没有读取用户 `.env`。

- 原生 PostgreSQL 17.11 初始化、启动、`pg_ctl status`、`pg_isready` 和 `psql SELECT 1` 均通过；开发库 `novelos` 与空测试库 `novelos_test` 分离。
- 不覆盖数据库 URL，直接执行 README 的 `uv run --locked --env-file ../../.env.example alembic upgrade head`、`current`、`check`：得到 `0001_baseline (head)`，无结构漂移。
- 设置专用测试库 URL 后执行 `uv run --locked --env-file ../../.env.example pytest -W error`：**10 passed**，无告警。
- 按相同配置启动真实 Uvicorn：存活与就绪均为 200；停止 `.local/postgres-dev` 后就绪 503、存活 200；原生数据库重启后，API 不重启即可恢复就绪 200。
- 用户要求初始化 Git 后建立本地 `main` 分支，按明确选择只设置仓库级 GitHub 名称和 noreply 邮箱，保留全局公司身份；检查忽略规则，未暂存或读取 `.env` 及 `.local/`。远程仓库尚未创建，不配置猜测的 origin，不执行远程推送。Git Credential Manager 已存在；SSH 到 GitHub 22 端口测试超时，不能据此判断 HTTPS 权限。
- 更新文档后，101 个本地 Markdown 链接与标题锚点通过检查；README、本地数据库和 Git 工作流中的 23 段 PowerShell 命令通过语法解析。未改动应用实现或依赖，因此沿用前述 Web 构建和静态检查证据，不把它们写成本次重新执行。

上述默认原生路径补验与前述锁文件重装、Web 和 Python 检查共同满足更新后的 T00 / M0 验收条件；这来自用户明确调整的契约及实际检查，不是把原来的容器失败改成成功。

## 限制与下一步

本机未预装 Docker 引擎，**可选 Compose 路径的镜像拉取、数据卷与健康检查启动仍待实测**；它不阻塞默认原生路径验收。数据库停止/恢复通过的是原生 PostgreSQL，未冒充容器重启测试。Linux / macOS 尚未运行。没有任何小说业务、模型网关、worker 或真实模型验证。

验证用 Web、API 和 PostgreSQL 进程已停止。二进制、临时数据库与额外虚拟环境位于已忽略的 `.local/`；安装产物也已忽略，不作为源文件交付。运行指南见根目录 README。

下一业务任务为 **T01：项目生命周期与隔离**，本轮不扩展。首次基线提交完成后提醒用户创建目标远程仓库并推送；将来选择 Compose 时，再单独执行容器启动与数据卷验证。
