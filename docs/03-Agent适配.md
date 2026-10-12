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
> 它们**仍然是 ⚠️ 未验证——样例不等于实测**。

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
| **Gemini CLI** | `AGENTS.md`（需在 `.gemini/settings.json` 声明） | — | ⚠️ 文档依据 |
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
执行纪律与 Git 闭环见全局 AGENTS.md §9；本项目托管块已含 v5 规则。
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
cat configs/block/GLOBAL-PROJECT-LOG-RULES.v5.md >> /path/to/project/CLAUDE.md
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

### 7. Gemini CLI ⚠️ 文档依据

**规则入口**：默认不读 `AGENTS.md`，需显式声明。

依据 [agents.md](https://agents.md/) 给出的配置：

```json
// .gemini/settings.json
{ "context": { "fileName": "AGENTS.md" } }
```

**未验证**：未在本机安装 Gemini CLI。

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
