# Agent Skill Maintenance Kit

[中文](#中文) | [English](#english)

## 中文

一个面向现代工具型 Agent 的小型 Skill 维护与安全发布工具包。首批包含两个可复用 Skill：

| Skill | 用途 | 默认边界 |
| --- | --- | --- |
| `skill-stocktake` | 清点、审计和改进本地 Skill 库 | 只读扫描；不会自动修改、安装、删除或联网 |
| `github-publisher` | 安全地创建、提交和推送 GitHub 仓库 | 推送前检查认证、远端、默认分支和隐私文件；公开仓库必须明确确认 |

这些 Skill 以 `SKILL.md` 为核心，适用于 Codex 以及其他能读取 Agent Skill 指令的工具。设计重点是触发边界、授权、上下文成本、可移植性和可验证性，而不是绑定某个单一模型版本。`skill-stocktake` 需要 Python 3.9+ 和 PyYAML 6.x；`github-publisher` 还需要 Git 与 GitHub CLI (`gh`)。

### 快速开始

1. 安装 Python 依赖：

   ```bash
   python -m pip install -r requirements.txt
   ```

2. 审计仓库内的 Skill：

   ```bash
   python skills/skill-stocktake/scripts/audit_skills.py --root repo=skills --strict
   ```

3. 将需要的 Skill 目录复制或链接到你的 Agent Skill 根，例如：

   - 通用共享根：`~/.agents/skills`
   - Codex：`$CODEX_HOME/skills` 或你的实际 Codex Skill 根
   - 项目本地：`<project>/.agents/skills`

安装后重新读取对应 `SKILL.md`，并用当前运行时提供的官方 Skill 校验器检查。

### 安全与隐私

- `audit_skills.py` 只读取文件并把报告写到标准输出。
- 审计结果可能包含绝对路径、Skill 描述和内容哈希。不要未经审查就上传原始报告。
- 本仓库不会自动安装依赖、授予权限、删除文件、推送代码或创建公开仓库。
- `github-publisher` 对公开可见性、强推、删远端分支、改仓库设置和敏感文件保持显式确认。
- 不要把 `.env`、令牌、Cookie、恢复码、私有 Agent 配置、备份、缓存或原始审计报告提交到仓库。

更多信息见 [隐私说明](docs/privacy.md)、[可移植性说明](docs/portability.md) 和 [安全策略](SECURITY.md)。

### 仓库结构

```text
agent-skill-maintenance-kit/
├─ skills/
│  ├─ skill-stocktake/
│  └─ github-publisher/
├─ docs/
├─ .github/workflows/validate.yml
├─ README.md
├─ SECURITY.md
└─ requirements.txt
```

### 本地验证

```bash
python skills/skill-stocktake/scripts/audit_skills.py --root repo=skills --strict
python -m py_compile skills/skill-stocktake/scripts/audit_skills.py
```

GitHub Actions 会在 Windows 和 Linux 上运行相同的审计与语法检查。

### 许可证

首次公开发布前需要确认内容权属并选择许可证。在仓库加入 `LICENSE` 之前，不授予超出适用版权法默认范围的再利用权。

### 声明

本项目与 OpenAI、GitHub、Anthropic 或其他产品厂商没有隶属或背书关系。产品名仅用于说明兼容性和工作流。

## English

A compact toolkit for maintaining and safely publishing Agent Skills for modern tool-using agents. The initial release contains two reusable skills:

| Skill | Purpose | Default boundary |
| --- | --- | --- |
| `skill-stocktake` | Inventory, audit, and improve a local Skill library | Read-only scanning; no automatic edits, installs, deletion, or network access |
| `github-publisher` | Create, commit, and push GitHub repositories safely | Checks auth, remotes, default branches, and private files; public visibility requires explicit confirmation |

The repository uses `SKILL.md` as its portable core. It is intended for Codex and other agents that can consume Agent Skill instructions. The design focuses on trigger fit, authorization, context cost, portability, and verification rather than claiming compatibility with only one model version. `skill-stocktake` requires Python 3.9+ and PyYAML 6.x; `github-publisher` also requires Git and the GitHub CLI (`gh`).

### Quick Start

1. Install the Python dependency:

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Audit the Skills in this repository:

   ```bash
   python skills/skill-stocktake/scripts/audit_skills.py --root repo=skills --strict
   ```

3. Copy or link the desired Skill directory into your agent's Skill root, for example:

   - Shared root: `~/.agents/skills`
   - Codex: `$CODEX_HOME/skills` or your actual Codex Skill root
   - Project-local: `<project>/.agents/skills`

After installation, re-read the relevant `SKILL.md` and run the official Skill validator provided by your current runtime.

### Safety and Privacy

- `audit_skills.py` reads files and writes its report only to stdout.
- Reports may contain absolute paths, Skill descriptions, and content hashes. Do not upload raw reports without review.
- This repository does not automatically install dependencies, grant permissions, delete files, push code, or create public repositories.
- `github-publisher` keeps public visibility, force pushes, remote branch deletion, repository settings, and sensitive files behind explicit confirmation.
- Never commit `.env` files, tokens, cookies, recovery codes, private agent configuration, backups, caches, or raw audit reports.

See [Privacy](docs/privacy.md), [Portability](docs/portability.md), and [Security](SECURITY.md).

### Repository Layout

```text
agent-skill-maintenance-kit/
├─ skills/
│  ├─ skill-stocktake/
│  └─ github-publisher/
├─ docs/
├─ .github/workflows/validate.yml
├─ README.md
├─ SECURITY.md
└─ requirements.txt
```

### Local Validation

```bash
python skills/skill-stocktake/scripts/audit_skills.py --root repo=skills --strict
python -m py_compile skills/skill-stocktake/scripts/audit_skills.py
```

GitHub Actions runs the same audit and syntax checks on Windows and Linux.

### License

Content ownership and a license must be confirmed before the first public release. Until a `LICENSE` file is added, no reuse rights are granted beyond the defaults of applicable copyright law.

### Disclaimer

This project is not affiliated with or endorsed by OpenAI, GitHub, Anthropic, or other product vendors. Product names are used only to describe compatibility and workflows.
