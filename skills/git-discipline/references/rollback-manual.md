# 回退手册

配套 `SKILL.md` 第 5 节。目标：任何时候都能把项目退回到之前某个正确状态。

## 1. 核心公式

```
能回退  =  干净起点  +  每步提交
```

- **干净起点**：动手前工作区没有未提交改动。否则回退时分不清"哪些原来就有、哪些是新改坏的"。
- **每步提交**：git 只能回退**已提交**的内容。提交粒度 = 你能回退的精度。

⚠️ git **撤不掉未跟踪的新文件**。这正是"改完就提交"必须成为硬规则的原因。

## 2. 最常用（安全，保留历史）

| 场景 | 命令 |
|---|---|
| 看时间线 | `git log --oneline --graph --decorate -25` |
| 撤销最近一次提交，改动留下 | `git reset --soft HEAD~1` |
| **撤销某次提交的内容（首选）** | `git revert <hash>` |
| 看某次提交改了什么 | `git show <hash>` |
| 看当前未暂存改动 | `git diff` |
| 看已暂存改动 | `git diff --staged` |

`git revert` 是**首选回退方式**：生成一个"反向提交"，历史完整保留，可以安全推送。

**revert 的 message 约定**（借自 [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 的建议写法）：

```
revert: <原提交描述>

Refs: <被回退的 commit SHA>, <另一个 SHA>
```

好处：回退动作本身也进入可检索的历史，日后能查出"哪次回退、退掉了什么"。
git 默认生成的 `Revert "xxx"` 也合格，补上 `Refs:` 更利于追溯。

## 3. 回到过去某个状态

| 场景 | 命令 |
|---|---|
| 恢复某文件到上次提交 | `git restore <文件>` |
| 恢复整个项目内容到某次提交 | `git checkout <hash> -- .` |
| 只看不回退（安全探查） | `git switch --detach <hash>`，之后 `git switch -` 返回 |
| 某文件回退到任意历史版本 | `git restore --source=<hash> <文件>` |

## 4. 危险操作（会丢东西，必须单独授权）

| 场景 | 命令 | 后果 |
|---|---|---|
| 彻底丢弃某次之后的提交 | `git reset --hard <hash>` | **未提交改动全部消失** |
| 删除未跟踪的新文件 | `git clean -fd` | **新文件永久删除** |
| 丢弃工作区改动 | `git restore .` | 未提交改动消失 |

用之前必须先预览或存档：

```bash
git clean -nd          # 预览会删什么（不实际删）
git stash -u           # 把改动（含未跟踪文件）存档
git stash list         # 查看存档
git stash pop          # 恢复
```

## 5. 应急：改坏了而且没提交过

```bash
git diff                      # 先看清改了什么
git restore <文件>             # 恢复已跟踪文件到上次提交
git clean -nd                 # 预览未跟踪文件（不删）
git clean -fd                 # 确认后再删
```

若连"上次提交"都是坏的：`git reflog` 列出所有历史位置，找到好的那个再 `git reset --hard <hash>`。

**`git reflog` 是最后一道保险，几乎什么都能救回来。**
即使误操作 `reset --hard`，只要没执行过 `git gc`，通常仍可恢复。

## 6. 按「第 N 次 git」编号回退

编号来自 `git rev-list --first-parent --count HEAD`，是本仓库连续提交序号。

```bash
# 当前是第几次
git rev-list --first-parent --count HEAD

# 反查第 N 次 git 对应的完整 SHA
git rev-list --first-parent --reverse HEAD | sed -n '20p'

# 列出带编号的时间线
git log --first-parent --oneline --reverse | nl -ba | tail -20
```

编号是**给人用的别名**，精确回退仍以完整 SHA 为准。两者都要记录。

## 7. 分支与隔离（需授权）

| 场景 | 命令 |
|---|---|
| 建实验分支 | `git switch -c <name>` |
| 并行工作隔离 | `git worktree add ../<dir> <branch>` |
| 回到原分支 | `git switch -` |
| 删除已合并分支 | `git branch -d <name>` |

大重构、批量替换前，先打标记或建分支，形成可回退的边界。

> ⚠️ `git worktree` 在本项目中**尚未验证**（见 `docs/02-实践经验.md` 第五节）。
> 作为需授权的手动手段保留，未升级为默认流程。

## 8. 实测验证记录

以下四条链路已实测通过（复现脚本见 `docs/02-实践经验.md` 第四节 B）：

| 链路 | 结果 |
|---|---|
| `git revert --no-edit HEAD` | ✅ 提交数 +1，历史未改写 |
| 按编号反查 SHA | ✅ 多次均正确定位 |
| `git restore --source=<sha> <file>` | ✅ 不影响 HEAD |
| `reset --hard` 后 `reflog` 找回 | ✅ 成功恢复 |
