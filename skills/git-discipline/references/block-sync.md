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
<!-- GLOBAL-PROJECT-LOG-RULES:START v3 -->
## GLOBAL-PROJECT-LOG-RULES 托管规则块（v3）

### 身份与范围
…（若干条款）

### 详细规则
- 完整规则与回退命令见 git 纪律技能 `git-discipline`。
<!-- GLOBAL-PROJECT-LOG-RULES:END -->
```

**三个设计要点**

| 要点 | 原因 |
|---|---|
| **配对标记**（START / END） | 旧版只有开头标记，实测漂移出 5 种格式，无法机械定位边界 |
| **版本号**（`v3`） | 使新旧块可区分；升版时可一次性筛选受影响文件 |
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
<!-- GLOBAL-PROJECT-LOG-RULES:END -->## 项目专属约束
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

当块内容有较大变更时，建议升版本号（`v2` → `v3`），使新旧可区分：

```markdown
<!-- GLOBAL-PROJECT-LOG-RULES:START v3 -->
```

**注意**：任何块内容变更都会改变哈希，因此**所有**目标都需要重新同步。
这正是要让同步可机械执行的原因。

## 9. 与技能的关系

| 载体 | 谁读 | 内容 |
|---|---|---|
| 托管块（写进 `AGENTS.md`） | Codex / opencode 等 | 精简投影，足以独立执行 |
| 技能 `git-discipline` | 支持技能的 Agent（含 DSH） | 完整规则 + 细节 references |

**DSH 不读 `AGENTS.md`**，只加载技能。因此两者必须同时提供，缺一会导致某类 Agent 完全失效。
