# Privacy / 隐私

## 中文

`skill-stocktake` 的报告可能包含本机绝对路径、目录名称、Skill 名称和描述、行数、内容哈希、重复副本、缺失链接以及静态风险信号。

这些信息默认只应保留在本地。分享报告前，应移除用户名、项目名、私有目录、内部 Skill 描述以及任何能推断账号或组织的信息。

`github-publisher` 在提交前应排除凭证、Cookie、`.env`、备份、缓存、工具状态、私有 Agent 配置和未审查报告。

## English

`skill-stocktake` reports may include absolute paths, directory names, Skill names and descriptions, line counts, content hashes, duplicate copies, missing links, and static risk signals.

Keep this information local by default. Before sharing a report, remove usernames, project names, private directories, internal Skill descriptions, and anything that can reveal an account or organization.

Before committing, `github-publisher` should exclude credentials, cookies, `.env` files, backups, caches, tool state, private agent configuration, and unreviewed reports.
