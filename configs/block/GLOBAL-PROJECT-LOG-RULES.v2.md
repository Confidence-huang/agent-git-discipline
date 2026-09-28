<!-- GLOBAL-PROJECT-LOG-RULES:START v2 -->
## GLOBAL-PROJECT-LOG-RULES 托管规则块（v2）

### 身份与范围
- 本块适用于本文件所在的**本仓库**，以及规范化后 Git common dir 与该仓库完全一致的 worktree；路径名、标记文件、remote 名或提交本身都不能单独证明身份。
- `PROJECT_LOG.md` 是唯一跨会话连续性入口与当前状态事实来源。进入项目先读 `PROJECT_LOG.md`，再读本文件，再读 live Git 状态。
- 用户当前会话中的明确指令与本块冲突时，**以用户明确指令为准**。

### 日志写入
- 仅当允许写项目时，才在任务完成、暂停、被叫停或阻塞前更新 `PROJECT_LOG.md`；更新前重读当前日志，避免覆盖更新的记录。
- 只有主 agent 写 `PROJECT_LOG.md`；子 agent 只向主 agent 报证据，不直接改。
- 更新形状：刷新当前快照，并追加至多一条简要近期记录（已核实改动、验证、未完成项、风险、下一个安全起点）。
- 普通 stop、compact、handoff 不新建独立交接 Markdown；旧交接文件保留为历史；额外交付文件需用户明确要求。
- 增长上限：只保留最近 20 条或 30 天；更早记录仅在获授权维护时归档到 `docs/project-log-archive/`。
- 历史边界：`current-task.md`、`.harness/session-state.json`、`.harness/session-log.md`、`03_*.md`、`PROJECT_HANDOFF.md`、`notes.md`、`.harness/latest-handoff.md`、`.harness/context-summaries/` 只作历史参考，永不覆盖固定日志。
- 保留原则：未经单独授权，不删除或改写历史日志。

### Git 事实与操作
- Live Git truth：branch、HEAD、worktree 状态是**恢复期事实**，必须从 Git 现读；日志只记稳定检查点与安全边界，不复制瞬时状态。
- 自引用：`PROJECT_LOG.md` 不预测包含它自己的那个 commit 的 SHA；该 commit 由 Git 在提交后解析。
- 写代码/配置前先核对 Git 根（`git rev-parse --show-toplevel`）、branch、HEAD、index 与目标文件归属；不得在不知道仓库边界时直接写代码。
- 首段写入前建本次原子基线；每个通过验证的原子改动只暂存本轮文件，复核 `git diff --staged` 后立即本地 commit；禁止 `git add .` / `git add -A`；**不允许积攒多轮改动一次混合提交**；混杂时用 `git add -p` 逐块挑选。
- **原子性检验**：只做一件事／代码库仍可工作／message 标题不需要"and"／能独立 revert／无需外部上下文即可理解。描述时必须说"和"，就是两个 commit。
- 本地 commit **已默认授权**，不必逐次确认；**不包含**新建/切换分支、rebase、reset、改写历史、tag、push、PR、删除、批量清理——这些需单独授权。`push --force` 禁止；确需时只用 `--force-with-lease` 且限自己分支。
- 工作区起点若为脏：用户的改动先报告、不擅自提交或丢弃；上一轮 agent 的改动先提交或 stash 存档；**不回退与本轮无关的改动**。
- commit 后 `git rev-list --first-parent --count HEAD` 记「第 N 次 git」/完整 SHA/文件范围/验证结果；最终回复**最后一条普通文本**写 `已git：第 N 次 git（commit <短SHA>）`；无 commit 写 `本轮未git：原因`；提交失败报 `GIT_BLOCKED`，不得把未提交说成完成。
- 回退优先 `git revert`（保留历史）；`reset --hard` / `git clean` 属危险操作需授权；`git reflog` 是最后保险。
- 日志机制本身不 commit、tag、push、删文件、切分支、操作数据库或控制服务；提交只能由上面的 Git 规则单独触发。

### 安全与隐私
- 永不把密码、`.env` 内容、凭据、token、cookie、私钥、真实学生数据、联系方式、数据库内容或敏感配置写入项目文件、日志或聊天。**秘密一旦提交极难清除**（需重写历史），防线前移到"根本不提交"。
- 无 git 跟踪的用户级文件，改前备份到本平台备份根，写入前核对目标盘可用与空间，写入后逐文件校验：
  - Windows Codex：`E:\CodexBackups\<类别>\<时间戳>`
  - WSL：`/mnt/e/CodexBackups/<类别>-<时间戳>/`
  - opencode：`E:\OpenCodeBackups\<类别>\<时间戳>`（**不与 Codex 备份混放**）

### 输出纪律
- 命令输出做精确匹配前先去 ANSI / 用 `--no-color`，优先结构化输出；名称命中后还要核对路径与身份。
- Windows/PowerShell 侧：结果变量不得命名为 `$matches`（与自动变量 `$Matches` 冲突）。
- 凡要求用户按精确文本回复/授权，必须把可发送原文单独放入 fenced code block；块内不加引号、句号或解释。

### 详细规则
- 完整规则与回退命令见 git 纪律技能 `git-discipline`（`SKILL.md` + `references/`）。
<!-- GLOBAL-PROJECT-LOG-RULES:END -->
