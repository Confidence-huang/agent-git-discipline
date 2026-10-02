#!/usr/bin/env python3
"""仓库级一致性检查：技能 frontmatter、换行、以及可执行脚本的语法。

与 verify_blocks.py 的分工
--------------------------
- verify_blocks.py  只管「托管块在各文件中是否字节一致」
- check_repo.py     管「仓库自身的其它约定是否被破坏」

检查项
------
1. 技能 frontmatter：每个 skills/*/SKILL.md 必须有 name（kebab-case）与 description
2. 换行：所有被跟踪的文本文件必须是 LF（由 .gitattributes 保证；
   本检查用于发现"绕过 .gitattributes 写进来"的 CRLF）
3. 脚本语法：.py 用 py_compile，.sh 用 bash -n

退出码：0 = 全部通过；1 = 有问题。可直接用于 CI。

用法
----
    python3 scripts/check_repo.py
    python3 scripts/check_repo.py --skip-syntax    # 跳过语法检查（快速模式）
"""

import argparse
import os
import re
import subprocess
import sys

# 需要按 LF 校验的文本扩展名
TEXT_EXT = {".md", ".py", ".sh", ".txt", ".yml", ".yaml", ".json", ".toml"}
# 允许 CRLF 的扩展名（Windows 专属脚本）
CRLF_OK_EXT = {".ps1", ".cmd", ".bat"}
# 不检查的路径前缀
SKIP_PREFIX = (".git/", "local/", "node_modules/")

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def tracked_files():
    """列出被 git 跟踪的文件；无 git 环境时退回遍历当前目录。

    ⚠️ 必须用 `-z`（NUL 分隔）而不是默认输出模式。
    默认模式下 `core.quotePath=true`（git 的默认值）会把含非 ASCII 字符的路径
    转义成**带双引号的 C 风格字符串**，例如：

        "docs/01-\\345\\217\\202\\350\\200\\203...md"

    这样的字符串拿去做 `os.path.isfile()` 恒为假，于是所有中文名文件
    会被下游检查**静默跳过**（曾导致 docs/01–05 从未被换行检查覆盖）。
    `-z` 输出原始字节、不做任何转义，从根本上消除这一类误判。

    显式指定 `encoding="utf-8"` + `surrogateescape`：前者让解码不随 locale 漂移
    （CI 里 `LANG` 可能未设置），后者保证即使遇到非 UTF-8 字节名也不会抛异常。
    """
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="surrogateescape",
            check=True,
        ).stdout
        return [p for p in out.split("\0") if p.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        found = []
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d != ".git"]
            for f in files:
                found.append(os.path.relpath(os.path.join(root, f)))
        return found


def parse_frontmatter(text):
    """极简 YAML frontmatter 解析：只取顶层标量键值，够用且无依赖。"""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data = {}
    for line in text[3:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" in line and not line.startswith((" ", "\t")):
            k, _, v = line.partition(":")
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def check_frontmatter():
    problems = []
    skills = [p for p in tracked_files()
              if p.startswith("skills/") and p.endswith("SKILL.md")]
    if not skills:
        return ["no SKILL.md found under skills/"], 0
    for p in skills:
        text = open(p, encoding="utf-8").read()
        fm = parse_frontmatter(text)
        if not fm:
            problems.append(f"{p}: 缺少 YAML frontmatter")
            continue
        name = fm.get("name", "")
        desc = fm.get("description", "")
        if not name:
            problems.append(f"{p}: 缺少必填字段 name")
        elif not NAME_RE.match(name):
            problems.append(f"{p}: name 不是 kebab-case: {name!r}")
        if not desc:
            problems.append(f"{p}: 缺少必填字段 description")
        elif len(desc) < 20:
            problems.append(f"{p}: description 过短（多数 Agent 用它做触发匹配）")
    return problems, len(skills)


def check_eol():
    problems, n = [], 0
    for p in tracked_files():
        if p.startswith(SKIP_PREFIX):
            continue
        ext = os.path.splitext(p)[1].lower()
        if ext in CRLF_OK_EXT or ext not in TEXT_EXT:
            continue
        if not os.path.isfile(p):
            continue
        n += 1
        with open(p, "rb") as fh:
            raw = fh.read()
        if b"\r\n" in raw:
            problems.append(f"{p}: 含 CRLF（应为 LF）")
    return problems, n


def check_syntax():
    problems, n = [], 0
    for p in tracked_files():
        if p.startswith(SKIP_PREFIX) or not os.path.isfile(p):
            continue
        if p.endswith(".py"):
            n += 1
            r = subprocess.run([sys.executable, "-m", "py_compile", p],
                               capture_output=True, text=True)
            if r.returncode != 0:
                problems.append(f"{p}: Python 语法错误\n{r.stderr.strip()}")
        elif p.endswith(".sh"):
            n += 1
            r = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
            if r.returncode != 0:
                problems.append(f"{p}: Bash 语法错误\n{r.stderr.strip()}")
    return problems, n


def main():
    ap = argparse.ArgumentParser(description="仓库级一致性检查")
    ap.add_argument("--skip-syntax", action="store_true", help="跳过语法检查")
    args = ap.parse_args()

    print("=" * 74)
    print("仓库一致性检查")
    print("=" * 74)

    all_problems = []
    total = 0

    p, n = check_frontmatter()
    total += n
    print(f"\n[1] 技能 frontmatter     检查 {n} 个")
    all_problems += p

    p, n = check_eol()
    total += n
    print(f"[2] 换行（LF）           检查 {n} 个文本文件")
    all_problems += p

    if not args.skip_syntax:
        p, n = check_syntax()
        total += n
        print(f"[3] 脚本语法             检查 {n} 个脚本")
        all_problems += p

    print()
    if all_problems:
        print(f"❌ 发现 {len(all_problems)} 个问题：")
        for x in all_problems:
            print(f"   · {x}")
        return 1
    print(f"✅ 全部通过（检查 {total} 项）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
