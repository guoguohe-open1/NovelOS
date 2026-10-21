# 设计文档导航

更新：2026-10-21。状态：**T00 默认原生路径已验收；业务能力待实现，Compose 可选**。实际检查和环境限制见 [T00 验证记录](t00-validation.md)。

## 阅读路径

- 理解产品：先读 [产品范围](product.md)，再读 [交互设计](ux.md)。
- 准备实现：先读 [架构](architecture.md)、[领域模型](domain-model.md)、[工作流](workflows.md)，再按 [实施计划](implementation-plan.md) 选择任务。
- 接口联调：读 [API 契约](api.md)，结合领域约束和 [验证策略](validation.md)。
- 追溯设计：读 [决策记录](decisions.md) 和 [样稿审阅](sample-review.md)。
- 本地开发与版本管理：读 [数据库运行](local-development.md) 和 [Git 工作流](git-workflow.md)。

## 单一职责与权威归属

| 文档 | 负责回答 | 作为哪类信息的依据 |
| --- | --- | --- |
| [product.md](product.md) | 为谁做、解决什么、做到哪里 | 范围、优先级、产品验收 |
| [architecture.md](architecture.md) | 模块怎样协作、怎样运行 | 目录、依赖方向、部署边界 |
| [domain-model.md](domain-model.md) | 什么是正式内容、如何保持一致 | 实体、约束、版本、事务 |
| [workflows.md](workflows.md) | AI 怎样执行、何时停、怎样恢复 | Agent 协议、任务状态、上下文 |
| [api.md](api.md) | 前后端怎样交互 | HTTP 资源、错误、幂等与并发契约 |
| [ux.md](ux.md) | 作者怎样完成一次创作 | 页面、操作、反馈与异常恢复 |
| [implementation-plan.md](implementation-plan.md) | 下一步做什么、如何判断完成 | 任务依赖、交付物、验收门槛 |
| [validation.md](validation.md) | 怎样证明功能与长篇能力有效 | 测试场景、实验方法、证据 |
| [decisions.md](decisions.md) | 为什么采用这些设计 | 重要取舍、代价、重审触发条件 |
| [sample-review.md](sample-review.md) | 样稿有什么问题、如何被吸收 | 审阅发现、原文定位与迁移关系 |
| [t00-validation.md](t00-validation.md) | T00 实际做了什么、哪些检查通过 | 运行环境、实测证据与未验证项 |
| [local-development.md](local-development.md) | 怎样不依赖 Docker 运行数据库 | 原生数据库默认路径、可选 Compose 与进程管理 |
| [git-workflow.md](git-workflow.md) | 何时提交、怎样配置账号与推送 | 本地 Git 流程与远程同步步骤 |

这些文档共同构成设计基线，并非多份独立方案。修改字段或状态时应同步引用它的文档；发生冲突先修订契约，不自行选一份实现。历史样稿已退出仓库；审阅记录中的原文名称仅用于追溯，不是实现依赖。

## 范围标识

- **MVP**：从无项目到一章可生成、可编辑、可验收、可导出的可运行闭环，对应 T00–T09。
- **长篇验证**：用已完成闭环开展 10 万字实验，对应 T10；未通过前不宣称支持稳定长篇生产。
- **后续**：多题材、语义检索、复杂图谱、自动导演、多用户和百万字实验，不进入 MVP 验收。

## 统一术语

| 名称 | 含义 |
| --- | --- |
| 项目 / Novel | 一部小说及其设定、章节、任务和记忆的隔离边界 |
| 正式剧情 / canon | 作者已确认的设定、大纲与已验收章节，不等于已对外发布 |
| `canon_revision` | 项目内正式剧情的单调递增修订号，用于检测上下文过期 |
| 草稿 / draft | 作者当前编辑的正文版本；保存不等于验收 |
| 候选稿 / candidate | AI 或人工产生的不可变正文版本，可与当前草稿比较 |
| 变更提案 / ChangeSet | 基于某个正式修订与草稿基线生成的结构化变更，等待作者验收 |
| 任务 / Run | 持久化的工作流执行；一个任务包含多个 Agent 步骤和模型尝试 |
| Agent | 有职责、类型化输入输出与能力边界的执行单元，可由普通函数实现 |
| 正式记忆 / MemoryRecord | 从已验收内容形成、带来源和时间边界的检索记录 |
| 提示词中的资料 | 小说文本、检索片段、模型输出都是数据，不是系统指令 |

安装、开发与检查命令见根目录 README，实际结果见 T00 验证记录；Txx 仍是文档中的任务标识，未创建外部 Issue。
