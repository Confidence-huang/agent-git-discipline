# 平台差异备忘

配套 `SKILL.md` 第 6 节。完整说明见仓库 `docs/04-环境支持.md`，本文只留执行时需要的要点。

## 1. 支持矩阵

| 平台 | 验证状态 |
|---|---|
| WSL2 (Ubuntu) | ✅ 实测验证 |
| Windows（原生） | ✅ 实测验证 |
| Linux（非 WSL） | 🟡 推断可行 |
| macOS | ⚠️ **未验证** |

## 2. 平台差异速查

> 下表的备份根用**示例盘符 `E`**。请按你机器上的实际备份盘替换
> （公开模板 `configs/block/` 里用的是 `<盘符>` 占位符）。

| 维度 | Windows | WSL / Linux |
|---|---|---|
| 备份根（Codex） | `<盘符>:\CodexBackups\<类别>\<时间戳>`（例：`E:\...`） | `/mnt/<小写盘符>/CodexBackups/<类别>-<时间戳>/`（例：`/mnt/e/...`） |
| 备份根（opencode） | `<盘符>:\OpenCodeBackups\<类别>\<时间戳>`（**与 Codex 备份不混放**） | 同左（经 `/mnt/<小写盘符>/` 访问） |
| Shell | `pwsh`（PowerShell 7） | bash / zsh |
| 复制 | `Copy-Item` | `cp` |
| 换行 | `*.ps1`/`*.cmd` 用 CRLF | 统一 LF |
| 技能根 | `%USERPROFILE%\.agents\skills` | `~/.agents/skills` |
| 规则入口 | `%USERPROFILE%\.codex\AGENTS.md` | `~/.codex/AGENTS.md` |

## 3. 三条平台陷阱

### 3.1 DrvFs 上 `cp -p` 会失败

```bash
cp -p src dst   # cp: preserving times for 'dst': Operation not permitted
```

`/mnt/c`、`/mnt/d`、`/mnt/e` 是 DrvFs（Windows 文件系统），不支持 `utimes`。

**做法**：用普通 `cp`，改用 **SHA256 校验**确认复制成功，不依赖时间戳。

### 3.2 备份盘不可用时必须停止

备份盘不可用或空间不足时**停止并报告**，
**不得**自动把备份写到系统盘（那违反"备份与源分离"的初衷）。
写入前核对可用空间，写入后逐文件校验。

### 3.3 PowerShell 结果变量别叫 `$matches`

`$Matches` 是 PowerShell 的自动变量（大小写不敏感）。
业务变量用它会被 `-match` 静默覆盖。

```powershell
$hits = Get-ChildItem | Select-String "foo"   # 正确
```

## 4. 换行策略

仓库用 `.gitattributes` 统一：

```gitattributes
* text=auto eol=lf
*.ps1 text eol=crlf
*.cmd text eol=crlf
*.bat text eol=crlf
*.png binary
```

- `eol=lf` 保证**工作区**也是 LF（只设 `text` 仅影响仓库存储）
- Windows 脚本必须 CRLF，否则部分工具报错
- 二进制显式标 `binary`，避免被误判为文本而损坏

**检查换行是否被污染**：

```bash
git ls-files --eol | grep -v "i/lf" | head
```

## 5. 跨平台双份配置的坑

同一 Agent 在 WSL 与 Windows 上**有两套独立配置目录**。
只配一边会导致另一边完全拿不到规则（真实踩过：WSL 侧连 git 身份都没设置）。

```bash
# WSL 侧
ls -la "$HOME/.codex/AGENTS.md" "$HOME/.config/opencode/AGENTS.md" "$HOME/.agents/skills"

# Windows 侧（从 WSL 访问）
ls -la /mnt/c/Users/*/.codex/AGENTS.md /mnt/c/Users/*/.config/opencode/AGENTS.md
```
