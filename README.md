# agent-git-discipline

[![CI](https://github.com/Confidence-huang/agent-git-discipline/actions/workflows/ci.yml/badge.svg)](https://github.com/Confidence-huang/agent-git-discipline/actions/workflows/ci.yml)

> 让 AI 编码 Agent **每次改动都留下可回退的点**，并把这条纪律机械地同步到多个 Agent、多个项目、多个平台。

写给同时使用多个 AI 编码 Agent（Codex / opencode / DeepSeek Harness / CodeBuddy·WorkBuddy / Claude Code / Cursor / …）的人：
规则写在五个地方、格式各不相同、改了一处忘了另一处，最后**一处都不可靠**。

---

## 一句话

```
能回退  =  干净起点  +  每步提交
```

git **撤不掉"未跟踪的新文件"**。如果 Agent 新建了若干文件却没提交，`git checkout`
对它们完全无效——只能手动删。所以"改完就提交"不是形式主义，它是安全网的**唯一**实现方式。

## 为什么需要它

真实踩过的三类断裂（详见 [docs/02-实践经验.md](docs/02-实践经验.md)）：

| 断裂 | 表现 | 后果 |
|---|---|---|
| **规则不落地** | 规则只写在 staging 目录，没有下发到任何活项目 | Agent 读到的规则里根本没有"要提交" |
| **规则自相矛盾** | 一处写"日志机制永不 commit"，另一处写"原子改动立即 commit" | Agent 选择不提交，**回退点为零** |
| **规则格式漂移** | 同一份托管块在 22 个项目里长出 5 种标记格式 | 无法机械同步，每次升级只能人眼比对 |

## 设计五要素

1. **单一事实源** —— 一份权威块模板 + 各项目的投影，块内容**字节一致**可用 SHA256 机械验证。
2. **配对标记 + 版本号** —— `<!-- GLOBAL-PROJECT-LOG-RULES:START v6 -->` … `:END`，
   整段可替换，不再靠人眼定位块边界。
3. **平台中立** —— 块内不写死盘符或路径，按平台列出取值，使同一份字节在
   WSL / Windows / macOS 通用。
4. **可回退编号** —— 每次 commit 记「第 N 次 git」，把 SHA 包装成人能用的序号；
   你说"退回到第 20 次"即可定位。
5. **推送以远端为准** —— `git push` 的**输出不可信**：实测出现过"报错的同时打印
   `Everything up-to-date`"而远端**实际没收到**。推送后必须 `git ls-remote origin <branch>`
   （或 `git fetch` + 比对 SHA）核对；不一致按**失败**处理。链路抖动属可重试错误，
   命令与处置见 [docs/05-提交与PR流程.md](docs/05-提交与PR流程.md) §三 步骤 3。

## 仓库结构

```
.
├── README.md                    # 本文件：总入口
├── docs/                        # 五类文档
│   ├── 01-参考来源.md            # 参考的开源仓库、借鉴点、差异、许可证注意事项
│   ├── 02-实践经验.md            # 踩过的坑 / 已验证做法 / 未解决问题（含复现步骤）
│   ├── 03-Agent适配.md           # 各 Agent 的配置文件、入口提示词、使用方法
│   ├── 04-环境支持.md            # WSL / Windows / macOS 平台差异与陷阱
│   ├── 05-提交与PR流程.md        # 推送/PR 授权边界、分支判据、标题与描述规范
│   └── 06-未验证项的业界做法.md   # ⚠️ 那些没验证的项，别人怎么做（含许可证与依据 URL）
├── skills/git-discipline/       # 技能本体（Agent 可直接加载）
│   ├── SKILL.md                 #   主规则：授权边界、原子提交、编号回报、回退分级
│   └── references/              #   回退手册等按需加载的细节
├── configs/                     # 示例配置（已脱敏）
│   ├── block/                   #   托管块权威模板（**v6 生效**；v4/v5 保留作历史）
│   ├── codex/                   #   Codex 全局规则示例
│   ├── opencode/                #   opencode 全局规则示例
│   ├── codebuddy/               #   CodeBuddy / WorkBuddy 全局规则示例（CODEBUDDY.md）
│   ├── claude/                  #   Claude Code 项目级 CLAUDE.md 示例（@AGENTS.md 导入）
│   ├── cursor/                  #   Cursor .cursor/rules/*.mdc 示例
│   ├── gemini/                  #   Gemini CLI GEMINI.md 与 settings.json 示例
│   ├── antigravity/             #   Google Antigravity 全局 AGENTS.md 与 skills.json 示例
│   └── aider/                   #   Aider .aider.conf.yml 示例（read: AGENTS.md）
├── scripts/                     # 功能脚本
│   ├── sync_block.py            #   把权威块同步进任意数量的项目
│   ├── verify_blocks.py         #   校验各项目块是否字节一致（CI 可用）
│   └── install_skill.sh         #   把技能装到各 Agent 的发现路径
├── templates/                   # 项目 AGENTS.md 骨架
└── local/                       # 【不发布】本机真实配置（已 .gitignore）
```

## 快速开始

### 1. 装技能（让 Agent 自动加载规则）

```bash
# 装到 DSH / 跨 Agent 共用根
./scripts/install_skill.sh --target agents-home

# 装到指定项目（优先级更高）
./scripts/install_skill.sh --target project --project-root /path/to/project
```

### 2. 给项目加托管块

把 [`configs/block/GLOBAL-PROJECT-LOG-RULES.v6.md`](configs/block/GLOBAL-PROJECT-LOG-RULES.v6.md)
的正文整段复制进项目的 `AGENTS.md`，或直接用骨架：

```bash
cp templates/AGENTS.project-skeleton.md /path/to/project/AGENTS.md
```

### 3. 批量同步与校验

先把你的真实目标写进 `local/targets.txt`（该文件不被提交），或直接传路径：

```bash
# 生成真实清单（示例）
ls /path/to/projects/*/AGENTS.md > local/targets.txt

# 同步（先 dry-run，确认无误再加 --apply）
python3 scripts/sync_block.py --block <你的块文件> --targets local/targets.txt
python3 scripts/sync_block.py --block <你的块文件> --targets local/targets.txt --apply \
        --backup-dir <备份根>/block-sync-$(date +%Y%m%d-%H%M%S)

# 校验：全部一致才算成功（退出码 0/1，可直接用于 CI）
python3 scripts/verify_blocks.py --block <你的块文件> --targets local/targets.txt
```

### 4. 按 Agent 配置入口

见 [docs/03-Agent适配.md](docs/03-Agent适配.md)。各 Agent 的规则入口与当前**验证状态**
（✅ = 已实测 / ⚠️ = 未验证；验证级别与每条的**证据边界**见 docs/03 §一）：

| Agent | 规则入口 | 状态 |
|---|---|---|
| Codex (OpenAI) | `$CODEX_HOME/AGENTS.md` | ✅ 已验证 |
| opencode | `~/.config/opencode/AGENTS.md` + 项目 `AGENTS.md`（技能自动加载 `~/.agents/skills/`） | ✅ 已验证 |
| DeepSeek Harness (DSH) | `<skill-root>/<name>/SKILL.md` | ✅ 已验证 |
| CodeBuddy / WorkBuddy | 用户级 `%USERPROFILE%\.codebuddy\CODEBUDDY.md`（+ `CODEBUDDY.local.md`）+ 项目 `AGENTS.md`（同目录另有 `CODEBUDDY.md` 时读后者） | ✅ 已验证 |
| Claude Code | 项目 `CLAUDE.md` 里写 `@AGENTS.md`（**默认不读 AGENTS.md**，样例见 `configs/claude/`） | ⚠️ 未验证（样例已按官方文档给出） |
| Cursor | 根/子目录 `AGENTS.md` 原生读取；可选 `.cursor/rules/*.mdc`（见 `configs/cursor/`） | ⚠️ 未验证 |
| Gemini CLI | `GEMINI.md` 里 `@AGENTS.md`，或配 `context.fileName`（见 `configs/gemini/`）；**默认不读 `AGENTS.md`** | ✅ 已验证（规则注入实测；真实模型后端需 API key/Vertex，见 docs/03 §7） |
| Google Antigravity | `AGENTS.md` / `GEMINI.md` **原生读取**（项目子目录 + 全局 `%USERPROFILE%\.gemini\`、`…\.gemini\config\`）；技能走 `.agents/skills/`、`…\.gemini\config\skills\`，**外部实体用 `skills.json` 清单引用**（见 `configs/antigravity/`） | ✅ 已验证（发现层 + 全局/项目级行为层**正反对照**；**不跟随 Junction**，见 docs/03 §10） |
| Aider | `.aider.conf.yml` 的 `read: [AGENTS.md]`（**无技能机制**，见 `configs/aider/`） | ⚠️ 未验证 |
| GitHub Copilot coding agent | 根 `AGENTS.md` **零配置生效**（含嵌套）；技能走 `.agents/skills/` | ⚠️ 未验证（官方文档口径） |

## 验证状态一览

本项目刻意区分**已验证**与**未验证**：

- ✅ **已验证**：块字节一致性校验、四条回退链路（`revert` / 按编号反查 / 单文件恢复 /
  `reflog` 兜底）、Git 身份缺失导致无法提交、暂存区滞留、DrvFs `cp -p` 失败、
  技能热加载（无需重启）、**opencode 的技能自动加载根是 `~/.agents/skills/`**
  （1.18.25 实测；`~/.config/opencode/skills/` **不是**发现根）、
  **Windows 侧技能入口必须用 Junction**（WSL 建的是 LX 软链，Windows 程序读不到）、
  **公开仓库的分支保护 + PR 门禁**（实测直推 `main` 被 `GH006` 拒绝）、
  **`git worktree` 的身份判据**（`--git-common-dir` 在主工作树返回**相对** `.git`、
  linked worktree 返回**绝对路径** ⇒ 必须 `--path-format=absolute` + `realpath` 才能比；
  实测同一分支二次检出被官方拒绝）、**入库钩子必须有执行位**（否则被静默忽略；
  本仓库 `.githooks/pre-push` 已是 `-rwxr-xr-x`）、
  **WorkBuddy 端到端规则生效**（2026-10-12 真实会话：项目 `AGENTS.md` 里只有该文件才有的口令
  被原样复述、它自行按托管块做了原子提交并写成 `已git：<仓库> 第 N 次 git（commit …）` 形态，
  编号与 `git rev-list --first-parent --count HEAD` 一致；同时**推翻**两处旧结论——
  用户级入口是 `%USERPROFILE%\.codebuddy\CODEBUDDY.md`（不是 `.workbuddy\`）、
  `%USERPROFILE%\.agents\skills\` **不是**它的技能发现根（同日受控实验：该根放探针技能不被发现，
  同一时刻放 `.workbuddy\skills\` 的对照技能被发现，缓存 48 → 49 条））、
  **Junction 目标仓库静默落后**（实测落后 `origin/main` 14 个提交，WorkBuddy 与
  Windows 侧 Codex、opencode 读到的是缺 v4「推送核验」条的旧技能，**全程零报错**）、
  **`git worktree` 的运行期副本风险与安全退休**（2026-10-13 实测：同一仓库两个 worktree 各有一份
  `tools/`，两份**同名**脚本对**同一个事实**给出**相反判据**，据此得出的结论是错的 ——
  识别信号 = 输出与仓库既有决定相反；退休路径已走通：三道核对 → `git worktree remove`
  （**不加 `--force`**）→ 四项验证。见 [docs/06](docs/06-未验证项的业界做法.md) §三）、
  **Antigravity 的项目级规则正反对照**（2026-10-28、App 2.27.0：真项目里项目 `AGENTS.md`
  加了三条独有条款 → commit message 变成 `PROJBLOCK:`、回报追加 `[project-block-active]`、
  口令原样复述；把三条移除后 → 前缀退回 `chore:`、后缀消失，而托管块闭环照旧。
  三个标记字符串在全局 `AGENTS.md` 里 0 命中，故是干净对照。见 docs/03 §10.6）、
  **Antigravity 的全局行为层闭环**（2026-10-28、App 2.27.0 真会话：无项目会话里下一句指令，
  它先 `git rev-parse --show-toplevel` 核对边界、只 `git add note.md`、`git diff --staged` 复核、
  原子提交并报 `已git：agy-e2e-verify 第 2 次 git（commit f1e1c08）`——编号与 SHA 与
  `rev-list`/`rev-parse` 逐项一致，且未推送。会话记录里可见它"已分析 git-discipline/SKILL.md#L1-205"，
  证明技能正文真的进了上下文。见 docs/03 §10.6）、
  **Gemini CLI 的规则注入**（2026-10-21、0.64.0：临时仓库 `AGENTS.md` 里的口令出现在
  **模型请求体**并被回显；`context.fileName` 多值时**全部加载**；**默认不读 `AGENTS.md`**；
  项目级 `.gemini/settings.json` 只在**受信任目录**生效——`--skip-trust` 不加载它，
  `GEMINI_CLI_TRUST_WORKSPACE=true` 才会。模型侧是**本地回环端点**，真实 Google 后端未验证，
  见 docs/03 §7 与下文 ⚠️）、
  **Google Antigravity 的规则/技能发现**（2026-10-28、App 2.27.0：`AGENTS.md` **原生读取**
  ——项目任意子目录 + 全局 `~/.gemini/` 与 `~/.gemini/config/`，不需要 `@` 导入；
  `.agents/rules/*.md` 缺 `trigger` 或写成驼峰 → **整条静默丢弃**；单文件 24 KB、
  全局规则 20,000 token 预算，超了降级成路径指针；**技能侧不跟随 Junction/软链**
  ——真目录与 `skills.json` 清单能发现，Junction（同盘/跨盘都试了）不能；
  规则文件 Junction 不能、HardLink 能。见 docs/03 §10）
- ⚠️ **未验证**：macOS 平台、`git worktree` 在**多 agent 并行**下的端到端回归、
  pre-commit 钩子强制（客户端钩子只是早筛：官方有 `--no-verify`，且 `core.hooksPath`
  **不在** Git protected configuration 名单里，还能 `-c core.hooksPath=/dev/null` 一次性禁掉）、
  **多人**协作的 PR 评审流程（本项目为单人仓库——官方明确**作者不能批准自己的 PR**，
  PR 流程本身已在公开仓库实测四轮，缺的是第二个人；见
  [docs/05-提交与PR流程.md](docs/05-提交与PR流程.md) 第八节）、
  Claude Code / Cursor / Aider 的**端到端规则生效**（本机已装 Claude Code，其 CLI 还需单独登录；
  Cursor / Aider **本机未安装**；样例见 `configs/`，但**样例 ≠ 实测**）、
  **Antigravity CLI(`agy`) 与独立 IDE**（App 侧的全局层与项目级层都已实测，见下一条；
  但本机没装 `agy`，两个入口取自官方文档）、
  **Gemini CLI 的真实模型后端**（规则注入已实测，但 0.64.0 的免费个人版登录已被 Google 下线：
  报 `This client is no longer supported for Gemini Code Assist for individuals`，提示迁移
  Antigravity；`0.65.0-preview.0` 的 OAuth client 未变。真实后端只能走 `GEMINI_API_KEY` 或
  Vertex AI——见 docs/03 §7）
- ❌ **已知未解决**：仅本地仓库无异地备份。本机**已有** `bak-local-archives`
  （私有仓库 + systemd 定时打 `git bundle` 推 GitHub），但**覆盖不全**：实测全机 90 个 git 仓库里
  **50 个既无远端、也不在它的清单里**（含 411 提交、95 提交那类），整棵 `CodexProjects/` 从未纳入；
  且 bundle **覆盖不到** `~/.codex/AGENTS.md` 这类无 git 跟踪的用户级规则文件。
  详见 [docs/02-实践经验.md](docs/02-实践经验.md) 第五节与
  [docs/06-未验证项的业界做法.md](docs/06-未验证项的业界做法.md) §六

> 每一项的**业界做法、官方依据 URL 与逐个核实的许可证**见
> [docs/06-未验证项的业界做法.md](docs/06-未验证项的业界做法.md)；
> 该文同时给出「哪些能照做、哪些仍不确定」。

## 持续集成

仓库自带 [`.github/workflows/ci.yml`](.github/workflows/ci.yml)，在每次推送与 PR 上运行三步：

| 步骤 | 脚本 | 拦什么 |
|---|---|---|
| 托管块一致性 | `scripts/verify_blocks.py` | 改了权威块却忘了同步 `templates/` 骨架 —— **本仓库的核心不变量** |
| 仓库一致性 | `scripts/check_repo.py` | 技能 frontmatter 缺失/非 kebab-case、文本文件混入 CRLF、脚本语法错误、被跟踪却缺失的文件 |
| 安装脚本冒烟 | `scripts/install_skill.sh` | 在隔离 HOME 下验证 link 与 copy 两种模式，并确认 copy 不带入 `.git` |

本地预演（与 CI 等价）：

```bash
python3 scripts/verify_blocks.py \
  --block configs/block/GLOBAL-PROJECT-LOG-RULES.v6.md --targets targets.txt
python3 scripts/check_repo.py
```

**给自己的部署加同样的门禁**：把你自己的块文件与 `local/targets.txt` 放进一个私有仓库，
用同样的 workflow 校验。这样任何人在项目里手改了块，PR 阶段就会被拦下。

### 客户端门禁（`.githooks/pre-push`）

仓库自带 `.githooks/pre-push`，跑的就是上面那两步。钩子文件入库，
但 `core.hooksPath` 是**仓库级配置、不入库**，所以克隆后需手动启用一次：

```bash
git config core.hooksPath .githooks
```

**为什么非要这一道**：免费私有仓库**拿不到** GitHub 分支保护
（API 返回 `Upgrade to GitHub Pro or make this repository public`），
客户端钩子是唯一能在本机落地的强制点。逃生口是 `git push --no-verify`——
门禁是减速带，不是牢门。详见 [docs/05-提交与PR流程.md §六](docs/05-提交与PR流程.md)。

**本仓库自身是例外**：它是**公开**仓库，因此**有**服务端分支保护——
`main` + `enforce_admins: true` + 必需检查 `一致性检查`。直推会被服务端拒绝：

```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: - Required status check "一致性检查" is expected.
```

所以对本仓库的改动一律走：**建分支 → push → 开 PR → 等 CI 绿 → rebase-and-merge**
（`--delete-branch=false` 保留源分支；合并后的收尾见
[docs/05-提交与PR流程.md §6.2/§6.3](docs/05-提交与PR流程.md)）。

提交与 PR 的完整流程——授权边界、什么时候才该开 PR、标题与描述模板、PR 阶段的回退——
见 [docs/05-提交与PR流程.md](docs/05-提交与PR流程.md)。

## 双版本说明

仓库分两份：

- **公开版**（本仓库）：用户名、盘符、服务路径、内部项目名均已替换为占位符，保留方法与结构。
- **本地真实版**：放在 `local/`，已被 `.gitignore` 排除，永不提交，仅本机对照用。

### 占位符一览

采用前请替换（块模板与示例配置中出现的）：

| 占位符 | 含义 | 示例 |
|---|---|---|
| `<盘符>` | Windows 备份盘符 | `E` |
| `<小写盘符>` | 对应的 WSL 挂载名 | `e`（即 `/mnt/e`） |
| `<类别>` / `<时间戳>` | 备份批次名与时间戳 | `rules-v2` / `20260928-120000` |
| `{{PROJECT_NAME}}` 等 | 项目骨架模板变量 | `my-project` |

### ⚠️ 校验要用**你自己的**块文件

`configs/block/GLOBAL-PROJECT-LOG-RULES.v6.md` 是**带占位符的模板**。
替换占位符后，请把它（或你的副本）作为**权威块**，再用它校验部署：

```bash
# 正确：用你自己的块
python3 scripts/verify_blocks.py --block local/block/GLOBAL-PROJECT-LOG-RULES.v6.local.md \
        --targets local/targets.txt

# 错误：用仓库里的公开模板去校验已填值的部署 —— 必然报"不一致"
```

这是**预期行为**：模板与填值后的实例本来就不同，校验比的正是"你的部署是否都等于你指定的那一份"。

### 🧭 本机清单别手写：用 `find_block_targets.py` 扫出来

`local/targets.txt` 是**本机**清单（`local/` 被 `.gitignore` 排除，不入库）。
手写它会**静默漏掉**带块的文件——2026-10-12 实测：一次 v4 → v5 全量升级按手写清单升了 20 个目标，
脚本一扫才发现另有 **9 个从未登记的部署件还停在 v3**（其中 8 个是正在被投影成 DSH 技能的"项目规则"源），
全程没有任何报错。所以：

```bash
# 生成本机清单（先看输出，再决定是否覆盖）
python3 scripts/find_block_targets.py \
    --root ~/projects --root /mnt/d/opencode_project \
    --exclude '*/agent-git-discipline/*' --exclude '*/test_run_*/*' > local/targets.txt

# 查漂移 / 定时巡检：有增删就退出码 1
python3 scripts/find_block_targets.py --root … --diff local/targets.txt

# 看每个部署件的块版本（找出"静默停在旧版本"的那些）
python3 scripts/find_block_targets.py --root … --json
```

判定规则有意收窄：**只看 `AGENTS.md` / `AGENTS.mdc` / `AGENTS*.md`**，且文件里必须**成对**出现
`:START` 与 `:END` 标记——这样投影产物（`RULES.md` / `SKILL.md`）、文档里的**引用**、
历史快照都不会被误当成部署件。工具仓自己的副本与一次性测试目录用 `--exclude` 排掉。

## 许可证

本项目代码与文档采用 [MIT](LICENSE)。

**注意事项**：本项目在写作时参考了若干开源项目，其中两个许可证需要特别当心——

- [langfuse/langfuse](https://github.com/langfuse/langfuse) 是**混合许可**：
  `ee/`、`web/src/ee/`、`worker/src/ee/` 目录走商业许可，其余为 MIT Expat。
  本项目只参考了其 `.agents/skills/` 下的内容，属于 MIT 部分。
- [Conventional Commits](https://www.conventionalcommits.org/) 的**仓库代码**是 MIT，
  但其**规范正文**采用 CC BY 3.0，引用正文需按 CC BY 署名。

完整出处与逐条差异见 [docs/01-参考来源.md](docs/01-参考来源.md)。

## 致谢

本项目的规则形态来自与使用者的长期协作，其中「托管块」「第 N 次 git 编号」
「规则同步硬门槛」等设计是使用者既有体系的沉淀，本项目负责把它们收敛、统一并机械可校验。
