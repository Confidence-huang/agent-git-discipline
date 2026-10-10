#!/usr/bin/env python3
"""把权威托管块同步进多个目标文件，替换掉其中已有的块。

设计要点
--------
1. **默认 dry-run**：不加 --apply 只打印将要做的变更，不动文件。
2. **整段替换**：定位到块的起止边界后整体替换，不逐行改——避免局部修改造成的格式漂移。
3. **保留块外内容**：块之前/之后的项目专属段落原样保留。
4. **换行收尾修正**：替换后确保 `:END` 之后有换行，否则会与后续标题粘连
   （这是实际踩过的坑，见 docs/02-实践经验.md 坑 3）。
5. **幂等**：已是目标块的文件会被跳过。

用法
----
    # 预览
    python3 scripts/sync_block.py --block configs/block/GLOBAL-PROJECT-LOG-RULES.v4.md \\
            --targets targets.txt

    # 实际写入（可选先备份）
    python3 scripts/sync_block.py --block <块文件> --targets targets.txt \\
            --apply --backup-dir /mnt/e/CodexBackups/block-sync-$(date +%Y%m%d-%H%M%S)
"""

import argparse
import hashlib
import os
import re
import shutil
import sys

# 配对标记（v4 推荐形态）。**版本号可缺省**：历史上有 13 个文件的 START 标记没有版本后缀
# （见 docs/02-实践经验.md 坑 3），旧正则要求 v[\d.]+，于是这些文件一个都定位不到，
# 只会打印「未找到托管块，跳过（需手工插入）」——它们因此长期无法被同步回来。
PAT_PAIRED = re.compile(
    r"<!--\s*GLOBAL-PROJECT-LOG-RULES:START(?:\s+v[\d.]+)?\s*-->.*?"
    r"<!--\s*GLOBAL-PROJECT-LOG-RULES:END\s*-->",
    re.S,
)
# 标题形态（旧版遗留，用于兼容替换）
PAT_HEADING = re.compile(
    r"##\s*GLOBAL-PROJECT-LOG-RULES[^\n]*\n(?:(?!##\s).)*",
    re.S,
)
# 块尾标记，用于修正换行粘连
END_MARK = "<!-- GLOBAL-PROJECT-LOG-RULES:END -->"


def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_block(path):
    """载入权威块。若文件含标记则提取正文整段（含标记），否则视为裸块。"""
    text = open(path, encoding="utf-8").read()
    m = PAT_PAIRED.search(text)
    if m:
        return m.group(0).strip()
    # 裸块文件（无标记）——直接整体使用
    return text.strip()


def find_existing(text):
    """返回 (起点, 终点) 或 None。优先配对标记，退回标题形态。"""
    m = PAT_PAIRED.search(text)
    if m:
        return m.start(), m.end()
    m = PAT_HEADING.search(text)
    if m:
        return m.start(), m.end()
    return None


def read_targets(targets_file):
    out = []
    with open(targets_file, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            out.append(os.path.expanduser(os.path.expandvars(line)))
    return out


def fix_trailing_newline(text):
    """确保块尾标记后跟换行。

    实际踩坑：替换块时若新块末尾无换行，会把紧随其后的 `## 项目专属约束`
    标题粘到同一行上（`...:END -->## 项目专属约束`），破坏 Markdown 结构。
    """
    return re.sub(re.escape(END_MARK) + r"[ \t]*(?=\S)", END_MARK + "\n\n", text)


def main():
    ap = argparse.ArgumentParser(
        description="把权威托管块同步进目标文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--block", required=True, help="权威块文件")
    ap.add_argument("--targets", help="目标清单文件（每行一个路径）")
    ap.add_argument("paths", nargs="*", help="也可直接给出目标文件路径")
    ap.add_argument("--apply", action="store_true", help="实际写入（默认仅预览）")
    ap.add_argument("--backup-dir", help="写入前把原文件备份到此目录")
    args = ap.parse_args()

    block = load_block(args.block)
    block_hash = digest(block)

    targets = list(args.paths)
    if args.targets:
        targets += read_targets(args.targets)
    seen, uniq = set(), []
    for t in targets:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    targets = uniq

    if not targets:
        print("⚠️  没有目标文件。用 --targets 或直接给出路径。", file=sys.stderr)
        return 1

    if args.backup_dir:
        os.makedirs(args.backup_dir, exist_ok=True)

    mode = "实际写入" if args.apply else "预览（dry-run）"
    print("=" * 78)
    print(f"同步模式: {mode}")
    print(f"权威块: {args.block}    SHA256(前12): {block_hash[:12]}")
    print("=" * 78)

    n_changed = n_same = n_missing = n_noblock = n_failed = 0

    for path in targets:
        if not os.path.isfile(path):
            print(f"  ❌ 文件不存在: {path}")
            n_missing += 1
            continue

        text = open(path, encoding="utf-8").read()
        span = find_existing(text)

        if span is None:
            # 没有块——不擅自追加，交由使用者决定插入位置
            print(f"  ❓ 未找到托管块，跳过（需手工插入）: {path}")
            n_noblock += 1
            continue

        old = text[span[0]:span[1]]
        if old.strip() == block:
            print(f"  ⏭️  已是目标块: {path}")
            n_same += 1
            continue

        new_text = fix_trailing_newline(text[:span[0]] + block + text[span[1]:])

        if not args.apply:
            print(f"  · 将替换 {path}")
            print(f"      旧块 {digest(old)[:8]} → 新块 {block_hash[:8]}")
            n_changed += 1
            continue

        try:
            if args.backup_dir:
                # 用「路径打平」的方式命名备份，避免不同目录同名文件互相覆盖。
                # 刻意用 shutil.copy 而非 copy2：DrvFs（/mnt/c、/mnt/d）不支持
                # utimes，copy2 会抛 "Operation not permitted"。
                # 见 docs/02-实践经验.md 坑 8。
                flat = path.strip("/").replace("/", "__").replace("\\", "__")
                shutil.copy(path, os.path.join(args.backup_dir, flat))
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(new_text)
            print(f"  ✅ 已替换 {path}  [{digest(old)[:8]} → {block_hash[:8]}]")
            n_changed += 1
        except OSError as exc:
            print(f"  ❌ 写入失败 {path}: {exc}")
            n_failed += 1

    print()
    print(f"  替换 {n_changed} / 已一致 {n_same} / 无块 {n_noblock} / "
          f"缺失 {n_missing} / 失败 {n_failed}")
    if not args.apply and n_changed:
        print("  ℹ️  这是预览。加 --apply 才会真正写入。")
    return 0 if (n_failed == 0 and n_missing == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
