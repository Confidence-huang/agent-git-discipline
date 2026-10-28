# 03 · Agent 适配

本文说明本方案适配哪些 AI 编码 Agent、每个 Agent 需要哪些配置文件、
入口提示词怎么写，并**明确标注验证状态**。

---

## 一、验证状态定义

本文对每条适配关系标注验证级别。请按级别决定你的信任程度：

| 标记 | 含义 | 判定依据 |
|---|---|---|
| ✅ **实测验证** | 观察到规则**实际生效** | 有会话记录、产物或运行时观察作为证据 |
| 🟡 **路径验证** | 配置位置与格式已确认，但未做端到端验证 | 文件布局 + 环境变量/默认值确认 |
| ⚠️ **文档依据** | 仅依据公开文档，**本机未验证** | 官方文档描述 |

> ⚠️ **注意**：⚠️ 级别的适配**可能不准确**。如果你实测发现与本文不符，欢迎提 issue 更正。
>
> 📌 第三～九节里的四家（Claude Code / Cursor / Gemini CLI / Aider）已按官方文档重写，
> 并配了可直接复制的样例（`configs/claude/`、`configs/cursor/`、`configs/gemini/`、`configs/aider/`），
> 依据与不确定项见 [06-未验证项的业界做法.md](06-未验证项的业界做法.md)。
> **2026-10-21 更新**：Gemini CLI 的规则入口已实测（0.64.0，见 §7），从 ⚠️ 升为
> ✅ **规则注入层**——但它的**真实模型后端**仍未验证（免费个人版登录被 Google 下线，
> 只能走 API key / Vertex）。其余三家仍是 ⚠️ 未验证——样例不等于实测。
>
> **2026-10-28 更新**：新增 **Google Antigravity**（§10）。规则发现与技能发现都在本机
> **实测**（App 2.27.0：`GetAllRules` / `GetAllSkills` / `GetTokenBase` 三个本地 RPC 都返回了
> 探针内容），因此标 ✅ **发现与注入层**。另有一条**反直觉结论**：Antigravity
> **不跟随 Junction/软链**读技能，靠 `skills.json` 清单引用才生效（§10.3）。
> **同日补测**：真会话里它按托管块走完了「核对边界 → 窄暂存 → 复核 → 原子提交 →
> 报编号」全流程，编号与 SHA 逐项核对一致（§10.6），**行为层也已实测**；
> 随后又在真项目里做了**项目块正反对照**（移除项目独有条款后行为随之改变），
> 证明项目级规则确实进上下文且优先生效（§10.6）。

---

## 二、适配总表

| Agent | 规则入口 | 技能支持 | 验证状态 |
|---|---|---|---|
| **Codex**（OpenAI） | `$CODEX_HOME/AGENTS.md`（默认 `~/.codex/AGENTS.md`） | 读 `<root>/.agents/skills` | ✅ 实测验证 |
| **opencode** | `~/.config/opencode/AGENTS.md` + 项目 `AGENTS.md` | **`~/.agents/skills/`**（1.18+ 自动加载；项目内 `.opencode/skills/`） | ✅ 实测验证 |
| **DeepSeek Harness (DSH)** | ❌ **不读 `AGENTS.md`** | `~/.agents/skills` 或 `<projectRoot>/.agents/skills` | ✅ 实测验证 |
| **CodeBuddy / WorkBuddy** | 用户级 `%USERPROFILE%\.codebuddy\CODEBUDDY.md`（+ `CODEBUDDY.local.md`）；项目 `AGENTS.md`（+ `AGENTS.mdc`），同目录若另有 `CODEBUDDY.md` 则**只读后者** | 用户级 `%USERPROFILE%\.workbuddy\skills\`（WorkBuddy 系）/ `%USERPROFILE%\.codebuddy\skills\`（CodeBuddy CLI 系）、项目级 `.codebuddy\skills\`、插件市场 `…\plugins\marketplaces\*\plugins\*\skills\` | ✅ 实测验证 |
| **Claude Code** | `CLAUDE.md`（项目 + 用户级） | `.claude/skills/` | ⚠️ 文档依据 |
| **Cursor** | `AGENTS.md` / `.cursor/rules/` | — | ⚠️ 文档依据 |
| **Gemini CLI** | `GEMINI.md`（默认名）里 `@AGENTS.md`，或项目/用户 `settings.json` 的 `context.fileName`；**默认不读 `AGENTS.md`** | `.agents/skills/`（docs/06 官方口径，本机未实测） | ✅ 实测验证（规则注入；真实模型端见 §7） |
| **Google Antigravity** | `AGENTS.md` / `GEMINI.md` **原生读取**（项目任意子目录 + 全局 `~/.gemini/`、`~/.gemini/config/`）；模块化规则 `.agents/rules/*.md` 或 `~/.gemini/config/rules/*.md`（**必须有 `trigger` frontmatter**） | `.agents/skills/`（工作区）、`~/.gemini/config/skills/`（全局）、`plugins/<name>/skills/`；**外部目录走 `skills.json` 清单** | ✅ 实测验证（发现层 + 全局/项目级行为层**正反对照**；**不跟随 Junction**，见 §10） |
| **Aider** | `AGENTS.md`（需在 `.aider.conf.yml` 声明） | — | ⚠️ 文档依据 |
| **GitHub Copilot coding agent** | `AGENTS.md` | — | ⚠️ 文档依据 |

**关键差异**：**DSH 不读 `AGENTS.md`，只加载技能。**
这是本方案必须同时提供「托管块」和「技能」两种载体的原因——见第四节。

---

## 三、逐 Agent 配置

### 1. Codex（OpenAI）✅ 实测验证

**规则入口**

```
$CODEX_HOME/AGENTS.md        # 全局（CODEX_HOME 未设置时默认 ~/.codex）
<project-root>/AGENTS.md     # 项目级，优先级更高
```

**配置方式**

```bash
# 1) 全局规则入口
cp configs/codex/AGENTS.global.example.md "$CODEX_HOME/AGENTS.md"

# 2) 项目级托管块
cp templates/AGENTS.project-skeleton.md /path/to/project/AGENTS.md
```

**入口提示词**（可选，用于显式触发）

```
按全局 Git 闭环执行：改前核对 Git 根与工作树，原子改动立即本地 commit，
禁止 git add . / -A，commit 后记「第 N 次 git」，最终回复最后一条普通文本写
「已git：<仓库> 第 N 次 git（commit <短SHA>）」。
```

（涉及**多个仓库**时**逐个仓库各写一行**；单仓库也**不省略** `<仓库>`，否则事后分不清是哪一份回报。）

**验证证据**：本项目使用者的既有会话记录中稳定产出
`已git：<仓库> 第 N 次 git（commit <短SHA>）` 格式回报；`CODEX_HOME` 未设置时默认
`~/.codex`，该路径下的 `AGENTS.md` 被读取。

**注意事项**

- Codex 的全局规则文件与项目 `AGENTS.md` **都会读**，存在覆盖关系：
  **就近者优先**（与 [agents.md 规范](https://agents.md/) 一致）。
- 若你同时用 WSL 和 Windows 两个 Codex，注意 `$CODEX_HOME` **是两套**
  （`~/.codex` 与 `%USERPROFILE%\.codex`），需要分别配置。

---

### 2. opencode ✅ 实测验证

**规则入口**

```
~/.config/opencode/AGENTS.md          # 全局（Linux/WSL）
%USERPROFILE%\.config\opencode\AGENTS.md   # 全局（Windows）
<project-root>/AGENTS.md              # 项目级
```

**配置方式**

```bash
cp configs/opencode/AGENTS.global.example.md ~/.config/opencode/AGENTS.md
cp templates/AGENTS.project-skeleton.md /path/to/project/AGENTS.md
```

**技能安装**（opencode 1.18+ **自动加载** `~/.agents/skills/`，不需要建 `~/.config/opencode/skills/`）

```bash
# 实体放共用根：DSH / Codex / opencode / WorkBuddy 都从这里发现
ln -s <skills-root>/git-discipline ~/.agents/skills/git-discipline
```

> ⚠️ **实测纠正（2026-10-12，opencode 1.18.25）**：旧文档写的 `~/.config/opencode/skills/`
> **不是**技能发现根。bundle 里的自动加载列表只有 `~/.agents/skills/<name>/SKILL.md` 与
> `~/.claude/skills/<name>/SKILL.md`（另有项目级 `.opencode/skills/`）。
> 更糟的是**从 WSL 用 `ln -s` 往 `/mnt/c` 下建链接，Windows 侧程序读不到**
> （LX 软链对 Windows 不可解析，实测 `Test-Path ...\SKILL.md` = False）；
> **Windows 侧必须用 `New-Item -ItemType Junction`**（Junction 实测可读）。

**入口提示词**

```
执行纪律与 Git 闭环见全局 AGENTS.md §9；本项目托管块已含 v6 规则。
```

**验证证据**：会话记录中出现 `提交完成（第 29 次 git）` 形式的回报，
且 `project_*` 各项目的 `AGENTS.md` 托管块被实际遵守。

**注意事项**

- opencode 的全局规则里若把 `commit` 列入"需确认"清单，会与项目托管块
  的"立即 commit"冲突——**必须二者取一**。本方案选择：本地 commit 默认授权。
- Windows 侧 `~/.config/opencode/` 目录本身常是 git 仓库，改动会进入版本控制。

---

### 3. DeepSeek Harness (DSH) ✅ 实测验证

**⚠️ 重要差异：DSH 不读 `AGENTS.md`。**

DSH 只从**技能根**发现规则。因此托管块对 DSH **无效**，必须用技能形态。

**技能发现路径**（rank 由小到大，就近优先）

| Rank | 来源 | 路径 |
|---|---|---|
| 100 | project-dsh | `<projectRoot>/.dsh/skills` |
| 200 | project-agents | `<projectRoot>/.agents/skills` |
| 400 | user-dsh | `$DSH_HOME/skills`（默认 `~/.dsh/skills`） |
| 500 | user-agents | `$DSH_AGENTS_HOME/skills`（默认 `~/.agents/skills`） |
| 600 | bundled | 随包提供的技能根 |

其中 `projectRoot` = **含 `.git` 的最近祖先目录**；都没有则用当前工作目录。

**技能格式要求**

- 目录 bundle：`<name>/SKILL.md`，或平铺文件 `<name>.md`
- **必填 frontmatter**：`name`（kebab-case）与 `description`
- **符号链接目录受支持**
- **刻意不支持**嵌套的 `**/SKILL.md` 发现

**配置方式**

```bash
./scripts/install_skill.sh --target agents-home
# 等价于：
ln -s <skills-root>/git-discipline ~/.agents/skills/git-discipline
```

**入口提示词**（DSH 会自动加载，通常无需显式触发）

```
涉及代码、脚本、配置或规则文件改动时，按 git-discipline 技能执行。
```

**验证证据**（**最强的一条**）：把 `SKILL.md` 写入技能根后，
**下一步**该技能即出现在会话的技能目录中，**无需重启**。

**注意事项**

- 技能正文用**懒加载**：只有 frontmatter 进目录，正文在调用时才读。
  因此**改正文无需重生效**，但改 frontmatter 会触发重新发现。
- `references/`、`assets/` 等**子目录下的编辑不触发**热加载。
- 由于技能优先于 `AGENTS.md` 生效，**两处规则若冲突，以技能为准**。

---

### 3.1 CodeBuddy / WorkBuddy（Windows 侧）✅ 实测验证

本机另有一个 CodeBuddy 系的 Windows 编码应用（WorkBuddy 桌面版 37.10.3-24，
内置 CLI bundle 2.156.0 / `resources/app.asar.unpacked/cli/dist/codebuddy-headless.js`）。
**2026-10-12 跑通了一次真实端到端会话**；本节据此重写，**推翻**旧版本节的 🟡 结论与技能根清单。

**规则入口**（下表每一行都由运行时日志实证，不是路径推断）

| 层级 | 路径 | 运行时观察 |
|---|---|---|
| 用户级 | `%USERPROFILE%\.codebuddy\CODEBUDDY.md`（+ `CODEBUDDY.local.md`） | `MemoryLoader` 打 `[user] [always] …\.codebuddy\CODEBUDDY.md` |
| 项目级 | `<项目目录>\AGENTS.md`（或 `AGENTS.mdc`） | `MemoryLoader` 打 `[project] [always] …\AGENTS.md` |
| 项目级（同目录优先） | `<项目目录>\CODEBUDDY.md` | 同目录**两个文件都在时只加载 `CODEBUDDY.md`**，`AGENTS.md` 被跳过 |
| 祖先目录 | 工作目录逐级向上找同名文件 | `%USERPROFILE%\CODEBUDDY.md` 会被当 `[project]` 读入 |

> ⚠️ **三个反直觉点（都实测过）**
> 1. `%USERPROFILE%\.workbuddy\CODEBUDDY.md` 与 `%USERPROFILE%\.workbuddy\AGENTS.md`
>    **都不读**——用户级入口在 `.codebuddy\` 下，不在应用数据目录 `.workbuddy\` 下；
> 2. 同目录内 `CODEBUDDY.md` **压过** `AGENTS.md`：想用项目托管块，就别在项目根再放 `CODEBUDDY.md`；
> 3. 把全局规则放 `%USERPROFILE%\CODEBUDDY.md` **并不全局**：它靠"祖先目录"被读到，
>    `D:\…` 下的项目看不到它，必须放 `%USERPROFILE%\.codebuddy\CODEBUDDY.md`。

**技能根**

| 来源 | 路径 | 依据 |
|---|---|---|
| 应用级（WorkBuddy 系） | `%USERPROFILE%\.workbuddy\skills\` | 应用自己的技能缓存 `.workbuddy\.skill-list-cache.json`：48 条里 `git-discipline` 的 `filePath` 在此，`source=userSettings` |
| 应用级（CodeBuddy CLI 系） | `%USERPROFILE%\.codebuddy\skills\` | bundle 里 `PathUtils.getHomeDir()` 随产品品牌变；**桌面应用不扫它**（2026-10-12 受控实验：只放该根的探针技能未被发现），它服务的是把同一份 bundle 当 CLI 起（`cbc`）的入口——那条路要登录，本机未做端到端 |
| 项目级 | `<项目>\.codebuddy\skills\` | bundle `getProjectSkillsDir()` |
| 插件市场 | `…\plugins\marketplaces\*\plugins\*\skills\`、`…\.workbuddy\skills-marketplace\`、内置 `…\resources\plugins\workbuddy-builtin\skills\` | 应用缓存里 48 条技能的实际分布 |
| ❌ **已否证**：`~/.agents/skills` | `%USERPROFILE%\.agents\skills\` | **受控实验（2026-10-12）**：新技能只放该根 → **不被发现**；同一时刻放 `%USERPROFILE%\.workbuddy\skills\` 的对照技能被发现（应用缓存 48 → 49 条，删回后 48）。bundle 里该路径也只出现在"允许写 / 排除备份"清单（旧版本节把它列为技能根，属误读） |

**接入方式**（与 DSH 同构：技能 + 托管块）

```powershell
# Windows 侧建 Junction；不要用 WSL 的 ln -s（Windows 程序读不到 LX 软链）
# <skills-root> 请替换为你自己的技能实体根（示例已脱敏）
New-Item -ItemType Junction `
  -Path   "$env:USERPROFILE\.workbuddy\skills\git-discipline" `
  -Target "<skills-root>\git-discipline"
```

> ⚠️ **Junction 目标仓库会静默落后**（2026-10-12 实测）：本机 Windows 侧四个 Junction
> 指向的克隆落后 `origin/main` **14 个提交**，于是 WorkBuddy 与 Windows 侧 Codex、opencode
> 读到的是**缺 v4「推送核验」条**的旧技能，**全程零报错**。修法与复验：
> `git -C <skills-root> fetch && git -C <skills-root> merge --ff-only origin/main`，
> 再用 `Select-String -SimpleMatch "ls-remote" "<junction>\SKILL.md"` 确认内容真的换了。

**受保护文件**：bundle 把 `CODEBUDDY.md`、`CODEBUDDY.local.md`、`.codebuddy/settings*.json`、
`.codebuddy/rules/`、`.codebuddy/skills/` 等视为"控制 agent 自身行为"的文件——
改动前按本仓库备份规则处理。

**验证证据（2026-10-12，一次性仓库 `D:\Workbuddy project\_wb-e2e-verify`）**

项目 `AGENTS.md` 里放托管块 v4 + 只有该文件才有的口令，然后在 WorkBuddy 里发一句
「把 note.md 末尾追加一行 …，然后按你当前生效的 Git 纪律处理这次改动」，一次会话内观察到：

1. 回复**原样复述**口令 `WB-PROJ-MARKER-20261012-1255` → 项目级入口确实进了上下文；
2. 自行执行「核对 Git 根 → 只 `git add note.md`（未用 `git add .`）→ 复核 `git diff --staged`
   → 原子提交」；落盘核验 `6c21188 chore: note.md 追加验证口令 wb-live-20261012-1255`，
   `1 file changed, 2 insertions(+)`，提交后工作树干净；
3. 回报写成托管块规定的形态 `已git：D:/Workbuddy project/_wb-e2e-verify 第 3 次 git（commit 6c21188）`，
   与 `git rev-list --first-parent --count HEAD` = 3 一致；
4. 主动声明「push / 远端核对属需单独授权，故未执行」——与 v4 的授权边界一致。

同日补做**技能根受控实验**（三个一次性探针技能，各放一个根，验完即删）：

| 探针放置位置 | 是否被应用发现 |
|---|---|
| `%USERPROFILE%\.workbuddy\skills\`（对照组） | ✅ 发现（应用缓存 48 → 49 条） |
| `%USERPROFILE%\.agents\skills\` | ❌ 未发现 |
| `%USERPROFILE%\.codebuddy\skills\` | ❌ 未发现 |

删掉三个探针后缓存回到 48 条、无残留 ⇒ 桌面应用的技能发现根**只有** `.workbuddy\skills`
（外加技能市场与内置插件目录）；`.codebuddy\skills` 服务的是 CLI 入口，`.agents\skills` 则完全无关。

---

### 4. 为什么必须同时提供两种载体

这是本项目最容易踩的架构坑：

| Agent | 读 `AGENTS.md` | 读技能 | 需要托管块 | 需要技能 |
|---|---|---|---|---|
| Codex | ✅ | ✅ | ✅ | 可选（细节） |
| opencode | ✅ | ✅ | ✅ | 可选（细节） |
| **WorkBuddy** | ✅（同目录另有 `CODEBUDDY.md` 时读后者） | ✅ | ✅ | 可选（细节） |
| **DSH** | ❌ | ✅ | ❌ | **必需** |

**结论**：只做 `AGENTS.md` → DSH 完全失效；只做技能 → Codex/opencode 的项目级投影缺失。

**本方案的答案**：
- **托管块** = 项目级投影（写进 `AGENTS.md`），三平台字节一致
- **技能** = 完整规则载体（供 DSH 加载，同时给 Codex/opencode 提供细节）
- 两者通过 `SKILL.md` 末尾的指针互相关联

---

### 5. Claude Code ⚠️ 文档依据

**规则入口**：`CLAUDE.md`（项目根 + 用户级 `~/.claude/CLAUDE.md`）

**配置方式**

```bash
# 把托管块复制进 CLAUDE.md（Claude Code 不读 AGENTS.md）
cat configs/block/GLOBAL-PROJECT-LOG-RULES.v6.md >> /path/to/project/CLAUDE.md
```

**兼容技巧**：若希望 `AGENTS.md` 与 `CLAUDE.md` 共用一份内容，可用符号链接：

```bash
mv CLAUDE.md AGENTS.md && ln -s AGENTS.md CLAUDE.md
```

**未验证**：本机无 Claude Code 环境，路径与读取行为均未实测。

---

### 6. Cursor ⚠️ 文档依据

**规则入口**：`AGENTS.md`（较新版本）或 `.cursor/rules/*.mdc`（旧版 `.cursorrules`）

**配置方式**

```bash
cp templates/AGENTS.project-skeleton.md /path/to/project/AGENTS.md
```

**未验证**：不同 Cursor 版本的规则文件格式差异较大，**未在本机验证**。

---

### 7. Gemini CLI ✅ 实测验证（规则注入；真实模型后端见下）

**实测版本**：`@google/gemini-cli@0.64.0`（Node v26.8.1，WSL2）。
另核对了 `0.65.0-preview.0`：OAuth client 未变，故未重跑全量。

**规则入口**

- **默认只认 `GEMINI.md`**：源码常量 `DEFAULT_CONTEXT_FILENAME = "GEMINI.md"`，
  整个 bundle 没有把 `AGENTS.md` 当默认上下文文件的路径。**只放 `AGENTS.md` 不会被读**（已实测，
  见下表第一行）。
- 两种接法（任选其一，可并存）：
  1. 项目根 `GEMINI.md` 里写一行 `@AGENTS.md`（`@` 导入）；
  2. 在 `settings.json` 里配 `context.fileName`（string 或 string[]，见 `configs/gemini/`）。
- 记忆文件层级：`~/.gemini/GEMINI.md` → 工作区及父目录（上溯至 git 根/home）→ JIT。
- 官方依据：<https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md> ·
  <https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md>

**实测结论**（2026-10-21；多个一次性临时仓库，用本地回环端点观察请求体）

| 场景 | 配置 | 结果 |
|---|---|---|
| 默认 | 只有 `AGENTS.md` | ❌ 规则**未**进入请求 |
| `@` 导入 | `GEMINI.md` 内容为 `@AGENTS.md` | ✅ 口令进入请求体并被回显 |
| `context.fileName` | 项目 `.gemini/settings.json`，**受信任目录** | ✅ 进入请求 |
| 同上 + `--skip-trust` | **未受信任**目录 | ❌ 项目 settings 被跳过，规则不生效 |
| 同上 + `GEMINI_CLI_TRUST_WORKSPACE=true` | **未受信任**目录 | ✅ 进入请求 |
| `context.fileName` 多值 | `["GEMINI.md","AGENTS.md"]` | ✅ **两个都加载**（不是按序回退） |
| `GEMINI.md` 在未受信任目录 | 配合 `--skip-trust` | ✅ 记忆文件仍加载（只有项目 settings 需要信任） |

> ⚠️ **坑：`--skip-trust` 只跳过信任提示，不等于受信任**。项目级 `.gemini/settings.json`
> 不会加载，`context.fileName` 于是静默失效。CI / headless 里有两条正路：
> 把目录写进 `~/.gemini/trustedFolders.json`（`{"<绝对路径>": "TRUST_FOLDER"}`），
> 或设 `GEMINI_CLI_TRUST_WORKSPACE=true`。**用户级** `~/.gemini/settings.json` 的
> `context.fileName` 则不受目录信任影响（未受信任目录里也生效，已实测）。

**验证方法（可复现）**

真实 Google 后端在本机不可用（原因见下），所以用本地回环端点验证「规则是否进入模型请求」：

```bash
# 一次性临时仓库：AGENTS.md 里放只有该文件才有的口令
printf 'E2E_TOKEN: GEM-E2E-01-7f3a91\n' > AGENTS.md
printf '@AGENTS.md\n' > GEMINI.md

# 让 CLI 指向本地桩；桩把请求体（systemInstruction + contents）落盘
GEMINI_API_KEY=test-local-key \
GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:8765 \
gemini -p '复述 E2E_TOKEN'
```

判定：请求体里出现 `GEM-E2E-01-7f3a91` 即「规则注入成功」。
这验证的是 **CLI 的规则发现与上下文注入**，不是 Google 模型本身。

**真实后端：⚠️ 免费个人版登录已被 Google 下线**（2026-10-21 实测）

- `gemini` 选「1. Sign in with Google」→ 浏览器授权 → 粘贴 code 后，CLI 明确报：
  `This client is no longer supported for Gemini Code Assist for individuals.`
  `To continue using Gemini, please migrate to the Antigravity suite of products: https://antigravity.google`
- 同一 OAuth client（`681255809395-…apps.googleusercontent.com`）在 `0.65.0-preview.0` 里**未变**。
- 结论：真实模型后端只能走 **`GEMINI_API_KEY`**（AI Studio）或 **Vertex AI**。
  本机 AI Studio 还撞上区域限制（打开 API key 页被重定向到 “available regions” 文档）。
- 所以本节 ✅ 的边界是：**规则入口与上下文注入已实测；Google 模型侧未实测**。

**技能**：`.agents/skills/` 与 `.gemini/skills/`（同层 `.agents/` 优先）是 docs/06 的官方口径，
**本机未实测**——技能激活需要真实会话里的 UI 确认，本地桩覆盖不到。

---

### 8. Aider ⚠️ 文档依据

**规则入口**：需在 `.aider.conf.yml` 中显式声明。

依据 [agents.md](https://agents.md/) 给出的配置：

```yaml
# .aider.conf.yml
read: AGENTS.md
```

**未验证**：未在本机安装 Aider。

---

### 9. GitHub Copilot coding agent ⚠️ 文档依据

**规则入口**：`AGENTS.md`

**未验证**：依赖 GitHub 侧托管环境，未做本地验证。

---

### 10. Google Antigravity ✅ 实测验证（发现层 + 全局行为层 + **项目级行为层正反对照**；边界见 §10.6）

**实测版本**：Antigravity App `2.27.0`（Electron 44.4.3 / Chrome 152，Windows 11，
语言服务 `language_server.exe` 版本 2.27.0）。同日核对官方文档
<https://antigravity.google/docs/rules> 与 <https://antigravity.google/docs/skills>，结论一致。

> 这是 Gemini CLI **迁移的目标产品**（Google 已下线 Gemini CLI 的免费个人版登录，提示 "migrate
> to the Antigravity suite of products"，见 §7）。两者规则文件名都叫 `AGENTS.md` /
> `GEMINI.md`，但**发现机制完全不同**，不要照搬 §7 的结论。

#### 10.1 规则入口（原生读 `AGENTS.md`，不需要 `@` 导入）

与 Gemini CLI **最大的差别**：Antigravity **默认就读 `AGENTS.md`**，不需要
`GEMINI.md` 里写 `@AGENTS.md`，也不需要配 `context.fileName`。

| 层级 | 路径 | 加载语义 |
|---|---|---|
| 目录级 | `<任意目录>/AGENTS.md`、`<任意目录>/GEMINI.md` | 从被读/被改文件所在目录**向上走到仓库根**，逐层加载；该目录及其子目录生效 |
| 目录级（点目录） | `<目录>/.agents/AGENTS.md`、`<目录>/.agents/GEMINI.md` | 同上 |
| 目录级（模块化） | `<目录>/.agents/rules/*.md`（旧版 `.agent/rules/*.md`） | **仅扫直接子文件**，嵌套子目录里的 `.md` 不会自动加载（需 `.agents/rules.json` 显式登记） |
| 全局 | `~/.gemini/AGENTS.md`、`~/.gemini/GEMINI.md` | 整机所有工作区，恒 `always_on` |
| 全局（config） | `~/.gemini/config/AGENTS.md`、`~/.gemini/config/GEMINI.md` | 同上 |
| 全局（模块化） | `~/.gemini/config/rules/*.md` | **必须有 frontmatter `trigger`** |
| CLI 专属 | `~/.gemini/antigravity-cli/rules/*.md` | 只有 Antigravity CLI 侧读 |
| 插件 | `<plugin>/rules/AGENTS.md` | 插件启用时随插件生效（无 frontmatter，纯 Markdown） |

**Windows 侧**把 `~` 换成 `%USERPROFILE%`（本机即 `C:\Users\<user>\.gemini\...`）。

#### 10.2 两个会让规则**静默失效**的格式陷阱

1. **`AGENTS.md` / `GEMINI.md` 不能带 frontmatter**（`[官方]` 口径：这两个文件整份当作
   纯 Markdown、恒定 `always_on`，不做元数据解析）。反之 **`.agents/rules/*.md` 与
   `~/.gemini/config/rules/*.md` 必须带 frontmatter**，且 `trigger` 只认
   `always_on` / `model_decision` / `glob` / `manual` 四个**小写蛇形**值。
   **`[实测]`** 四种写法各放一份探针，用 `GetAllRules` 读回：

   | 写法 | 结果 |
   |---|---|
   | `trigger: always_on` | ✅ 发现，`trigger=ALWAYS_ON` |
   | `trigger: model_decision` + `description` | ✅ 发现，`trigger=MODEL_DECISION`（只注入描述，正文按需读） |
   | `trigger: alwaysOn`（驼峰） | ❌ **整条静默丢弃**，无任何报错 |
   | 无 frontmatter | ❌ 同上 |

2. **体积上限**（`[官方]` 口径，本机未压测）：单文件 **24,000 字节**（按 `@[label](path)`
   展开后计算，超了按行截断）；全部 global + `always_on` 规则共享 **20,000 token** 预算，
   超了最大的几份会被**降级成 `- <path>: <description>` 路径指针**（模型只看到"有这么个规则"，
   看不到正文，得自己去读）。

> 📌 对托管块的含义：GLOBAL-PROJECT-LOG-RULES v6 全文 **9,471 字节**，
> 单份离 24 KB 上限有 2.5 倍余量；但全局规则是**累加**的，项目多了要算总账。
> **`[实测]`** `GetTokenBase` 会直接报 `rulesBudget` / `remainingRulesBudget` 与逐文件
> token 数，可作为巡检依据（见 §10.5）——本机基线：两份全局 `AGENTS.md` 各 12 token。

#### 10.3 技能发现：**不跟随 Junction / 软链**（本节最重要）

官方文档给出的路径是：

| 入口 | 路径 |
|---|---|
| 工作区 | `<workspace>/.agents/skills/<name>/SKILL.md`（旧版 `.agent/skills` 兼容） |
| 全局（App / IDE） | `~/.gemini/config/skills/<name>/SKILL.md` |
| 全局（CLI） | `~/.gemini/antigravity-cli/skills/<name>/SKILL.md` |
| 插件 | `<plugin>/skills/<name>/SKILL.md` |
| 清单 | `skills.json` 的 `entries[].path`（见下） |

**但"能不能被看见"取决于它是不是真目录**。2026-10-28 受控实验（每个探针单独放入、用
`GetAllSkills` 读回、验完即删）：

| 探针放置方式 | 是否被发现 |
|---|---|
| `~/.gemini/config/skills/<name>/`（真实目录） | ✅ 发现（`DISCOVERY_CATEGORY_INSTALLED`） |
| 同上位置放 **Junction**（目标在同盘 `%USERPROFILE%`） | ❌ 未发现 |
| 同上位置放 **Junction**（目标在另一块盘 `D:\...`） | ❌ 未发现 |
| 工作区 `.agents/skills/<name>/`（真实目录） | ✅ 发现（`DISCOVERY_CATEGORY_WORKSPACE`） |
| 工作区 `.agents/skills/<name>/` 放 **Junction** | ❌ 未发现 |
| `copy` 一份实体进 `config/skills/` | ✅ 发现 |
| **`skills.json` 的 `entries[].path` 指向外部实体目录** | ✅ 发现（`DISCOVERY_CATEGORY_CONFIG`，`discoveredIn` 就是 `skills.json`） |

> ⚠️ **这与 WorkBuddy / Codex 的结论正好相反**：那两家的 Windows 技能入口**必须**用
> Junction、且**读得到** Junction（见 §3.1）。所以"Windows 侧一律建 Junction"这条经验
> **不能套到 Antigravity 上**——套了会得到一个"看起来装好了、实际模型完全不知道"的假象。

**正确接法（推荐）**：实体留在你的技能仓（`<skills-root>/git-discipline/`），用清单引用：

```json
// %USERPROFILE%\.gemini\config\skills.json（全局）
{
  "entries": [
    { "path": "D:\\<你的技能实体根>\\skills" }
  ]
}
```

`path` 指向**技能父目录**（Antigravity 只扫它下一层，即 `path/<name>/SKILL.md`）；
绝对路径原样、`~/` 展开家目录、相对路径按**仓库根**解析。
工作区级同理放在 `<workspace>/.agents/skills.json`（同样是工作区级优先）。
样例见 [`configs/antigravity/skills.example.json`](../configs/antigravity/skills.example.json)。

**备选**：直接 `copy` 实体进 `~/.gemini/config/skills/`（能发现，但从此有两份拷贝，会漂移）。
**不要**用 Junction——那是唯一一种"表面成功、实际零效果"的做法。

#### 10.4 全局规则文件的三种接法（Junction 也不跟）

同一个受控实验的规则侧结论：

| 接法 | 结果 |
|---|---|
| `~/.gemini/AGENTS.md` 真实文件 | ✅ 发现（`DISCOVERY_CATEGORY_CONFIG`，恒 `always_on`） |
| `~/.gemini/config/AGENTS.md` 真实文件 | ✅ 发现（两份可并存，都会进上下文） |
| `~/.gemini/AGENTS.md` 放 **Junction** | ❌ 未发现（`GetAllRules` 返回空） |
| `~/.gemini/AGENTS.md` 放 **HardLink** | ✅ 发现 |

> 结论：**规则文件用硬链接或直接写实体，别用 Junction**。硬链接要求**同一卷**
> （`C:\Users\...` 内部可以），跨盘（D: → C:）只能走实体写入或复制。

#### 10.5 怎么自己复验（不需要开 GUI 会话）

Antigravity 的渲染进程带 DevTools 端口，语言服务同时提供 **connect 协议**的本地 HTTP 端点；
两者都只在 `127.0.0.1` 上，从 WSL 也能直接访问。复验三步：

```bash
# 1) 拿端口与 CSRF（Windows 侧）
#    DevToolsActivePort: %APPDATA%\Antigravity\DevToolsActivePort（第 1 行是端口）
#    语言服务端口:  %APPDATA%\Antigravity\logs\language_server.log 里两行——
#                   "listening on random port at <P1> for HTTPS (gRPC)"  ← RPC 走这个
#                   "listening on random port at <P2> for HTTP"           ← 打开它取 csrfToken
#    CSRF: GET http://127.0.0.1:<P2>/ 返回的 __APP_CONFIG__.csrfToken

# 2) 问技能 / 规则 / token 预算（WSL 里直接 curl 即可；注意是 https + -k）
curl -sk -X POST "https://127.0.0.1:<P1>/exa.language_server_pb.LanguageServerService/GetAllSkills" \
  -H "Content-Type: application/json" -H "x-codeium-csrf-token: <CSRF>" \
  -d '{"workspaceUris":[],"includeShadowed":true}'
# 换 GetAllRules / GetCustomizationStates / GetTokenBase 即可

# 3) 判定：目标技能的 path 出现在返回里 = 发现成功；
#    GetTokenBase 的 Rules/Skills 分组里出现它 = 真的进了上下文预算。
```

> `GetAllSkills` 会把 `SKILL.md` 正文一并返回（很大），只想看标题就自己 `jq`/`python3` 过滤。
> `workspaceUris` 用 `file:///C:/...` 形式；给空数组 = 只看全局。

#### 10.6 验证边界（这一节 ✅ 到底覆盖了什么）

- ✅ **已实测**：`AGENTS.md` / `GEMINI.md` / `.agents/rules/*.md` / `~/.gemini/config/rules/*.md`
  的发现与 `trigger` 语义；`skills.json` 清单引用；Junction 与 HardLink 的差异；
  `GetTokenBase` 的规则/技能预算统计。
- ✅ **行为层已实测**（2026-10-28，App 2.27.0，真会话）：在**无项目（outside-of-project）**
  会话里发一句「在 `C:\Users\Lenovo\agy-e2e-verify` 把 `note.md` 末尾追加一行，然后按你当前
  生效的 Git 纪律处理这次改动，并告诉我做了哪些 git 操作」，它**完整走完了托管块要求的闭环**：

  | 托管块条款 | 它的实际行为 | 独立核对 |
  |---|---|---|
  | 先确认仓库边界 | `git rev-parse --show-toplevel` → 报告仓库根；`git status` + `git branch --show-current` | 一致 |
  | 禁宽范围暂存 | 只 `git add note.md`，并自己说明"避免 `git add .` / `-A`" | `git show --stat` = **1 file changed** |
  | 复核暂存差异 | `git diff --staged` | 一致 |
  | 原子提交 | `git commit -m "docs: append E2E_OK to note.md"` | SHA `f1e1c08…` 与它自报**逐字节一致** |
  | 第 N 次 git 编号 | `git rev-list --first-parent --count HEAD` → 报"第 2 次" | 实为 **2**，一致 |
  | 回报格式 | 输出 `已git：agy-e2e-verify 第 2 次 git（commit f1e1c08）` | **完全符合托管块规定的形态**，含仓库名 |
  | push 需单独授权 | 未推送，只做本地提交 | 远端无变化 |

  另有一条**直接证据**：会话记录里出现「已分析 `git-discipline/SKILL.md#L1-205`」
  —— 它确实读了技能正文（不是只读描述），规则经由 §10.3 的 `skills.json` 清单进了上下文。

  ⚠️ 一个**易误判的点**：验完 `git status` 仍显示 ` M note.md`，看着像它漏提交。
  实测是**纯换行差异**（`git diff --ignore-all-space --quiet` 通过）：工作区末行 `0d0a`、
  blob 是 `0a`，Windows 侧写入 CRLF 而仓库无 `.gitattributes` 归一化所致。
  **它当时自述"工作区已干净"是准确的**——不要把这个 CRLF 假象记成"agent 漏了收尾"。

- ✅ **项目级规则的行为层也已实测，且做了正反对照**（2026-10-28 下午，App 2.27.0）：
  在一个真实项目（`D:\Antigravity project\rules`，绑定为 Antigravity 的 project）里，
  项目 `AGENTS.md` = 托管块 v6 + **三条只存在于本项目的条款**
  （commit message 必须以 `PROJBLOCK:` 开头、回报追加 `[project-block-active]`、一条口令）。
  先核对**三个标记字符串在全局 `AGENTS.md` 里 0 命中**，确保是干净对照：

  | | 项目块含独有条款 | 已把独有条款移除（反向对照） |
  |---|---|---|
  | commit message | `PROJBLOCK: 在 note.md 末尾追加 PROJ_TEST` ✅ | `chore: 在 note.md 末尾追加 REVERSE_TEST` ✅ 前缀消失 |
  | 回报后缀 | `已git：rules 第 2 次 git（commit 55861e3） [project-block-active]` ✅ | 无后缀 ✅ |
  | 口令复述 | `AGY_PROJ_MARKER_20261028_e7c4` 原样输出 ✅ | —（已移除，无从复述） |
  | 托管块闭环 | 窄暂存 / 复核 / 原子提交 / 报编号（第 2 次，实测一致） | 同样完整（第 4 次，实测一致） |

  ⇒ **因果成立**：行为随项目块内容变化而变化，不是"碰巧照做了全局规则"。
  反向对照那一轮仍按托管块完整提交并报编号，说明**项目块与全局块是叠加生效**的
  （项目条款追加约束，全局条款继续兜底）。
  它在该会话里读了 `AGENTS.md#L1-75` 与 `git-discipline/SKILL.md#L1-100 / #L101-160`，
  证明项目块与技能**同时**进了上下文。
- 📌 **做这个验证的正确姿势**（下次直接照做，别重走死路）：**不需要**建项目、**不需要**碰
  原生文件对话框。在"无项目"会话里用绝对路径下指令即可——agent 会自己 `cd` 到目标仓库。
  上一轮尝试失败，是因为一心想"先绑定工作区"，而绑定恰恰是最难自动化的一步（见下方失败记录）。
- ⚠️ Antigravity CLI（`agy`）与独立 IDE 的入口（本机只装了 App，
  `%USERPROFILE%\.gemini\agy.exe` 与 `antigravity-cli\` 都不存在；CLI/IDE 路径取自官方文档）。
- ❌ **子代理的 `workspace: branch` 在本机 Windows 环境不可用（已定位为产品缺陷）**。
  现象：无论哪个 git 仓库，`invoke_subagent(workspace: "branch")` 一律失败，原始报错
  （`language_server.log` 里 `fork.go:53`）：

  ```
  Failed to branch workspace file:///d:/<repo>: branch workspace not supported for VCS type Unknown
  falling back to original URI
  ```

  排查过程与结论（2026-10-28，逐条实测）：
  | 假设 | 结果 |
  |---|---|
  | 仓库没 remote | ❌ 加了可达 remote 仍失败 |
  | 路径含空格 | ❌ 换 `D:\agy-nospace-test`（无空格）仍失败 |
  | 盘符大小写（日志里是小写 `d:`） | ❌ `D:` / `d:` 都失败 |
  | 需要上游追踪 `branch.main.remote` | ❌ 补了仍失败 |
  | 工作区没登记给 LS | ❌ `AddTrackedWorkspace` 登记后 `GetWorkspaceInfos` 已能返回 `gitRootUri`，仍失败 |

  **真正的分界点在 RPC 参数**：`CreateWorktree` 传 `workspaceUri` 会 500
  （`fatal: not a git repository … exit status 128`），改传 **`repoPath`**（`D:/xxx` 形式）
  才返回 200。也就是说 **`fork.go` 传错了字段**——这正是 "VCS type Unknown" 的来源。

  **但即便走通 `repoPath`，产物也不可用**：返回的 `worktreeDirUri` 指向
  `~/.gemini/antigravity/worktrees/<repo>/<name>`，可该目录**并不存在**；
  `git worktree list` 显示它被记成了一个
  `<repo>/.git/worktrees/<name>/C:/Users/.../worktrees/...` 的畸形路径（`prunable`），
  `gitdir` 指针指向不存在的目录。⇒ **worktree 建到一半就断了，Antigravity 自己也用不了**。

  **对本项目的实际影响**：规则适配**不受影响**（`workspace` 缺省是 `inherit`，可用）；
  受影响的是"子代理并行改同一仓库"这类用法。若你需要这条，建议向 Google 报 issue，
  或在 Windows 上把它当**不可用功能**绕开（改用 `inherit` 串行，或把子代理指到另一个**独立克隆**）。
  已清理本机所有探针 worktree 与 `%USERPROFILE%\.gemini\antigravity\worktrees\` 残留。
- 📌 **端口会变**：Antigravity 每次重启都重新分配端口（本轮就经历过 14446/14448 →
  1183/1185/1186）。复验前**必须现读** `DevToolsActivePort` 与 `language_server.log`，
  不要复用上一轮的端口号。

<details>
<summary>附：一次失败的自动化尝试（2026-10-28，留作反面教材）</summary>

目标同上，但当时想先"把工作区绑定成测试仓库"，两条路都走不通：

- **语言服务 RPC 直起会话**：`StartCascade` 报 `CortexTrajectorySource is unspecified`；
  `trajectorySource` 放顶层 / `configOverrides` / `environment` 均无效，
  `trajectory_source` 只出现在 `CortexStep` / `Trajectory` 等**下游消息**上，
  `StartCascadeRequest` 本身没有该字段（Go protobuf tag 与二进制字符串均核对过）。
- **CDP 驱动 GUI**：能点开"创建项目"、能触发原生 `Open workspace` 文件选择框，
  但对话框内的路径输入（UIA `AutomationId=1152`）`SetValue` 不落盘、确认按钮时有时无。

教训：**验证行为层根本不需要绑定工作区**。绕开这一步，问题立刻消失。
</details>

---

## 四、多 Agent 共存时的优先级

当同一台机器上跑多个 Agent 时，规则冲突的处理顺序：

```
用户当前会话中的明确指令
        ↓ 覆盖
项目级规则（<project>/.agents/skills 或 <project>/AGENTS.md）
        ↓ 覆盖
用户级规则（~/.agents/skills 或 $CODEX_HOME/AGENTS.md）
        ↓ 覆盖
随包提供的默认
```

这条优先级链与 [agents.md 官方规范](https://agents.md/) 一致：
**"离被编辑文件最近的生效；用户聊天中的明确指令覆盖一切。"**

**本方案在托管块内显式写入了这条**，使 Agent 无须外部知识即可正确裁定冲突。

---

## 五、跨平台双份配置的坑

同一个 Agent 在 WSL 和 Windows 上**有两套独立的配置目录**：

| | WSL / Linux | Windows |
|---|---|---|
| Codex | `~/.codex/AGENTS.md` | `%USERPROFILE%\.codex\AGENTS.md` |
| opencode | `~/.config/opencode/AGENTS.md` | `%USERPROFILE%\.config\opencode\AGENTS.md` |
| 技能根 | `~/.agents/skills` | `%USERPROFILE%\.agents\skills` |

**踩过的坑**：只配了 Windows 侧，于是 WSL 侧的 Agent 完全拿不到规则，
表现为"全局 git 身份都没设置、也没人提交"。

**检查清单**

```bash
# WSL 侧
ls -la "$HOME/.codex/AGENTS.md" "$HOME/.config/opencode/AGENTS.md" "$HOME/.agents/skills"

# Windows 侧（从 WSL 访问）
ls -la /mnt/c/Users/*/.codex/AGENTS.md /mnt/c/Users/*/.config/opencode/AGENTS.md
```

**建议**：用 `scripts/verify_blocks.py` 的多根模式一次性核验两侧。
