# agent-git-discipline

[![CI](https://github.com/Confidence-huang/agent-git-discipline/actions/workflows/ci.yml/badge.svg)](https://github.com/Confidence-huang/agent-git-discipline/actions/workflows/ci.yml)

> 让 AI 编码 Agent **每次改动都留下可回退的点**，并把这条纪律机械地同步到多个 Agent、多个项目、多个平台。

写给同时使用多个 AI 编码 Agent（Codex / opencode / Claude Code / Cursor / …）的人：
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

## 设计四要素

1. **单一事实源** —— 一份权威块模板 + 各项目的投影，块内容**字节一致**可用 SHA256 机械验证。
2. **配对标记 + 版本号** —— `<!-- GLOBAL-PROJECT-LOG-RULES:START v2 -->` … `:END`，
   整段可替换，不再靠人眼定位块边界。
3. **平台中立** —— 块内不写死盘符或路径，按平台列出取值，使同一份字节在
   WSL / Windows / macOS 通用。
4. **可回退编号** —— 每次 commit 记「第 N 次 git」，把 SHA 包装成人能用的序号；
   你说"退回到第 20 次"即可定位。

## 仓库结构

```
.
├── README.md                    # 本文件：总入口
├── docs/                        # 四类文档
│   ├── 01-参考来源.md            # 参考的开源仓库、借鉴点、差异、许可证注意事项
│   ├── 02-实践经验.md            # 踩过的坑 / 已验证做法 / 未解决问题（含复现步骤）
│   ├── 03-Agent适配.md           # 各 Agent 的配置文件、入口提示词、使用方法
│   └── 04-环境支持.md            # WSL / Windows / macOS 平台差异与陷阱
├── skills/git-discipline/       # 技能本体（Agent 可直接加载）
│   ├── SKILL.md                 #   主规则：授权边界、原子提交、编号回报、回退分级
│   └── references/              #   回退手册等按需加载的细节
├── configs/                     # 示例配置（已脱敏）
│   ├── block/                   #   托管块权威模板
│   ├── codex/                   #   Codex 全局规则示例
│   └── opencode/                #   opencode 全局规则示例
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

把 [`configs/block/GLOBAL-PROJECT-LOG-RULES.v2.md`](configs/block/GLOBAL-PROJECT-LOG-RULES.v2.md)
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

见 [docs/03-Agent适配.md](docs/03-Agent适配.md)。已被本项目**实测验证**的组合：

| Agent | 规则入口 | 状态 |
|---|---|---|
| Codex (OpenAI) | `$CODEX_HOME/AGENTS.md` | ✅ 已验证 |
| opencode | `~/.config/opencode/AGENTS.md` + 项目 `AGENTS.md` | ✅ 已验证 |
| DeepSeek Harness (DSH) | `<skill-root>/<name>/SKILL.md` | ✅ 已验证 |
| Claude Code / Cursor / Gemini CLI / Aider | 各自的规则文件 | ⚠️ 未验证（见文档） |

## 验证状态一览

本项目刻意区分**已验证**与**未验证**：

- ✅ **已验证**：块字节一致性校验、四条回退链路（`revert` / 按编号反查 / 单文件恢复 /
  `reflog` 兜底）、Git 身份缺失导致无法提交、暂存区滞留、DrvFs `cp -p` 失败、
  技能热加载（无需重启）
- ⚠️ **未验证**：macOS 平台、`git worktree` 隔离、pre-commit 钩子强制、
  Claude Code / Cursor / Gemini CLI / Aider 的规则入口
- ❌ **已知未解决**：仅本地仓库无异地备份（见
  [docs/02-实践经验.md](docs/02-实践经验.md) 第五节）

## 持续集成

仓库自带 [`.github/workflows/ci.yml`](.github/workflows/ci.yml)，在每次推送与 PR 上运行三步：

| 步骤 | 脚本 | 拦什么 |
|---|---|---|
| 托管块一致性 | `scripts/verify_blocks.py` | 改了权威块却忘了同步 `templates/` 骨架 —— **本仓库的核心不变量** |
| 仓库一致性 | `scripts/check_repo.py` | 技能 frontmatter 缺失/非 kebab-case、文本文件混入 CRLF、脚本语法错误 |
| 安装脚本冒烟 | `scripts/install_skill.sh` | 在隔离 HOME 下验证 link 与 copy 两种模式，并确认 copy 不带入 `.git` |

本地预演（与 CI 等价）：

```bash
python3 scripts/verify_blocks.py \
  --block configs/block/GLOBAL-PROJECT-LOG-RULES.v2.md --targets targets.txt
python3 scripts/check_repo.py
```

**给自己的部署加同样的门禁**：把你自己的块文件与 `local/targets.txt` 放进一个私有仓库，
用同样的 workflow 校验。这样任何人在项目里手改了块，PR 阶段就会被拦下。

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

`configs/block/GLOBAL-PROJECT-LOG-RULES.v2.md` 是**带占位符的模板**。
替换占位符后，请把它（或你的副本）作为**权威块**，再用它校验部署：

```bash
# 正确：用你自己的块
python3 scripts/verify_blocks.py --block local/GLOBAL-PROJECT-LOG-RULES.v2.filled.md \
        --targets local/targets.txt

# 错误：用仓库里的公开模板去校验已填值的部署 —— 必然报"不一致"
```

这是**预期行为**：模板与填值后的实例本来就不同，校验比的正是"你的部署是否都等于你指定的那一份"。

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
