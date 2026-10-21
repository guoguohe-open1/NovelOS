# HTTP API 契约

状态：MVP 业务 API 的待实现契约。T00 仅实现基础设施健康端点，见下节；业务实现后以服务生成的 OpenAPI 描述精确类型，并用契约测试防止与本文漂移。

## T00 基础设施端点（已实现）

`GET /health/live` 返回 `200 {"status":"ok"}`，不访问数据库。`GET /health/ready` 实际查询 PostgreSQL，成功返回 `200 {"status":"ready"}`，失败返回 `503 {"status":"not_ready"}`，不暴露连接信息。就绪检查不替代迁移验证；启动与迁移分离。

这些端点不使用 `/api/v1`、业务成功封装或业务错误封装。当前只允许配置中的明确来源进行 GET 跨域访问；未来业务写接口需按架构补齐来源与 JSON 校验，不因健康接口已有 CORS 而视为完成。

## 1. 通用约定

- 基础路径 `/api/v1`，项目内业务资源全部置于 `/novels/{novel_id}` 下；项目列表/创建及只读能力发现使用全局路径。
- 请求/响应 JSON，字段 `snake_case`；UUID 字符串，时间为 UTC 的 ISO 8601 字符串。
- 成功响应为 `{"data": ...}`；列表为 `{"data":{"items":[],"next_cursor":null}}`。游标分页排序稳定，默认 20、上限 100，非法游标返回 `422`。
- 新建普通资源返回 `201`，异步任务返回 `202`，更新与决策操作返回 `200`。创建响应含资源 ID 和读取位置；响应头 `X-Request-ID` 用于排查问题。
- 所有 `POST` / `PATCH` 都必须携带 `Idempotency-Key`；相同作用域、相同键与相同规范化请求返回首次的状态/结果，不重复创建资源、任务或模型请求。相同键不同请求返回 `409 idempotency_conflict`。作用域至少包括项目、方法和规范化路由，创建项目则用全局操作作用域。
- 幂等记录与业务写入在同事务提交；并发重复请求由唯一约束协调，不能先发模型再记录幂等。
- 正式剧情写入携带 `expected_canon_revision`；草稿写入携带 `base_version_id`。运行与提案另保留创建时的基线，不能只信任客户端提供的新修订号。
- MVP 采用轮询获取任务进度，不提供未经实现的 SSE/WebSocket 承诺；正文候选通过版本资源读取，不在每次任务轮询中返回全文。

## 2. 资源与端点

表中以 `/api/v1` 开头的路径为完整路径，其余路径相对 `/api/v1/novels/{novel_id}`。

| 方法 | 路径 | 主要行为/并发条件 |
| --- | --- | --- |
| GET | `/api/v1/capabilities` | 可用规则包版本、模型配置名/是否为 Fake/是否已配置、支持能力与预算上限；不返回密钥或供应商连接信息 |
| GET / POST | `/api/v1/novels` | 列表 / 创建项目；创建固定规则包版本 |
| GET / PATCH | `/api/v1/novels/{novel_id}` | 读取 / 更新标题、创意、风格或归档状态；PATCH 需预期正式修订，禁止修改规则包 |
| GET / POST | `/volumes` | 列表 / 新建卷，写入需预期正式修订 |
| PATCH | `/volumes/{volume_id}` | 修改卷目标等规划；有历史影响时需显式确认 |
| GET / POST | `/chapters` | 按全局章序列出 / 创建下一章，写入需预期正式修订 |
| GET / PATCH | `/chapters/{chapter_id}` | 读详情 / 修改标题或大纲；大纲更改校验正式修订及历史影响 |
| GET / POST | `/assets` | 按类型列出 / 创建有 schema 的正式资产 |
| GET / PATCH | `/assets/{asset_id}` | 读取 / 创建资产新版本；需预期正式修订与 `base_asset_version_id` |
| GET | `/assets/{asset_id}/versions` | 按修订号读取历史；明确包含已失效的来源版本 |
| POST | `/chapters/{chapter_id}/drafts` | 保存人工正文为新版本，移动草稿指针，检查 `base_version_id` |
| GET | `/chapters/{chapter_id}/versions` | 版本列表，区分作者、任务、草稿/正式/候选引用 |
| GET | `/chapters/{chapter_id}/versions/{version_id}` | 读取不可变正文和来源元数据 |
| POST / GET | `/runs` | 提交异步任务 / 查询任务列表，支持状态筛选 |
| GET | `/runs/{run_id}` | 状态、当前步骤、尝试摘要、用量、错误和产物引用 |
| POST | `/runs/{run_id}/cancel` | 保存取消请求；待审任务同时拒绝提案；终态返回冲突 |
| POST | `/runs/{run_id}/retry` | 从失败、取消或过期任务创建新任务；显式给出当前基线及预算 |
| GET | `/change-sets` | 按状态列出提案，用于待验收列表 |
| GET | `/change-sets/{change_set_id}` | 正文引用、结构化操作、基线、警告、影响范围 |
| POST | `/change-sets/{change_set_id}/accept` | 原子验收正文/规划与记忆，校验正式及草稿基线 |
| POST | `/change-sets/{change_set_id}/reject` | 拒绝待审提案，源任务转为取消，不修改正式剧情 |
| GET | `/memory/search` | `query`、`target_chapter_number`、`memory_type`、`limit`；只能检索有效正式记忆 |
| GET | `/export?format=markdown` | 固定数据库快照导出有效已验收正文；返回附件与正式修订响应头 |

路径归属不匹配统一返回 `404 resource_not_found`，包括某项目下引用其他项目的版本和资产；不能只检查资源 ID 是否存在。资产的历史版本列表是管理视图，生成用的有效状态必须经过章节边界过滤。

导出端点返回 Markdown 附件而非 JSON 成功封装；失败仍按 JSON 错误契约。存在 `needs_revalidation` 章节时返回 `409 invalidated_chapters` 并列出相关章节。

## 3. 主要请求

### 创建小说

`POST /api/v1/novels`：

```json
{
  "title": "青云纪",
  "premise": "一名失去修为的药师重新进入宗门",
  "genre_plugin_id": "fantasy",
  "genre_plugin_version": "1.0.0",
  "style_profile": {
    "pace": "medium",
    "dialogue_ratio": 0.35,
    "tone": "warm",
    "description_density": "medium"
  }
}
```

示例版本只是目标规则包版本；实现前不存在可加载的规则包。创建成功返回项目对象及 `canon_revision: 0`；未知规则包/版本返回 `422 unknown_plugin_version`，不能静默选择其他版本。

### 保存草稿

`POST .../chapters/{chapter_id}/drafts`：

```json
{
  "base_version_id": null,
  "content_markdown": "# 第一章\n\n山门前，药师停下了脚步。"
}
```

首次草稿基线为 `null`；后续填当前草稿 UUID。回退或采用 AI 候选都通过保存内容创建新版本，传可选 `copied_from_version_id` 记录来源，`base_version_id` 仍是当前草稿指针。响应返回新版本 ID、草稿指针、计数和未验收标志，不递增正式修订。

### 提交生成任务

`POST .../runs`：

```json
{
  "kind": "generate_chapter",
  "chapter_id": "11111111-1111-4111-8111-111111111111",
  "expected_canon_revision": 8,
  "base_draft_version_id": null,
  "model_profile": "default",
  "parameters": {"target_length_hanzi": 2500},
  "budget": {"max_calls": 8, "max_total_tokens": 30000, "max_output_tokens_per_call": 6000}
}
```

数值是示例输入，不是已验证的默认值。服务端校验正数、配置上限、模型能力、章节前置条件与当前基线后持久化。响应：

```json
{
  "data": {
    "id": "22222222-2222-4222-8222-222222222222",
    "kind": "generate_chapter",
    "status": "queued",
    "base_canon_revision": 8,
    "base_draft_version_id": null
  }
}
```

`plan_novel` 不接受 `chapter_id` 或正文基线，`parameters` 指定规划范围；`review_chapter` 必须给 `chapter_id`、当前 `draft_version_id` 和相同的 `base_draft_version_id`，不接受生成长度。采用按 `kind` 区分的 schema，禁止无意义字段被静默忽略。

`model_profile` 是后端配置中的受支持路由名，不能通过请求传任意供应商 URL 或密钥。价格与供应商参数来自服务端配置快照。可选 `allow_model_fallback` 默认为 `false`；只有显式允许且后端预配置了兼容备用路由时才降级，结果记录实际路由与模型。

### 验收提案

`POST .../change-sets/{change_set_id}/accept`：

```json
{
  "expected_canon_revision": 8,
  "expected_draft_version_id": null,
  "acknowledge_review_warnings": true,
  "acknowledge_downstream_invalidation": false
}
```

正文提案中 `expected_draft_version_id` 必须与提案基线和当前草稿三者一致，`null` 也参与比较；规划提案不接受这个字段。成功响应包含 `accepted_canon_revision`、`accepted_version_id`（正文提案）、`run_status: succeeded` 和实际失效章节列表。

审稿警告需要确认；任何硬规则、schema、归属、版本错误都不允许通过确认字段绕过。需要使后续章节失效时，先读取提案影响范围，再明确提交确认。重复点击使用同一幂等键重放；不同键重验收已处理提案返回状态冲突。

资产、大纲历史修订同样使用 `acknowledge_downstream_invalidation`；资产写入还指定 `effective_from_chapter_number`。服务端根据当前有效链路重算影响，不信任客户端传来的失效章节列表。

## 4. 读取任务结果

`GET .../runs/{run_id}` 的 `data` 至少包括：

```text
id, kind, status, current_step, completed_steps, created_at, updated_at
base_canon_revision, base_draft_version_id
cancel_requested, candidate_version_id?, change_set_id?
usage: {input_tokens?, output_tokens?, estimated_cost?, currency?, has_unknown_usage}
attempts: [{step, attempt_no, status, provider, model, elapsed_ms, error_code?}]
error: {code, message, retryable, details}?
```

进度用当前步骤和完成步骤表达，不编造模型生成百分比。建议客户端在页面可见时以退避间隔轮询；终态与 `awaiting_review` 停止主动轮询，重新聚焦时可刷新。UI 不依赖浏览器连接维持任务。

## 5. 错误契约

```json
{
  "error": {
    "code": "canon_conflict",
    "message": "正式剧情已更新，请重新生成或审阅候选稿",
    "details": {"expected": 8, "actual": 9},
    "retryable": false
  },
  "request_id": "request-identifier"
}
```

| HTTP | 典型错误码 | 客户端行为 |
| --- | --- | --- |
| 404 | `resource_not_found` | 返回项目入口，不泄漏其他项目资源 |
| 409 | `canon_conflict`、`draft_conflict`、`asset_conflict` | 保留输入，刷新比较，不自动覆盖 |
| 409 | `run_in_progress`、`changeset_not_pending`、`run_state_conflict` | 展示当前任务或最新状态 |
| 409 | `novel_archived`、`unresolved_runs` | 恢复项目，或先处理任务/提案再归档 |
| 409 | `previous_chapters_unaccepted`、`downstream_confirmation_required`、`invalidated_chapters` | 导航到需处理的章节或影响列表 |
| 409 | `idempotency_conflict` | 同一键不能发送不同操作，停止自动重试 |
| 422 | `validation_error`、`unknown_plugin_version`、`hard_rule_violation`、`context_too_large` | 定位字段/约束问题并保留内容 |
| 429 | `local_rate_limited` | 按返回的重试建议等待 |
| 503 | `service_unavailable` | 数据库等本地依赖不可用；按幂等规则重试 |
| 500 | `internal_error` | 展示请求 ID，不泄漏堆栈或敏感内容 |

供应商调用发生在异步任务里：认证错误、模型限流耗尽、`budget_exceeded`、`invalid_model_output`、`outcome_unknown` 等保存在 Run.error，轮询本身仍可返回 `200`。`retryable` 表示是否适合创建新任务，不表示当前失败任务会复活，也不允许绕过预算或确认。
