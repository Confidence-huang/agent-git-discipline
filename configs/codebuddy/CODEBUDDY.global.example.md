# CODEBUDDY.md 全局规则示例（Git 纪律部分）

> **用途**：可直接**追加**到 WorkBuddy / CodeBuddy 的用户级记忆文件
> （`%USERPROFILE%\.codebuddy\CODEBUDDY.md`，另有 `CODEBUDDY.local.md`）的示例。
>
> **依据（2026-10-12 先读 bundle、后跑运行时实测）**：用户级记忆文件是
> `%USERPROFILE%\.codebuddy\CODEBUDDY.md`（运行时打 `[user] [always] …` 实锤）；
> **项目级**记忆文件名才是 `AGENTS.md` / `AGENTS.mdc`——所以项目里的托管块本来就生效，
> 这份示例补的是**用户级**那一层。
>
> ⚠️ 两个实测坑：① `%USERPROFILE%\.workbuddy\CODEBUDDY.md` **不读**（用户级入口在 `.codebuddy\` 下）；
> ② 项目根若同时存在 `CODEBUDDY.md`，**只加载后者**、`AGENTS.md` 被跳过。
>
> **不要整体覆盖**你已有的 `CODEBUDDY.md`——只把下面条目追加进去。

---

## Git 纪律（与托管块 v5 同源）

- 改动任何代码、脚本、配置或规则前，先核对 **Git 根**（`git rev-parse --show-toplevel`）、
  branch、HEAD、index 与目标文件归属；不得在不知道仓库边界时动手。
- **本地 `git commit` 默认授权**，不必逐次确认；**不包含** `push`、新建/切换分支、`rebase`、
  `reset`、改写历史、`tag`、PR、删除与批量清理——这些需单独授权，且**一次授权只覆盖一个动作、一个仓库**。
- 原子改动：只暂存本轮明确文件 → 复核 `git diff --staged` → 立即提交；
  禁止 `git add .` / `git add -A`；**不积攒多轮改动一次混合提交**。
- 编号回报：`git rev-list --first-parent --count HEAD` 记「第 N 次 git」；
  最后一条普通文本写 `已git：<仓库> 第 N 次 git（commit <短SHA>）`，
  无提交写 `本轮未git：原因`；多仓库时逐个仓库各写一行。
- **推送结果以远端为准**：`git push` 的输出不可信（实测出现过"报错的同时打印
  `Everything up-to-date`"而远端没收到）；推送后必须 `git ls-remote origin <branch>` 核对，
  不一致按**失败**处理、不得回报"已推送"。链路抖动可重试：
  `git -c http.version=HTTP/1.1 -c pack.threads=1 push`；**禁止 `--no-verify` 绕过门禁**。
- 项目级 `AGENTS.md` 应包含 `GLOBAL-PROJECT-LOG-RULES` 托管块 **v5**；权威模板见来源仓库
  `agent-git-discipline` 的 `configs/block/GLOBAL-PROJECT-LOG-RULES.v5.md`。

---

## 技能接入（Windows 侧必须用 Junction）

WorkBuddy / CodeBuddy 的技能发现根（2026-10-12 运行时实测）：
`%USERPROFILE%\.workbuddy\skills\`（WorkBuddy 系）或 `%USERPROFILE%\.codebuddy\skills\`
（CodeBuddy CLI 系），另有项目级 `.codebuddy\skills\` 与插件市场
`…\plugins\marketplaces\*\plugins\*\skills\`。
`%USERPROFILE%\.agents\skills\` **未证实**是它的发现根（只出现在 bundle 的"允许写/排除备份"清单里），
挂上成本极低、可以挂，但别当成已知生效的入口。

```powershell
# 不要用 WSL 的 ln -s 往 /mnt/c 建链接（LX 软链 Windows 程序读不到）
# <skills-root> 请替换为你自己的技能实体根（示例已脱敏）
New-Item -ItemType Junction `
  -Path   "$env:USERPROFILE\.workbuddy\skills\git-discipline" `
  -Target "<skills-root>\git-discipline"
```

> ⚠️ **Junction 目标仓库会静默落后**：本机 2026-10-12 实测四个 Junction 指向的克隆
> 落后 `origin/main` **14 个提交**，Agent 读到的是缺 v4「推送核验」条的旧技能且**零报错**。
> 定期复验：`git -C <skills-root> fetch && git -C <skills-root> status -sb`，
> 落后就 `merge --ff-only origin/main`。

---

## 备份位置

- 无 git 跟踪的用户级文件改前备份到 `E:\OpenCodeBackups\<类别>\<时间戳>`
  （与 opencode 同侧；CodeBuddy/WorkBuddy 目前**未**在权威托管块里单列备份根，
  暂归此处，改前核对备份盘可用与空间，改后逐文件校验）。
