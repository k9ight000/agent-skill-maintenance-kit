#!/usr/bin/env python3
"""Read-only inventory and static evidence collection for local Agent Skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "PyYAML is required because the official skill validator also uses it. "
        "Install nothing automatically; use the configured Codex Python runtime."
    ) from exc


MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_BODY_LINES = 500
ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
}
SKIP_PARTS = {
    ".git",
    ".system",
    "__pycache__",
    "node_modules",
}
RISK_PATTERNS = (
    ("legacy-task-tool", re.compile(r"\bTask\s*\(")),
    ("legacy-todo-tool", re.compile(r"\bTodoWrite\b")),
    ("legacy-web-tool", re.compile(r"\b(?:WebSearch|WebFetch)\b")),
    ("legacy-file-tool", re.compile(r"\b(?:write_to_file|view_file)\b")),
    (
        "permission-bypass",
        re.compile(
            r"(?:--dangerously-skip-permissions|\byolo\b|sandbox_permissions\s*[:=]\s*[\"']?danger)",
            re.IGNORECASE,
        ),
    ),
    (
        "destructive-git",
        re.compile(
            r"(?:git\s+reset\s+--hard|git\s+clean\s+-[a-z]*f|git\s+worktree\s+remove\s+--force)",
            re.IGNORECASE,
        ),
    ),
    (
        "permanent-delete",
        re.compile(
            r"(?:Remove-Item\b[^\n]*(?:-Recurse[^\n]*-Force|-Force[^\n]*-Recurse)|\brm\s+-rf\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "background-process",
        re.compile(
            r"(?:Start-Process\b|detached\s*[:=]\s*true|nohup\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "automatic-install",
        re.compile(
            r"(?:\bnpx\s+--yes\b|\bpip\s+install\b|\bnpm\s+install\b|\bwinget\s+install\b)",
            re.IGNORECASE,
        ),
    ),
)
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FENCED_CODE_RE = re.compile(
    r"(?ms)^(?:\x60{3}|~{3}).*?^(?:\x60{3}|~{3})[^\n]*$"
)
NAME_RE = re.compile(r"^[a-z0-9-]+$")
PROHIBITION_RE = re.compile(
    r"\b(?:do not|don't|never|must not|should not|cannot|can't|forbidden)\b|(?:禁止|不得|不要)",
    re.IGNORECASE,
)
INSTALL_GUARD_RE = re.compile(
    r"(?:ask|obtain|require|explicit|approval|authorization|confirmation)"
    r".{0,180}(?:install|download|dependency)|"
    r"(?:install|download|dependency).{0,180}"
    r"(?:ask|approval|authorization|confirmation)",
    re.IGNORECASE | re.DOTALL,
)
FENCE_WITH_INFO_RE = re.compile(
    r"(?ms)^(?P<fence>\x60{3}|~{3})(?P<info>[^\n]*)\n.*?^(?P=fence)[^\n]*$"
)
CONTAINER_FENCE_LANGS = {"dockerfile", "containerfile"}


@dataclass
class SkillRecord:
    root: str
    path: str
    real_path: str
    aliases: list[str] = field(default_factory=list)
    name: str | None = None
    description: str | None = None
    line_count: int = 0
    sha256: str = ""
    content_sha256: str = ""
    reparse_entry: bool = False
    frontmatter_keys: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    risk_signals: list[str] = field(default_factory=list)
    guarded_signals: list[str] = field(default_factory=list)
    contextual_signals: list[str] = field(default_factory=list)
    missing_links: list[str] = field(default_factory=list)


def default_roots() -> list[tuple[str, Path]]:
    home = Path.home()
    return [
        ("shared", home / ".agents" / "skills"),
        ("codex", home / ".codex" / "skills"),
        ("claude", home / ".claude" / "skills"),
        ("superpowers", home / ".agents" / "superpowers" / "skills"),
    ]


def parse_root(value: str) -> tuple[str, Path]:
    if "=" in value:
        label, raw_path = value.split("=", 1)
        label = label.strip()
        if not label:
            raise argparse.ArgumentTypeError("Root label cannot be empty.")
    else:
        raw_path = value
        label = Path(value).name or "custom"
    return label, Path(raw_path).expanduser()


def normalized_path(path: Path) -> str:
    try:
        resolved = path.resolve(strict=False)
    except OSError:
        resolved = path.absolute()
    return os.path.normcase(str(resolved))


def is_reparse_point(path: Path) -> bool:
    try:
        stat_result = os.lstat(path)
    except OSError:
        return False
    attributes = getattr(stat_result, "st_file_attributes", 0)
    return bool(attributes & 0x400)


def normalized_content_sha256(text: str) -> str:
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def iter_skill_files(root: Path, include_system: bool) -> Iterable[Path]:
    if not root.is_dir():
        return
    for path in root.rglob("SKILL.md"):
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            relative_parts = path.parts
        if any(part in SKIP_PARTS for part in relative_parts):
            if not include_system or ".system" not in relative_parts:
                continue
        yield path


def read_text(path: Path, record: SkillRecord) -> str:
    raw = path.read_bytes()
    record.sha256 = hashlib.sha256(raw).hexdigest()
    if raw.startswith(b"\xef\xbb\xbf"):
        record.warnings.append("utf8-bom")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        record.errors.append(f"not-utf8:{exc.start}")
        text = raw.decode("utf-8", errors="replace")
    record.content_sha256 = normalized_content_sha256(text)
    return text


def validate_frontmatter(text: str, record: SkillRecord) -> None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        record.errors.append("invalid-or-missing-frontmatter")
        return

    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        record.errors.append(f"invalid-yaml:{exc.__class__.__name__}")
        return

    if not isinstance(data, dict):
        record.errors.append("frontmatter-not-mapping")
        return

    record.frontmatter_keys = sorted(str(key) for key in data)
    unexpected = sorted(set(data) - ALLOWED_FRONTMATTER_KEYS)
    if unexpected:
        record.errors.append("unexpected-frontmatter:" + ",".join(unexpected))

    name = data.get("name")
    description = data.get("description")
    if not isinstance(name, str):
        record.errors.append(f"name-not-string:{type(name).__name__}")
    else:
        record.name = name.strip()
        if not record.name:
            record.errors.append("name-empty")
        elif (
            not NAME_RE.fullmatch(record.name)
            or record.name.startswith("-")
            or record.name.endswith("-")
            or "--" in record.name
        ):
            record.errors.append("name-not-hyphen-case")
        if len(record.name) > MAX_NAME_LENGTH:
            record.errors.append(f"name-too-long:{len(record.name)}")
        if record.name != Path(record.path).parent.name:
            record.warnings.append(
                f"folder-name-mismatch:{Path(record.path).parent.name}"
            )

    if not isinstance(description, str):
        record.errors.append(
            f"description-not-string:{type(description).__name__}"
        )
    else:
        record.description = description.strip()
        if not record.description:
            record.errors.append("description-empty")
        if len(record.description) > MAX_DESCRIPTION_LENGTH:
            record.errors.append(
                f"description-too-long:{len(record.description)}"
            )
        if "<" in record.description or ">" in record.description:
            record.errors.append("description-angle-brackets")


def check_links(text: str, skill_file: Path) -> list[str]:
    missing: set[str] = set()
    scan_text = FENCED_CODE_RE.sub("", text)
    for raw_target in MARKDOWN_LINK_RE.findall(scan_text):
        target = raw_target.strip().strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        if any(marker in target for marker in ("[", "]", "{", "}")):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        candidate = (skill_file.parent / target).resolve(strict=False)
        if not candidate.exists():
            missing.add(target)
    return sorted(missing)


def line_at(text: str, offset: int) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return text[start:end]


def fenced_contexts(text: str) -> list[tuple[int, int, str]]:
    contexts: list[tuple[int, int, str]] = []
    for match in FENCE_WITH_INFO_RE.finditer(text):
        info = match.group("info").strip().split(maxsplit=1)
        language = info[0].lower() if info else ""
        contexts.append((match.start(), match.end(), language))
    return contexts


def is_container_context(
    label: str,
    text: str,
    offset: int,
    contexts: list[tuple[int, int, str]],
) -> bool:
    if label not in {"automatic-install", "permanent-delete", "background-process"}:
        return False
    for start, end, language in contexts:
        if start <= offset < end and language in CONTAINER_FENCE_LANGS:
            return True
    line = line_at(text, offset).lower()
    return "same run" in line or "dockerfile layer" in line or "container image" in line


def classify_risk_signals(
    text: str,
) -> tuple[list[str], list[str], list[str]]:
    risk: set[str] = set()
    guarded: set[str] = set()
    contextual: set[str] = set()
    contexts = fenced_contexts(text)

    for label, pattern in RISK_PATTERNS:
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        install_guarded = label == "automatic-install" and INSTALL_GUARD_RE.search(text)
        for match in matches:
            line = line_at(text, match.start())
            if PROHIBITION_RE.search(line) or install_guarded:
                guarded.add(label)
            elif is_container_context(label, text, match.start(), contexts):
                contextual.add(label)
            else:
                risk.add(label)

    return sorted(risk), sorted(guarded), sorted(contextual)


def build_record(label: str, skill_file: Path) -> SkillRecord:
    record = SkillRecord(
        root=label,
        path=str(skill_file),
        real_path=normalized_path(skill_file),
        reparse_entry=is_reparse_point(skill_file.parent),
    )
    text = read_text(skill_file, record)
    record.line_count = len(text.splitlines())
    if record.line_count > MAX_BODY_LINES:
        record.warnings.append(f"over-500-lines:{record.line_count}")
    validate_frontmatter(text, record)
    (
        record.risk_signals,
        record.guarded_signals,
        record.contextual_signals,
    ) = classify_risk_signals(text)
    record.missing_links = check_links(text, skill_file)
    if record.missing_links:
        record.warnings.append(f"missing-links:{len(record.missing_links)}")
    return record


def collect(
    roots: list[tuple[str, Path]], include_system: bool
) -> tuple[list[SkillRecord], list[str]]:
    records_by_real_path: dict[str, SkillRecord] = {}
    root_notes: list[str] = []

    for label, root in roots:
        root = root.expanduser()
        if not root.is_dir():
            root_notes.append(f"missing-root:{label}={root}")
            continue
        for skill_file in iter_skill_files(root, include_system):
            real_path = normalized_path(skill_file)
            if real_path in records_by_real_path:
                records_by_real_path[real_path].aliases.append(str(skill_file))
                continue
            records_by_real_path[real_path] = build_record(label, skill_file)

    records = sorted(
        records_by_real_path.values(),
        key=lambda item: ((item.name or ""), item.path.lower()),
    )
    return records, root_notes


def duplicate_groups(records: list[SkillRecord]) -> list[dict[str, object]]:
    by_name: dict[str, list[SkillRecord]] = {}
    for record in records:
        if record.name:
            by_name.setdefault(record.name, []).append(record)

    groups: list[dict[str, object]] = []
    for name, items in sorted(by_name.items()):
        if len(items) < 2:
            continue
        content_hashes = {item.content_sha256 for item in items}
        raw_hashes = {item.sha256 for item in items}
        groups.append(
            {
                "name": name,
                "kind": "identical-physical-copies"
                if len(content_hashes) == 1
                else "divergent-physical-copies",
                "raw_byte_identical": len(raw_hashes) == 1,
                "paths": [item.path for item in items],
            }
        )
    return groups


def render_text(
    records: list[SkillRecord],
    roots: list[tuple[str, Path]],
    root_notes: list[str],
    duplicates: list[dict[str, object]],
) -> None:
    print("Roots:")
    for label, root in roots:
        print(f"  - {label}: {root}")
    for note in root_notes:
        print(f"  - warning: {note}")

    error_count = sum(bool(record.errors) for record in records)
    warning_count = sum(bool(record.warnings) for record in records)
    risk_count = sum(bool(record.risk_signals) for record in records)
    review_count = sum(
        bool(record.guarded_signals or record.contextual_signals)
        for record in records
    )
    print(
        "\nSummary: "
        f"{len(records)} unique skill targets; "
        f"{error_count} with validator errors; "
        f"{warning_count} with warnings; "
        f"{risk_count} with unguarded static risk signals; "
        f"{review_count} with guarded/contextual mentions; "
        f"{len(duplicates)} duplicate-name groups."
    )

    print("\nSkills:")
    for record in records:
        status = "ERROR" if record.errors else "OK"
        extras: list[str] = []
        if record.warnings:
            extras.append("warnings=" + ",".join(record.warnings))
        if record.risk_signals:
            extras.append("signals=" + ",".join(record.risk_signals))
        if record.guarded_signals:
            extras.append("guarded=" + ",".join(record.guarded_signals))
        if record.contextual_signals:
            extras.append("contextual=" + ",".join(record.contextual_signals))
        if record.aliases:
            extras.append(f"junction-aliases={len(record.aliases)}")
        suffix = "; " + "; ".join(extras) if extras else ""
        print(
            f"  [{status}] {record.name or '<unknown>'} "
            f"({record.root}, {record.line_count} lines){suffix}"
        )
        print(f"       {record.path}")
        for error in record.errors:
            print(f"       error: {error}")
        for link in record.missing_links:
            print(f"       missing link: {link}")

    if duplicates:
        print("\nDuplicate names:")
        for group in duplicates:
            print(f"  - {group['name']}: {group['kind']}")
            if (
                group["kind"] == "identical-physical-copies"
                and not group["raw_byte_identical"]
            ):
                print("      note: normalized content matches may still differ in raw bytes")
            for path in group["paths"]:
                print(f"      {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inventory of active local Agent Skills. "
            "Static signals require human or model review."
        )
    )
    parser.add_argument(
        "--root",
        action="append",
        type=parse_root,
        help=(
            "Root to scan, optionally label=path. Repeat for multiple roots. "
            "Defaults to shared, Codex, Claude, and Superpowers active roots."
        ),
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="Include bundled .system skills. Plugin caches remain out of scope.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Write the report to stdout in text or JSON form.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when validator errors or divergent duplicate names exist.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    roots = args.root or default_roots()
    records, root_notes = collect(roots, args.include_system)
    duplicates = duplicate_groups(records)

    if args.format == "json":
        payload = {
            "roots": [
                {"label": label, "path": str(path)} for label, path in roots
            ],
            "root_notes": root_notes,
            "skills": [asdict(record) for record in records],
            "duplicates": duplicates,
        }
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        render_text(records, roots, root_notes, duplicates)

    has_errors = any(record.errors for record in records)
    has_divergence = any(
        group["kind"] == "divergent-physical-copies" for group in duplicates
    )
    return 1 if args.strict and (has_errors or has_divergence) else 0


if __name__ == "__main__":
    raise SystemExit(main())
