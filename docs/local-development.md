# 本地 PostgreSQL：原生运行与可选 Compose

默认方式是本机直接运行 Next.js、FastAPI 和 PostgreSQL **17.11**。Docker 在此前方案中只负责下载固定版本的数据库环境、管理数据卷和启动检查；仓库没有应用 Dockerfile，Web/API 不需要打包成镜像。

以下 Windows 便携方式不安装系统服务，数据留在已被 Git 忽略的 `.local/`。也可使用现有 PostgreSQL 服务。不要同时启动两个占用 `127.0.0.1:5432` 的数据库实例。

## 1. 安装或解压

从 [PostgreSQL Windows 官方入口](https://www.postgresql.org/download/windows/)进入 EDB 的二进制下载，选择 PostgreSQL 17.11 Windows x64 ZIP。可复现示例使用 `postgresql-17.11-1-windows-x64-binaries.zip`；其他平台从 [官方下载](https://www.postgresql.org/download/)选择相同数据库版本，其他平台命令尚未实测。

若使用 ZIP，根目录下载并解压；已有 `.local/pgsql/bin` 时跳过，避免覆盖现有工具：

```powershell
New-Item -ItemType Directory -Path .local -Force | Out-Null
curl.exe --fail --location https://get.enterprisedb.com/postgresql/postgresql-17.11-1-windows-x64-binaries.zip --output .local/postgresql-17.11.zip
tar.exe -xf .local/postgresql-17.11.zip -C .local pgsql/bin pgsql/lib pgsql/share
& ./.local/pgsql/bin/postgres.exe --version
```

确认输出为 17.11。项目初始化时已下载过的本机工具可以复用，但 `.local/` 不进入仓库，新的克隆仍需安装或下载数据库。

## 2. 首次初始化和建库

只在 `.local/postgres-dev` **不存在**时初始化；已有集群直接进入启动步骤。不要删除已有数据来重新初始化。

```powershell
& ./.local/pgsql/bin/initdb.exe -D .local/postgres-dev -U novelos --auth=scram-sha-256 --encoding=UTF8 --locale=C -W
```

`-W` 会交互询问数据库密码。若直接使用仓库的公开本地示例，可输入 `.env.example` 中的 `novelos_local_only`；自定义密码则通过后端运行环境设置匹配的 `NOVELOS_DATABASE_URL`，不改写用户现有 `.env`。这里的账号和密码只用于本地开发。

启动并首次创建数据库：

```powershell
& ./.local/pgsql/bin/pg_ctl.exe -D .local/postgres-dev -l .local/postgres-dev.log -o '-h 127.0.0.1 -p 5432' -w start
& ./.local/pgsql/bin/createdb.exe -h 127.0.0.1 -p 5432 -U novelos -W novelos
& ./.local/pgsql/bin/createdb.exe -h 127.0.0.1 -p 5432 -U novelos -W novelos_test
& ./.local/pgsql/bin/psql.exe -h 127.0.0.1 -p 5432 -U novelos -W -d novelos -c 'SELECT 1;'
```

`novelos` 用于开发；`novelos_test` 必须为空、专供迁移往返测试。建库命令只运行一次，数据库已存在时不要重复创建。初始化集群的 `novelos` 为开发集群管理员；公网或多用户部署需要独立账号权限方案，不在本地 T00 范围内。

迁移、API/Web 启动和检查命令见 [根目录 README](../README.md)。默认命令显式加载脱敏 `.env.example`，不会自动加载根目录 `.env`。

## 3. 后续启动、状态和停止

在根目录执行：

```powershell
& ./.local/pgsql/bin/pg_ctl.exe -D .local/postgres-dev -l .local/postgres-dev.log -o '-h 127.0.0.1 -p 5432' -w start
& ./.local/pgsql/bin/pg_ctl.exe -D .local/postgres-dev status
& ./.local/pgsql/bin/pg_isready.exe -h 127.0.0.1 -p 5432
```

停止数据库，保留数据目录：

```powershell
& ./.local/pgsql/bin/pg_ctl.exe -D .local/postgres-dev -m fast -w stop
```

改端口时同时调整 `pg_ctl -o` 中的端口与后端连接 URL；不要停止其他项目的数据库来腾端口。测试断开与恢复时只操作本项目的数据目录。

## 4. 使用已安装的数据库服务

若已有 PostgreSQL 17.11 服务，无需再初始化便携集群。用安装时的管理员账号登录 `psql`，首次执行：

```sql
CREATE ROLE novelos LOGIN;
\password novelos
CREATE DATABASE novelos OWNER novelos;
CREATE DATABASE novelos_test OWNER novelos;
```

`\password` 通过交互输入密码，避免把真实密码写进 SQL 历史。已有角色和数据库时复用或选择独立名称，不重复创建。服务启停由原有安装方式管理，后端连接、Alembic 和测试与便携方式相同。

## 5. 可选 Docker Compose

只有选择容器数据库时才需要 Docker Engine / Docker Desktop 与 Compose 2.20+。它管理 PostgreSQL 容器和数据卷，不打包 Web/API：

```powershell
docker compose --env-file .env.example -f infrastructure/compose.yaml config --quiet
docker compose --env-file .env.example -f infrastructure/compose.yaml up -d --wait
docker compose --env-file .env.example -f infrastructure/compose.yaml exec db createdb -U novelos novelos_test
```

默认会创建开发库 `novelos`；测试库另建。保持 API 运行时，可用 `stop db` 和 `up -d --wait` 检查数据库断开/恢复；使用 `down` 停止并保留卷，不加 `-v`。

Compose 配置及锁定镜像已经校验；本机缺少 Docker 引擎，容器启动没有通过实测。该限制只属于这条可选路径，不作为原生运行路径的验收条件。
