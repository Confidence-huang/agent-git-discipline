# 贡献与提交约定

本仓库是**公开**仓库，`main` 有分支保护（直推会被 `GH006` 拒绝），所有改动走 PR。

## 提交信息

采用 [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)，
类型限：`feat` / `fix` / `docs` / `chore` / `refactor` / `test` / `ci` / `build` / `perf` / `backup`。

- 标题里**不要出现「和」/「and」**——出现了就说明它该拆成两个提交（见 `skills/git-discipline/SKILL.md` §3）。
  ⚠️ 这条**只有人能判**：实测 `commitlint` 会放行「feat: 加登录 和 顺手修了日志格式」，
  它只管类型与格式。别把它当成"有 CI 兜着"。
- CI 的 `提交信息规范` 作业用官方 `commitlint` 校验 PR 范围内的**类型与格式**
  （`type-enum` / `type-empty` / `subject-empty` / `header-max-length`，配置见 `commitlint.config.mjs`）。
  实测：`update: 随便改改` 被拒、`feat: 正常的一条` 通过。
- 依据与背景：`docs/05-提交与PR流程.md`。**为什么用 CI 而不是 rulesets**：
  提交元数据规则在 GitHub 是 Enterprise 专属，免费 public 仓库只能用 CI 补，见 `docs/06` §五。

## 外部贡献

- 请使用 DCO：`git commit -s`（每个提交带 `Signed-off-by`）。
- 目前不要求 CLA（个人项目无法律实体流程）。

## 本地门禁（与 CI 同一套命令）

```bash
python3 scripts/verify_blocks.py \
  --block configs/block/GLOBAL-PROJECT-LOG-RULES.v4.md --targets targets.txt
python3 scripts/check_repo.py
```

客户端 `pre-push` 钩子（可选，克隆后手动启用一次——**钩子不是自动生效的**）：

```bash
git config core.hooksPath .githooks
# ⚠️ 钩子文件必须有执行位，否则会被 Git 静默忽略
ls -l .githooks/pre-push
```

## 绕过留痕

凡自己绕过 required approval 的合并，请在 PR 里补一条评论：`BYPASS: <理由> + <验证证据>`。
（单人仓库拿不到真评审，这条是**形式门禁**的替代品；见 `docs/06` §五。）
