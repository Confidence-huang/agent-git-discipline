#!/usr/bin/env python3
"""校验多个目标文件里的托管块是否与权威块**字节一致**。

设计要点
--------
1. 只比对**标记之间**的内容，不比对整个文件——否则文件其他部分的差异会污染结果。
2. 兼容两种块形态：
   - 配对标记 `<!-- ...:START v2 --> ... <!-- ...:END -->`（v2 推荐）
   - 标题形态  `## GLOBAL-PROJECT-LOG-RULES ...` 到下一个二级标题（旧版遗留）
3. 退出码：0 = 全部一致；1 = 有不一致或错误。便于在 CI 里直接使用。

用法
----
    python3 scripts/verify_blocks.py --block configs/block/GLOBAL-PROJECT-LOG-RULES.v2.md \\
            --targets targets.txt
    python3 scripts/verify_blocks.py --block <块文件> <文件1> <文件2> ...
    python3 scripts/verify_blocks.py --block <块文件> --targets targets.txt --json
"""

import argparse
import hashlib
import json
import os
import re
import sys

# ── 块边界的两类正则 ──────────────────────────────────────────────
# 配对标记：非贪婪匹配 START vN 到 END
PAT_PAIRED = re.compile(
    r"<!--\s*GLOBAL-PROJECT-LOG-RULES:START\s+v[\d.]+\s*-->(.*?)"
    r"<!--\s*GLOBAL-PROJECT-LOG-RULES:END\s*-->",
    re.S,
)
# 标题形态：从标题行起，到下一个二级标题（或文件尾）之前
PAT_HEADING = re.compile(
    r"##\s*GLOBAL-PROJECT-LOG-RULES[^\n]*\n(?:(?!##\s).)*",
    re.S,
)
# 仅用于「旧格式残留」告警：这些写法说明块没被 v2 统一
PAT_LEGACY = re.compile(
    r"GLOBAL-PROJECT-LOG-RULES:(START|BEGIN)\s*-->|"
    r"GLOBAL-PROJECT-LOG-RULES\s+START\s*-->|"
    r"<!--\s*/GLOBAL-PROJECT-LOG-RULES\s*-->|"
    r"GLOBAL-PROJECT-LOG-RULES:\s*[^-\n]+-->"
)


def extract_block(text):
    """从文件内容里取出托管块正文。

    返回 (正文, 形态标签)；取不到返回 (None, None)。
    先试配对标记，再退回标题形态。
    """
    m = PAT_PAIRED.search(text)
    if m:
        return m.group(1).strip(), "paired"
    m = PAT_HEADING.search(text)
    if m:
        return m.group(0).strip(), "heading"
    return None, None


def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def read_targets(targets_file):
    """读取目标清单：忽略空行与 # 注释，展开 $HOME。"""
    out = []
    with open(targets_file, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            out.append(os.path.expanduser(os.path.expandvars(line)))
    return out


def main():
    ap = argparse.ArgumentParser(
        description="校验托管块在各目标文件中是否字节一致",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--block", required=True, help="权威块文件（可含标记，脚本自动提取）")
    ap.add_argument("--targets", help="目标清单文件（每行一个路径）")
    ap.add_argument("paths", nargs="*", help="也可直接给出目标文件路径")
    ap.add_argument("--json", action="store_true", help="输出 JSON（便于 CI 消费）")
    ap.add_argument("--quiet", action="store_true", help="只输出结论行")
    args = ap.parse_args()

    # ── 1. 载入权威块 ──
    if not os.path.isfile(args.block):
        print(f"❌ 权威块文件不存在: {args.block}", file=sys.stderr)
        return 1
    ref_text, ref_kind = extract_block(open(args.block, encoding="utf-8").read())
    if ref_text is None:
        # 块文件本身就是裸块（没有标记），直接整体使用
        ref_text = open(args.block, encoding="utf-8").read().strip()
        ref_kind = "raw"
    ref_hash = digest(ref_text)

    # ── 2. 汇总目标列表 ──
    targets = list(args.paths)
    if args.targets:
        targets += read_targets(args.targets)
    # 去重且保持顺序
    seen, uniq = set(), []
    for t in targets:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    targets = uniq

    if not targets:
        print("⚠️  没有目标文件。用 --targets 或直接给出路径。", file=sys.stderr)
        return 1

    # ── 3. 逐个比对 ──
    rows, n_ok, n_bad = [], 0, 0
    for path in targets:
        if not os.path.isfile(path):
            rows.append({"path": path, "status": "missing", "hash": None, "kind": None})
            n_bad += 1
            continue
        text = open(path, encoding="utf-8").read()
        body, kind = extract_block(text)
        legacy = bool(PAT_LEGACY.search(text))

        if body is None:
            rows.append({"path": path, "status": "no-block", "hash": None, "kind": None,
                         "legacy": legacy})
            n_bad += 1
        elif digest(body) == ref_hash:
            rows.append({"path": path, "status": "ok", "hash": digest(body)[:12],
                         "kind": kind, "legacy": legacy})
            n_ok += 1
        else:
            rows.append({"path": path, "status": "differs", "hash": digest(body)[:12],
                         "kind": kind, "legacy": legacy})
            n_bad += 1

    # ── 4. 输出 ──
    if args.json:
        print(json.dumps({
            "reference": {"block": args.block, "kind": ref_kind, "hash": ref_hash},
            "summary": {"ok": n_ok, "bad": n_bad, "total": n_ok + n_bad},
            "results": rows,
        }, ensure_ascii=False, indent=2))
        return 0 if n_bad == 0 else 1

    ICON = {"ok": "✅", "differs": "⚠️ ", "no-block": "❓", "missing": "❌"}
    if not args.quiet:
        print("=" * 78)
        print(f"权威块: {args.block}")
        print(f"基准 SHA256(前12): {ref_hash[:12]}   形态: {ref_kind}")
        print("=" * 78)
    for r in rows:
        if not args.quiet:
            extra = "  [含旧格式标记]" if r.get("legacy") else ""
            print(f"  {ICON[r['status']]} {r['status']:<9} {r['hash'] or '-':<13} "
                  f"{r['path']}{extra}")
    print()
    print(f"  {'✅' if n_bad == 0 else '⚠️ '} 一致 {n_ok} / 不一致或异常 {n_bad} / 合计 {n_ok + n_bad}")
    if n_bad == 0:
        print(f"  基准 SHA256 = {ref_hash[:12]}  —— 全部一致")
    return 0 if n_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
