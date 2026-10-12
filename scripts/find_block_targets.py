#!/usr/bin/env python3
"""扫描本机，找出所有**带托管块**的项目文件，生成 / 比对部署清单。

为什么需要它
------------
`local/targets.txt` 是**手写**的本机清单（且被 `.gitignore` 排除，不入库），
换一台机器就只剩入库的示例 `targets.txt`；更糟的是**手写清单会漏**——
2026-10-12 实测：v4 → v5 全量升级时，按手写清单升了 20 个目标，
用本脚本一扫才发现另有 **10 个带块的文件从未被登记**（其中 9 个还停在 v3，
包含 8 个正在被投影成 DSH 技能的"项目规则"源）。手写清单漏一个，
那个文件就**静默**停在旧版本，没有任何报错——正是本项目要消灭的那类问题。

判定规则（有意收窄，避免把"引用块"误当"部署件"）
------------------------------------------------
1. **只看文件名**：`AGENTS.md` / `AGENTS.mdc` / `AGENTS*.md`
   （模板叫 `AGENTS_托管块模板.md`，也在内）。这样天然排掉
   `RULES.md` / `SKILL.md`（那是**投影产物**）、`README.md`、`docs/*`、
   `01_复盘踩坑精编版.md`（只是**引用**了块）、`GLOBAL-…deployed.md`（历史快照）。
2. **必须成对**：文件里同时有 `:START` 与 `:END` 标记；只引用半截的不算。
3. 目录跳过 `.git` / `node_modules` / `__pycache__` / 虚拟环境等噪声；
   其余用 `--exclude` 逐条排除（本机建议排掉工具仓副本与一次性测试目录）。

用法
----
    # 生成本机清单（覆盖写之前先看一眼输出）
    python3 scripts/find_block_targets.py \\
        --root ~/deepseek_project --root ~/workspace --root ~/CodexProjects \\
        --root /mnt/d/opencode_project \\
        --exclude '*/agent-git-discipline/*' --exclude '*/test_run_*/*' > local/targets.txt

    # 只查漂移：与已有清单比，退出码 1 = 有增删（可直接进 CI / 定时任务）
    python3 scripts/find_block_targets.py --root … --diff local/targets.txt

    # 顺带看每个文件的块版本（找出"静默停在旧版本"的部署件）
    python3 scripts/find_block_targets.py --root … --json

退出码：0 = 正常（`--diff` 时无差异）；1 = 参数/IO 错误，或 `--diff` 有差异。
"""

import argparse
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

# 目录级噪声（不参与扫描）
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "site-packages",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".idea", ".vscode-test",
}
# 文件名规则：AGENTS.md / AGENTS.mdc / AGENTS*.md（模板命名）
NAME_RE = re.compile(r"^AGENTS(\.md|\.mdc|.*\.md)$", re.IGNORECASE)
START_RE = re.compile(r"<!--\s*GLOBAL-PROJECT-LOG-RULES:START(?:\s+v([\d.]+))?\s*-->")
END_RE = re.compile(r"<!--\s*GLOBAL-PROJECT-LOG-RULES:END\s*-->")
MAX_SIZE = 1 << 20  # 1 MiB：块文件都是几 KB，超过这个尺寸不可能是部署件


def expand(path: str) -> str:
    return os.path.expanduser(os.path.expandvars(path))


def is_name_candidate(name: str) -> bool:
    return bool(NAME_RE.match(name))


def excluded(path: str, patterns) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def scan(roots, excludes):
    """返回 [(绝对路径, 版本字符串)]，按路径排序、去重。"""
    found = {}
    for root in roots:
        root = expand(root)
        if not os.path.isdir(root):
            print(f"⚠️  跳过不存在的根：{root}", file=sys.stderr)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if not is_name_candidate(name):
                    continue
                p = os.path.join(dirpath, name)
                if excluded(p, excludes):
                    continue
                try:
                    if os.path.getsize(p) > MAX_SIZE:
                        continue
                    text = Path(p).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                m = START_RE.search(text)
                if not m or not END_RE.search(text):
                    continue          # 只引用半截的、或压根没有块的，都不算部署件
                found[os.path.abspath(p)] = "v" + m.group(1) if m.group(1) else "(无版本号)"
    return sorted(found.items())


def read_list(path):
    """读取 targets.txt 形态的清单，返回生效行（绝对路径集合）。"""
    out = set()
    for line in Path(expand(path)).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.add(os.path.abspath(expand(s)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="扫描带托管块的项目文件，生成/比对部署清单")
    ap.add_argument("--root", action="append", default=[], required=False,
                    help="扫描根目录，可重复；支持 ~ 与 $HOME")
    ap.add_argument("--exclude", action="append", default=[],
                    help="排除 glob（对完整路径匹配），可重复")
    ap.add_argument("--diff", metavar="TARGETS_TXT",
                    help="与已有清单比对：有增删则退出码 1")
    ap.add_argument("--json", action="store_true", help="输出 JSON（含每个文件的块版本）")
    ap.add_argument("--quiet", action="store_true", help="只输出路径，不带表头注释")
    args = ap.parse_args()

    if not args.root:
        ap.error("至少给一个 --root")

    hits = scan(args.root, args.exclude)
    if not hits:
        print("⚠️  没有扫描到任何带托管块的文件（检查 --root 与 --exclude）", file=sys.stderr)

    if args.json:
        print(json.dumps([{"path": p, "block": v} for p, v in hits],
                         ensure_ascii=False, indent=2))
    else:
        if not args.quiet:
            print("# 由 scripts/find_block_targets.py 生成——不要手改，改 --root/--exclude 后重跑")
            print(f"# 扫描根：{' '.join(args.root)}")
            if args.exclude:
                print(f"# 排除：{' '.join(args.exclude)}")
            print(f"# 命中 {len(hits)} 个带托管块的部署件")
            print()
        for p, _v in hits:
            print(p)

    if args.diff:
        want = {p for p, _ in hits}
        have = read_list(args.diff)
        added, removed = sorted(want - have), sorted(have - want)
        if added or removed:
            print(f"\n❌ 与 {args.diff} 不一致：新增 {len(added)} / 消失 {len(removed)}", file=sys.stderr)
            for p in added:
                print(f"   + {p}", file=sys.stderr)
            for p in removed:
                print(f"   - {p}", file=sys.stderr)
            return 1
        print(f"\n✅ 与 {args.diff} 一致（{len(have)} 个目标）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
