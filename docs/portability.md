# Portability / 可移植性

## 中文

- 使用 `<skill-dir>`、`<project>`、`$HOME` 和 `$CODEX_HOME` 等占位符，不依赖个人用户名。
- Skill 根由当前 Agent 运行时决定；不要假设所有工具共享同一目录。
- Windows junction、Unix symlink 和物理复制都可以使用，但应避免多个可漂移的物理副本。
- 运行 Python 脚本时使用 UTF-8。Windows PowerShell 5.1 读取中文文件时应显式指定 `-Encoding UTF8`。
- 官方 Skill 校验器的位置由运行时决定。先发现路径，再运行。

## English

- Use placeholders such as `<skill-dir>`, `<project>`, `$HOME`, and `$CODEX_HOME` instead of personal usernames.
- The active Skill root is defined by the current agent runtime; do not assume every tool shares one directory.
- Windows junctions, Unix symlinks, and physical copies can all work, but avoid multiple physical copies that can drift.
- Run Python scripts in UTF-8 mode. With Windows PowerShell 5.1, explicitly use `-Encoding UTF8` for non-ASCII files.
- The official Skill validator path is runtime-specific. Discover it before running it.
