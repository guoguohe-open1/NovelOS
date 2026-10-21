# Git 身份、提交和远程同步

项目使用 `main` 作为初始分支。Git 管理源码、设计文档和依赖锁文件；`.env`、`.local/`、数据库数据、node_modules、虚拟环境和构建缓存不进入版本历史。`.gitattributes` 统一文本换行为 LF。

## 1. 区分提交身份和登录账号

`user.name` / `user.email` 是提交中的作者署名，不是 GitHub / GitLab / Gitee 的登录凭据。HTTPS 的认证由 Git Credential Manager 等凭据助手完成；SSH 使用密钥。GitHub 连接器的账号不能证明本机命令行也使用同一账号。

查看本仓库最终生效的署名：

```powershell
git config --show-origin --get user.name
git config --show-origin --get user.email
```

多账号机器优先只设置本仓库，保留全局工作账号。以下值需替换为自己的身份；GitHub noreply 邮箱应从 [GitHub 邮箱设置](https://github.com/settings/emails)确认：

```powershell
git config --local user.name '你的提交显示名称'
git config --local user.email '你的 GitHub noreply 邮箱'
git config --local user.useConfigOnly true
```

邮箱决定提交能否关联到托管平台账号，可使用 noreply 邮箱避免把私人或公司邮箱带入公开历史。配置原理见 [Git user.name / user.email](https://git-scm.com/docs/git-config#Documentation/git-config.txt-username) 和 [GitHub 提交邮箱](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address)。

本次初始化已按用户选择设置本仓库的个人 GitHub 名称及 noreply 邮箱；全局公司身份没有修改。身份配置保存在本机 `.git/config`，不会随克隆复制给其他开发者。

## 2. 何时创建本地提交

每个逻辑完整的改动完成并通过相应验证后提交，例如：文档契约收尾、工程初始化、一个修复或一个可验收业务切片。检查未通过或仍在临时探索时保留工作区，不制造完成提交。依赖清单、锁文件、迁移和相关文档一起提交。

开始工作先看 `git status --short`；提交前审阅当前任务差异与文件清单，保护用户已有改动。显式暂存当前任务文件，再检查将要提交的内容：

```powershell
git status --short
git diff --check
git diff -- README.md AGENTS.md
git add -- README.md AGENTS.md
git diff --cached --stat
git diff --cached --check
git diff --cached
git commit -m 'docs: 更新本地运行与协作约定'
git status --short
```

上例只演示两个文档，实际按本轮改动填写文件清单。首次工程基线提交应逐一核对已有源文件和文档，不能用 `git add .` 将未知文件混入。`.env` 的检查只验证忽略状态，不读取内容：

```powershell
git check-ignore -v .env .local/
git ls-files -- .env
```

第二条应无输出。按 [README 检查说明](../README.md#检查与最小测试)运行与改动相关的验证；纯文档修改检查链接与命令一致性，不为展示文案重复运行整个业务测试集。

## 3. 首次创建远程并推送

当前本地仓库已初始化；目标远程仓库尚未创建，未配置 `origin`，因此还不能验证目标写权限或执行首次推送。此时无法仅凭作者邮箱判断“能推到哪个账号”。

用户在预期账号下创建空仓库（例如 NovelOS），选择可见性；已有完整本地工程时不要在远程额外初始化 README、`.gitignore` 或 License。复制新仓库的 HTTPS 地址，核对所有者后执行（示例占位符需替换）：

```powershell
git remote add origin 'https://github.com/<owner>/NovelOS.git'
git remote -v
git log -1 --oneline
git push --dry-run origin main
git push -u origin main
```

已有 `origin` 时先检查，不重复添加或擅自替换。`--dry-run` 不更新远程引用，可验证连接和推送协商；最终推送仍需遵守服务器分支规则。实际推送由用户执行，或在用户明确要求代为推送后执行。

本机已安装 Git Credential Manager 并配置 `manager` 助手。首次 HTTPS 推送可能弹出浏览器登录，请在本机选择目标账号完成认证；不要把密码或令牌发给助手，不把令牌写进远程 URL、文档或提交。GitHub Git 操作不使用普通账户密码，详见 [GitHub HTTPS 与凭据缓存](https://docs.github.com/en/get-started/git-basics/caching-your-github-credentials-in-git)。

本次未安装 `gh`，不要求额外安装。SSH 到 GitHub 的 22 端口连接测试超时，未能证实 SSH 登录账号；后续可先使用 HTTPS，网络与目标仓库写权限仍需实际验证。连接器访问仓库的权限与命令行认证分开判断。

若远程已经有历史，先获取并检查分叉关系，保留双方内容；不要为了完成初始化使用强推覆盖。

## 4. 后续同步与提醒时机

初始化基线完成、一个任务验收完成、或准备开始下一项较大工作且本地已有完整可用提交时，助手应主动提醒用户推送，并列出提交、验证和工作区状态。默认不代替用户推送，也不按文件保存次数反复提醒。

工作区干净且确认上游分支后，同步示例为：

```powershell
git fetch origin
git status -sb
git log --oneline origin/main..HEAD
git push
```

如果远程有本地缺失的提交，先检查差异，按当前协作约定整合；不自动重置、改写历史或强推。正常本地提交无需逐步确认，实际远程发布遵守用户当次授权范围。
