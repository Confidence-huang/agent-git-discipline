#!/usr/bin/env bash
# 把 git-discipline 技能装到各 Agent 的技能发现路径。
#
# 两种安装方式：
#   link（默认）—— 建符号链接。适合「单一实体 + 多处可见」的架构，
#                  改一处内容，所有 Agent 立即生效。
#   copy        —— 复制实体。适合目标路径不支持符号链接的场景
#                  （例如某些 Windows 目录或同步盘）。
#
# 用法
#   ./scripts/install_skill.sh --target agents-home
#   ./scripts/install_skill.sh --target project --project-root /path/to/project
#   ./scripts/install_skill.sh --target opencode --method copy
#   ./scripts/install_skill.sh --target codex-entities --entities-root /d/_skills/agents/skills
#
# 支持的目标
#   agents-home     ~/.agents/skills/<name>                 （DSH rank 500 / 跨 Agent 共用）
#   dsh-home        $DSH_HOME/skills/<name>                 （DSH rank 400，默认 ~/.dsh）
#   project         <project-root>/.agents/skills/<name>    （DSH rank 200，就近优先）
#   opencode        ~/.config/opencode/skills/<name>
#   codex-entities  <entities-root>/<name>                  （技能实体根；Codex 常有整目录 junction）
#   codex-home      $CODEX_HOME/skills/<name>               （仅在 Codex 用独立技能目录时需要）

set -euo pipefail

# ── 默认值 ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE="$REPO_ROOT/skills/git-discipline"
NAME="git-discipline"
METHOD="link"
TARGET=""
PROJECT_ROOT=""
ENTITIES_ROOT=""

usage() { sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

# ── 参数解析 ──────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
  case "$1" in
    --target)        TARGET="${2:?}"; shift 2 ;;
    --method)        METHOD="${2:?}"; shift 2 ;;
    --source)        SOURCE="${2:?}"; shift 2 ;;
    --name)          NAME="${2:?}"; shift 2 ;;
    --project-root)  PROJECT_ROOT="${2:?}"; shift 2 ;;
    --entities-root) ENTITIES_ROOT="${2:?}"; shift 2 ;;
    -h|--help)       usage 0 ;;
    *) echo "未知参数: $1" >&2; usage 1 ;;
  esac
done

[ -n "$TARGET" ] || { echo "❌ 必须指定 --target" >&2; usage 1; }

# ── 前置校验：技能本体必须存在且 frontmatter 合法 ──────────────────
if [ ! -f "$SOURCE/SKILL.md" ]; then
  echo "❌ 技能本体不存在: $SOURCE/SKILL.md" >&2
  exit 1
fi

# 检查必填 frontmatter（缺 name/description 的技能会被多数 Agent 静默跳过）
if ! head -20 "$SOURCE/SKILL.md" | grep -q '^name:'; then
  echo "⚠️  警告：SKILL.md 缺少 frontmatter 字段 name（可能被 Agent 忽略）" >&2
fi
if ! head -20 "$SOURCE/SKILL.md" | grep -q '^description:'; then
  echo "⚠️  警告：SKILL.md 缺少 frontmatter 字段 description（可能被 Agent 忽略）" >&2
fi

# ── 解析目标路径 ──────────────────────────────────────────────────
case "$TARGET" in
  agents-home)    DEST_DIR="$HOME/.agents/skills" ;;
  dsh-home)       DEST_DIR="${DSH_HOME:-$HOME/.dsh}/skills" ;;
  opencode)       DEST_DIR="$HOME/.config/opencode/skills" ;;
  codex-home)     DEST_DIR="${CODEX_HOME:-$HOME/.codex}/skills" ;;
  project)
    [ -n "$PROJECT_ROOT" ] || { echo "❌ --target project 需要 --project-root" >&2; exit 1; }
    DEST_DIR="$PROJECT_ROOT/.agents/skills"
    ;;
  codex-entities)
    [ -n "$ENTITIES_ROOT" ] || { echo "❌ --target codex-entities 需要 --entities-root" >&2; exit 1; }
    DEST_DIR="$ENTITIES_ROOT"
    ;;
  *) echo "❌ 未知目标: $TARGET" >&2; usage 1 ;;
esac

DEST="$DEST_DIR/$NAME"

echo "=============================================================="
echo "技能安装"
echo "=============================================================="
echo "  来源    : $SOURCE"
echo "  目标    : $DEST"
echo "  方式    : $METHOD"
echo

# ── 已存在时的处理：不擅自覆盖 ────────────────────────────────────
if [ -e "$DEST" ] || [ -L "$DEST" ]; then
  if [ -L "$DEST" ]; then
    current="$(readlink "$DEST")"
    if [ "$current" = "$SOURCE" ]; then
      echo "  ⏭️  已是指向同一来源的链接，无需操作"
      exit 0
    fi
    echo "  ℹ️  已有链接指向: $current"
  else
    echo "  ℹ️  目标已存在实体目录"
  fi
  echo "  ℹ️  先移除旧的（原内容请自行确认已备份）"
  rm -rf -- "$DEST"
fi

mkdir -p "$DEST_DIR"

# ── 建立链接或复制 ────────────────────────────────────────────────
if [ "$METHOD" = "link" ]; then
  ln -s "$SOURCE" "$DEST"
  echo "  ✅ 已建符号链接"
else
  # 刻意用 cp 而非 cp -a：DrvFs 等文件系统不支持保留时间戳，
  # cp -a/-p 会以 "Operation not permitted" 失败（见 docs/02-实践经验.md 坑 8）
  mkdir -p "$DEST"
  cp -r "$SOURCE/." "$DEST/"
  # 复制模式下不带走版本控制元数据
  rm -rf -- "$DEST/.git"
  echo "  ✅ 已复制实体"
fi

# ── 装后验证 ──────────────────────────────────────────────────────
echo
echo "  验证:"
if [ -f "$DEST/SKILL.md" ]; then
  echo "    ✅ SKILL.md 可读（$(wc -l < "$DEST/SKILL.md" | tr -d ' ') 行）"
else
  echo "    ❌ SKILL.md 不可读" >&2
  exit 1
fi
if [ -d "$DEST/references" ]; then
  echo "    ✅ references/ 存在（$(find "$DEST/references" -type f | wc -l | tr -d ' ') 个文件）"
fi
echo
echo "  注意：DSH 类 Agent 有热加载，新增技能通常无需重启；"
echo "        但 references/ 等子目录下的编辑不会触发热加载。"
