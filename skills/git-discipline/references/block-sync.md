# 托管块同步机制

配套 `SKILL.md` 第 9 节。本文说明托管块为何这样设计，以及如何机械同步与校验。

## 1. 为什么需要托管块

多个 Agent、多个项目需要**同一套项目日志与 Git 纪律**。若每个项目各写一份：

- 内容深度不一（实测从 3 行到 17 行不等）
- 无法判断"是否已经统一"

托管块 = **一段带边界标记的标准文本**，整段复制进各项目 `AGENTS.md`，
内容保持**字节一致**，从而可用哈希校验。

## 2. 块形态

```markdown
<!-- GLOBAL-PROJECT-LOG-RULES:START v4 -->
## GLOBAL-PROJECT-LOG-RULES 托管规则块（v4）

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
- **推送结果以远端为准**（v4 新增）：`git push` 的**输出不可信** —— 实测出现过报错的同时打印
  `Everything up-to-date`，而远端**实际没收到**。推送后必须用 `git ls-remote origin <branch>`（或
  `git fetch` + 比对 SHA）核对远端；核对不一致就当作**失败**，不得回报"已推送"。
  链路抖动导致的推送中断（`GnuTLS recv error (-110)` / `send-pack: unexpected disconnect` /
  `Empty reply from server`）属**可重试错误**：先 `git -c http.version=HTTP/1.1 -c pack.threads=1 push`
  重试（关掉 HTTP/2 多路复用 + 单流 pack），连续失败再换出口/稍后重试；
  **禁止用 `--no-verify` 绕过门禁**来"解决"推送问题。
- commit 后 `git rev-list --first-parent --count HEAD` 记「第 N 次 git」/完整 SHA/文件范围/验证结果；最终回复**最后一条普通文本**写 `已git：<仓库> 第 N 次 git（commit <短SHA>）`——`<仓库>` **必填**，只改一个仓库也不省略（否则事后无法分辨是哪一份回报）；涉及多个仓库时**逐个仓库各写一行**；无 commit 写 `本轮未git：原因`；提交失败报 `GIT_BLOCKED`，不得把未提交说成完成。
- 回退优先 `git revert`（保留历史）；`reset --hard` / `git clean` 属危险操作需授权；`git reflog` 是最后保险。
- 日志机制本身不 commit、tag、push、删文件、切分支、操作数据库或控制服务；提交只能由上面的 Git 规则单独触发。

### 安全与隐私
- 永不把密码、`.env` 内容、凭据、token、cookie、私钥、真实个人数据、联系方式、数据库内容或敏感配置写入项目文件、日志或聊天。**秘密一旦提交极难清除**（需重写历史），防线前移到"根本不提交"。
- 无 git 跟踪的用户级文件，改前备份到本平台备份根，写入前核对目标盘可用与空间，写入后逐文件校验：
  - Windows Codex：`<盘符>:\CodexBackups\<类别>\<时间戳>`
  - WSL：`/mnt/<小写盘符>/CodexBackups/<类别>-<时间戳>/`
  - opencode：`<盘符>:\OpenCodeBackups\<类别>\<时间戳>`（**不与 Codex 备份混放**）

### 输出纪律
- 命令输出做精确匹配前先去 ANSI / 用 `--no-color`，优先结构化输出；名称命中后还要核对路径与身份。
- Windows/PowerShell 侧：结果变量不得命名为 `$matches`（与自动变量 `$Matches` 冲突）。
- 凡要求用户按精确文本回复/授权，必须把可发送原文单独放入 fenced code block；块内不加引号、句号或解释。

### 详细规则
- 完整规则与回退命令见 git 纪律技能 `git-discipline`（`SKILL.md` + `references/`）。
<!-- GLOBAL-PROJECT-LOG-RULES:END -->
```

**三个设计要点**

| 要点 | 原因 |
|---|---|
| **配对标记**（START / END） | 旧版只有开头标记，实测漂移出 5 种格式，无法机械定位边界 |
| **版本号**（`v4`） | 使新旧块可区分；升版时可一次性筛选受影响文件 |
| **平台中立** | 块内不写死盘符，按平台列出取值，使三平台共用同一份字节 |

## 3. 为什么必须平台中立

| 方案 | 变体数量 | 同步方式 |
|---|---|---|
| 平台专属块 | 随平台数增长 | 人眼比对（必然漂移） |
| **平台中立块** | **恒为 1** | **SHA256 机械校验** |

代价：块比平台专属版本略长（多两行路径说明）。
收益：同步**可判定**，这是跨三平台保持一致的根本原因。

## 4. 同步流程

```bash
# 1) 预览（默认 dry-run，不动文件）
python3 scripts/sync_block.py \
    --block configs/block/GLOBAL-PROJECT-LOG-RULES.v3.md \
    --targets targets.txt

# 2) 实际写入（可选先备份）
python3 scripts/sync_block.py \
    --block configs/block/GLOBAL-PROJECT-LOG-RULES.v3.md \
    --targets targets.txt --apply \
    --backup-dir <backup-root>/block-sync-$(date +%Y%m%d-%H%M%S)

# 3) 校验：必须 n/n 全一致
python3 scripts/verify_blocks.py \
    --block configs/block/GLOBAL-PROJECT-LOG-RULES.v3.md \
    --targets targets.txt
```

**退出码**：`verify_blocks.py` 全部一致返回 0，否则返回 1 —— 可直接用于 CI。

## 5. 校验原理

**只比对标记之间的内容**，不比对整个文件。否则文件其他部分的差异会污染结果。

```python
PAT_PAIRED = re.compile(
    r"<!--\s*GLOBAL-PROJECT-LOG-RULES:START\s+v[\d.]+\s*-->(.*?)"
    r"<!--\s*GLOBAL-PROJECT-LOG-RULES:END\s*-->", re.S)
# 取出 group(1) → strip → SHA256
```

同一块在 25 个文件中应产生**同一个哈希**。

## 6. 实测踩过的两个坑

### 坑 A：替换后标题粘连

替换块时若新块末尾**没有换行**，会把紧随其后的标题粘到同一行：

```
<!-- GLOBAL-PROJECT-LOG-RULES:END -->

## 项目专属约束
```

破坏 Markdown 结构。`sync_block.py` 的 `fix_trailing_newline()` 负责修正。

### 坑 B：项目专属内容被块覆盖

若把项目特有条款写进**块内部**，下次同步整段替换时会丢失。

**规则**：项目专属内容必须写在块**之外**，另起 `## 项目专属约束` 段。

## 7. 目标清单（targets）

`targets.txt` 每行一个文件路径：

```
# 注释与空行会被忽略
$HOME/projects/example/AGENTS.md
/mnt/d/projects/another/AGENTS.md
```

**批量生成**：

```bash
ls /mnt/d/projects/*/AGENTS.md > local/targets.txt
```

**注意**：真实清单含本机路径，应写入 `local/targets.txt`（已被 `.gitignore` 排除），
不要提交到公开仓库。

## 8. 升级块的版本

当块内容有较大变更时，建议升版本号（`v3` → `v4`），使新旧可区分：

```markdown
<!-- GLOBAL-PROJECT-LOG-RULES:START v4 -->
```

**注意**：任何块内容变更都会改变哈希，因此**所有**目标都需要重新同步。
这正是要让同步可机械执行的原因。

## 9. 与技能的关系

| 载体 | 谁读 | 内容 |
|---|---|---|
| 托管块（写进 `AGENTS.md`） | Codex / opencode 等 | 精简投影，足以独立执行 |
| 技能 `git-discipline` | 支持技能的 Agent（含 DSH） | 完整规则 + 细节 references |

**DSH 不读 `AGENTS.md`**，只加载技能。因此两者必须同时提供，缺一会导致某类 Agent 完全失效。
