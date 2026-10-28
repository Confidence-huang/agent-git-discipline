# Antigravity 全局规则示例（Git 纪律部分）

> **用途**：放到 Antigravity 的**全局规则入口**，对本机所有工作区生效：
>
> - `%USERPROFILE%\.gemini\AGENTS.md`，或
> - `%USERPROFILE%\.gemini\config\AGENTS.md`
>
> **已脱敏**：路径用占位符，请按 [docs/04-环境支持.md](../../docs/04-环境支持.md) 替换备份根。
>
> ⚠️ **两个硬约束（2026-10-28 实测，违反会静默失效）**
> 1. 本文件**不能带 YAML frontmatter**。`AGENTS.md` 是"整份纯 Markdown、恒定 always_on"，
>    出现 frontmatter 会被当成正文内容而不是元数据。
> 2. 单文件上限 **24,000 字节**（`@[label](path)` 展开后计算），超出按行截断；
>    全局与 always_on 规则合计还有 **20,000 token** 预算，超了会被降级成"路径指针"，
>    模型只看到 `- <path>: <description>` 而不是全文。
>
> **不要整体覆盖**你已有的全局规则——只把下面章节追加进去；
> 更细的规则交给技能侧（`git-discipline`），避免同一套规则在两处各写一遍然后漂移。

---

## 代码修改的 Git 闭环

- 任何代码、脚本、构建配置或规则文件改动前，先用 `git rev-parse --show-toplevel` 确认 Git 根，
  核对 branch、HEAD、index 与工作树；不得在不知道仓库边界时直接动手。
  多 worktree 并存时先确认自己改的是哪个工作树的副本。
- 本地 `git commit` **已默认授权**，不必逐次确认：每个通过验证的原子改动，
  只暂存本轮明确文件 → 复核 `git diff --staged` → 立即提交。
  **不允许积攒多轮改动后一次混合提交。**
- 禁止 `git add .` / `git add -A`；混杂时用 `git add -p` 逐块挑选。
  发现范围外文件被暂存，用 `git restore --staged <文件>` 撤回，**但不得丢弃用户内容**。
- 判据只有一条：只做一件事／代码库仍可工作／commit 标题不需要"and"／
  能独立 revert ／审查者无需外部上下文即可理解。**描述时必须说"和"，那就是两个 commit。**
- 回退优先 `git revert`（保留历史，可安全推送）；`git reset --hard` 与 `git clean`
  属危险操作需单独授权；`git reflog` 是最后保险。

## 授权边界

| 动作 | 授权状态 |
|---|---|
| `git status` / `diff` / `log` / `show` / `rev-list` | ✅ 默认授权 |
| `git add <本轮明确文件>`、本地原子 commit | ✅ 默认授权 |
| 新建/切换分支、`rebase`、`reset`、改写历史、`tag` | ⚠️ 需单独授权 |
| `push`、PR、任何远端写操作 | ⚠️ 需单独授权 |
| 删除文件、`git clean`、批量清理 | ⚠️ 需单独授权 |
| `git push --force` | ❌ 禁止；确需时只用 `--force-with-lease` 且限自己分支 |

## 编号与回报

- commit 后执行 `git rev-list --first-parent --count HEAD`，记「第 N 次 git」+ 完整 SHA + 文件范围。
- 最终回复的**最后一条普通文本**写 `已git：<仓库> 第 N 次 git（commit <短SHA>）`；
  无 commit 写 `本轮未git：原因`。**不得伪造编号。**
- 涉及**多个仓库**时逐个仓库各写一行；单仓库也**不省略** `<仓库>`。

## 推送以远端为准

- ⚠️ `git push` 的输出不可信：实测出现过"报错的同时打印 `Everything up-to-date`"而远端**没收到**。
  推送后必须用 `git ls-remote origin <branch>`（或 `git fetch` + 比对 SHA）核对；
  不一致按**失败**处理，不得回报"已推送"。
- 链路抖动（`GnuTLS recv error (-110)` / `send-pack: unexpected disconnect` / `Empty reply from server`）
  属可重试错误：先 `git -c http.version=HTTP/1.1 -c pack.threads=1 push` 重试，
  连续失败再换出口或稍后重试；**禁止用 `--no-verify` 绕过门禁**来解决推送问题。

## 安全与收尾

- 永不把密码、凭据、token、私钥、真实个人数据写进项目文件或聊天；秘密一旦提交极难清除。
- 工作区起点若为脏：**用户的**改动先报告、不擅自提交或丢弃；**上一轮 agent 的**改动先提交或 `stash`；
  **不回退与本轮无关的改动**。
- 项目级 `AGENTS.md` 里的 `GLOBAL-PROJECT-LOG-RULES` 托管块（v6）优先于本节；
  用户当前会话中的明确指令优先于一切。
