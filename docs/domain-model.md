# 领域模型、版本与一致性

## 1. 领域不变量

1. 每个业务资源属于一个 `Novel`；跨项目 ID 即使存在也不能被读写或检索到。
2. `canon_revision` 从 `0` 开始，仅在一次成功的正式剧情事务结束时加 `1`，不因读操作、草稿保存、候选生成或失败任务变化。
3. 正文和资产版本内容不可变。当前指针、有效性标记可变，但历史正文与结构化内容不可就地重写。
4. AI 提案只有作者验收后才生效；正文验收与相应资产/记忆更新必须同事务成功或回滚。
5. 模型产物不能绕过字段 schema、项目归属、版本基线、章节顺序和人工验收校验。
6. 同一项目最多一个 `queued` 或 `running` 的任务；`awaiting_review` 不占执行槽，允许作者先处理已有候选。

以下是关系与字段设计，**不是已有数据库 schema**。实现用迁移、约束与事务测试落实这些规则。

## 2. 核心对象

### Novel

`id: UUID`、`title`、`premise`、`status: active|archived`、`genre_plugin_id`、`genre_plugin_version`、`style_profile: JSONB`、`canon_revision: bigint`、`created_at`、`updated_at`。

标题和归档状态是管理元数据，单独修改不递增正式修订；创意、风格及故事结构属于生成依据，修改它们需要正式修订检查。题材包 ID/版本创建后在 MVP 中固定，迁移规则包属于后续能力。

归档项目只允许读取、导出和恢复为 `active`。有 `queued`、`running` 或 `awaiting_review` 任务时禁止归档，需先取消或处理提案；归档与任务创建共用项目锁，不能通过并发请求绕过。

`style_profile` 使用固定 schema，例如 `pace`、`dialogue_ratio`、`tone`、`description_density`；范围与枚举由 schema 校验，不能是任意插件代码。

### Volume 与 Chapter

| 对象 | 主要字段 |
| --- | --- |
| Volume | `id`、`novel_id`、`order_index`、`title`、`goal`、`summary` |
| Chapter | `id`、`novel_id`、`volume_id`、`chapter_number`、`title`、`outline`、`outline_revision`、`draft_version_id?`、`accepted_version_id?`、`needs_revalidation` |
| ChapterVersion | `id`、`novel_id`、`chapter_id`、`parent_version_id?`、`content_markdown`、`content_hash`、`hanzi_count`、`character_count`、`author_type: human\|ai`、`source_run_id?`、`created_at` |

章节号在项目内全局唯一，从 `1` 连续创建，跨卷也不重置。已验收章节的排序和编号在 MVP 中不可直接修改。卷顺序唯一；用复合外键确保卷、章节、版本属于同一项目。

`outline` 是有 schema 的章节纲，含目标、冲突、场景计划和涉及资产 ID；保存递增 `outline_revision` 并产生正式修订。卷目标等规划数据同样属于正式剧情。运行快照保留实际使用的规划内容，不依赖之后的可变字段。

正文没有可变的 `Chapter.content` 副本。编辑区加载 `draft_version_id`；正式导出加载 `accepted_version_id`。候选生成只新增 `ChapterVersion`，不修改这两个指针。

草稿保存需携带当前 `draft_version_id`，成功新增版本并移动草稿指针；值为 `null` 时表示尚无草稿。同一事务将该章基于旧草稿的待审正文提案和对应任务标记 `stale`，不影响规划提案；执行中的任务在检查点再核对。回退旧稿是复制旧内容生成新版本，MVP 不提供版本树合并。

章节展示状态由数据推导：没有有效验收版本为 `draft`，有有效验收版本为 `accepted`，`needs_revalidation=true` 为 `needs_revalidation`。已验收章节继续保存草稿时，原正式稿仍有效，UI 同时显示“有未验收修改”。任务状态单独展示。

### StoryAsset 与 AssetVersion

为了避免四套相似 CRUD 与版本逻辑，人物、世界实体、事件、伏笔统一为**有类型的资产**，而不是自由文本堆积：

| 对象 | 主要字段 |
| --- | --- |
| StoryAsset | `id`、`novel_id`、`kind: character\|world\|event\|foreshadowing`、`created_at` |
| AssetVersion | `id`、`novel_id`、`asset_id`、`revision`、`name`、`schema_version`、`data: JSONB`、`effective_from_chapter_number`、`source_chapter_version_id?`、`source_run_id?`、`author_type`、`created_at` |

核心 ID、类型、来源、版本、生效章节是关系字段；类型细节放 JSONB 并用 Pydantic/JSON Schema 验证。核心 schema 至少约束：

- 人物：角色、动机、性格、秘密、当前状态；关系项引用本项目人物 ID。
- 世界：实体类型、描述、不可违反的规则；玄幻扩展提供境界等字段 schema。
- 事件：起因、结果、参与者、发生章节；引用实体必须存在或在同一提案中创建。
- 伏笔：内容、埋设章节、预期回收范围、`open|resolved` 状态、回收来源。

不单独建立图数据库；MVP 人物关系先用 schema 校验的引用表达。未来复杂关系查询再迁移为独立关系实体。

资产版本按章节边界生效：初始设定从第 `1` 章可见；第 `k` 章验收提取的状态从第 `k+1` 章可见。人工编辑默认从“最后一章有效验收章节的下一章”生效；历史修订必须显式选择边界并展示影响范围。

Context Builder 为目标章 `n` 选取生效边界 `<= n` 的最新有效资产版本，不能直接把最新人物状态用于重写早期章节。来源章节版本已失效的资产版本不参与选取；版本内容仍保留用于审计。

### MemoryRecord

`id`、`novel_id`、`memory_type: chapter_summary|fact|open_thread`、`content`、`source_chapter_version_id?`、`source_asset_version_id?`、`effective_from_chapter_number`、`importance`、`status: active|retired`、`created_at`。

两种来源必须恰有一种非空，并由复合外键保证项目一致。章摘要由已验收章形成，事实与伏笔可由已验收资产形成。`MemoryRecord` 是可重建的检索资料，不是资产事实的第二套可独立修改来源。

来源 ID 由应用根据实际验收的正文/资产版本绑定，不接受模型任意指定来源。人工正式资产修改与 AI 提案接纳都由应用同步生成或退役对应检索记录；从无记忆能力的早期开发阶段升级时，需提供从正式资产重建记录的步骤。

检索必须过滤 `novel_id`、`active`、生效章节及来源有效性；目标章 `n` 的摘要只能来自 `< n` 的章。正文候选、审稿分数不能成为正式记忆。MVP 使用结构化筛选、最近章摘要与关键词查询；向量索引字段暂不加入权威表。

## 3. 任务与提案对象

| 对象 | 关键字段与用途 |
| --- | --- |
| Run | `id`、`novel_id`、`kind`、`chapter_id?`、`status`、`base_canon_revision`、`base_draft_version_id?`、`input_snapshot`、`config_snapshot`、`checkpoint`、`lease_owner?`、`lease_generation`、`lease_expires_at?`、`cancel_requested_at?`、`retry_of_run_id?`、`budget`、`usage`、`error?`、时间戳 |
| StepAttempt | `id`、`run_id`、`step`、`attempt_no`、`status`、请求/响应摘要、输出引用、供应商与模型、提示词版本、输入输出 token、费用估算、是否有未知用量、开始/完成时间 |
| ChangeSet | `id`、`novel_id`、`source_run_id`、`kind: plan\|chapter`、`status: pending\|accepted\|rejected\|stale`、`base_canon_revision`、`chapter_id?`、`base_draft_version_id?`、`candidate_version_id?`、`operations`、`review_report`、`accepted_canon_revision?` |
| IdempotencyRecord | 操作作用域、键、请求内容哈希、资源 ID、原始 HTTP 状态和响应、创建时间 |

`Run.kind` 为 `plan_novel|generate_chapter|review_chapter`，状态与恢复规则见 [工作流](workflows.md)。幂等记录至少与关联项目同寿命保留，清理策略须显式设计；MVP 不自动过期。

`StepAttempt.status` 为 `prepared|sent|succeeded|failed|outcome_unknown`。`lease_generation` 每次领取/重领递增，所有检查点与结果写入必须匹配当前代数；丢失租约的旧 worker 不得继续推进任务。

`input_snapshot` 保存实际章节纲、资产版本 ID、记忆 ID 与文本快照、基础正文版本、输入哈希。`config_snapshot` 保存提示词版本、规则包版本、模型参数和能力选择，避免工作中配置变化造成无法解释的结果。

`operations` 只允许有限领域操作：`create_asset`、`revise_asset`、`create_volume`、`create_chapter`、`revise_outline`、`add_memory`、`accept_chapter_version`。每类有独立 schema，不接受 SQL、任意 JSON Patch、文件路径或可执行代码。新对象使用提案内临时引用，验收时一次性分配 ID 并校验引用闭合。

`chapter` 提案只能接纳一个正文版本，并包含该确切版本的摘要与状态变化；提取器不能顺带修改无关章节纲或卷结构。MVP 提案整批接纳/拒绝；修改候选正文后需要重新审阅并生成提案，不做部分套用。

## 4. 事务与并发

### 正式验收事务

1. 根据 `novel_id` 锁定 Novel 行；读取提案并检查项目归属、`pending`、关联任务为 `awaiting_review`。
2. 核对请求和提案的 `base_canon_revision` 均等于当前正式修订；章节提案额外核对当前草稿指针等于 `base_draft_version_id`。
3. 验证候选版本、记忆来源、引用、规则包和所有操作；正文提案必须已完成该版本的审阅。允许作者显式确认审稿警告，但 schema、版本、隔离和硬规则失败不可跳过。
4. 对目标章检查前序章节已连续有效验收。替换第 `k` 章时允许该章已有正式稿，但必须先有影响范围确认。
5. 应用所有操作；正文验收将草稿指针与正式指针都移动到候选版本；创建/替换正式记忆和资产版本。
6. 递增一次 `canon_revision`；提案记为 `accepted`，源任务记为 `succeeded`；其他基于旧修订的待审提案/任务记为 `stale`。
7. 一并保存幂等响应后提交。任一步异常全部回滚，不能出现“正文已接纳、记忆未更新”。

保存人工资产、规划或项目生成约束同样锁定 Novel 并核对预期修订，更新后使旧待审提案过期。运行中的任务在下一检查点发现修订变化时停止为 `stale`。

### 修改已验收历史

替换第 `k` 章时，旧版对应的正式记忆退役；所有后续已验收章节标记 `needs_revalidation`，并退役它们的记忆。来自这些章节的资产版本不再有效。原正文与资产版本保留。

历史资产/大纲修订从显式生效边界起，同样使相关已验收章节和记忆失效。UI 先显示影响列表；写请求必须携带 `acknowledge_downstream_invalidation: true`，服务端仍按事务时的当前数据重算影响。

作者按章序对原文执行 `review_chapter` 并重新验收，或重新生成，恢复有效链路。MVP 不自动重写后续章节。存在失效章节时，正式整书导出返回冲突并列出章节，不静默遗漏。

## 5. 数据库约束与索引

- UUID 主键；时间为带时区的 UTC，展示时转换为用户时区；token、计数、章节序号与修订号有非负/正数约束。
- 唯一约束：`(novel_id, chapter_number)`、`(novel_id, volume.order_index)`、`(asset_id, revision)`、`(run_id, step, attempt_no)`、幂等作用域和键。
- 对 `runs(novel_id)` 建 `status IN ('queued','running')` 的部分唯一索引；领取任务按状态与创建时间索引，避免多 worker 重复执行。
- 所有跨对象外键含项目归属校验；章节版本的指针还需确认同一章节。可用复合外键实现的，不只依赖 API 校验。
- 为章节顺序、资产类型/生效边界、记忆来源/状态、任务状态和版本历史建立匹配查询的索引。JSONB 按实际查询增加索引，不全量盲建。
- MVP 无物理删除业务资源接口。归档保留历史和来源；清理和保留期在有真实数据规模后单独设计。

汉字数按固定 Unicode 汉字范围计数，总字符数独立统计；计数规则在 T01 固化并测试。10 万字实验只累计有效已验收版本，不能重复累计历史版本。
