---
name: skill-stocktake
description: "Use when the user explicitly asks to audit, inventory, consolidate, or improve a local Agent Skill library for quality, overlap, staleness, safety, portability, or context bloat. Produce evidence-backed Keep/Improve/Update/Retire/Merge verdicts; do not use for ordinary task routing or discovery."
---

# Skill Stocktake

Audit an active Skill library without turning static signals into automatic verdicts.

## Scope

Discover the active roots from the current agent runtime. Common examples are:

- shared Skills under `$HOME/.agents/skills`;
- the current runtime's own Skill root;
- Superpowers Skills under `$HOME/.agents/superpowers/skills`.

Exclude bundled system and plugin-cache Skills unless the user explicitly asks to audit them. Audit project-local roots separately and label them.

Use `scripts/audit_skills.py` for read-only inventory and mechanical evidence. It separates unguarded risk signals from guarded prohibitions and container-specific command context. It does not edit Skills, create a cache, install dependencies, access the network, or decide which Skills to retire.

## Workflow

1. Read the governing agent policy file for the current environment and this Skill completely.
2. Preserve a baseline before edits using version control or a backup outside active roots.
3. Resolve the directory containing this `SKILL.md`, then run:

   ```bash
   python -X utf8 "<skill-dir>/scripts/audit_skills.py"
   ```

4. Use `--format json` when another tool consumes the result. Use repeatable `--root label=path` arguments for custom roots.
5. Read every `SKILL.md` selected for a verdict completely. For Retire or Merge, also read the proposed covering alternative or merge target completely. Read only directly relevant scripts and references.
6. Judge each Skill holistically using the dimensions below.
7. Forward-test substantial trigger or workflow changes with independent read-only agents only when delegation is authorized.
8. Validate changed Skills with the official validator provided by the current runtime in UTF-8 mode.
9. Present retirement and merge candidates with impact analysis. Never delete, move, retire, or merge without explicit confirmation.

For substantial prompt, trigger, or workflow rewrites, compare the preserved baseline and candidate on the same representative tasks. Keep test agents blind to the intended verdict; when several agents are used, assign non-overlapping paths and a fixed output schema. Require correctness and safety first, then compare instruction adherence and, when available, tokens, latency, and cost. Skip A/B for metadata-only or mechanical fixes.

## Judgment Dimensions

- **Trigger fit**: the description states the real intent, explicit-only boundary, and important near misses; the body does not widen the trigger.
- **Actionability**: instructions add executable value beyond a capable current model.
- **Uniqueness**: the job, output, tools, audience, and success criteria are not already owned by global policy or a stronger Skill.
- **Currency**: tool names, CLI flags, APIs, paths, versions, and platform assumptions are current.
- **Safety and authorization**: external sends, credentials, installs, background processes, destructive actions, Git writes, and persistence are confirmed at the right boundary.
- **Context efficiency**: the body is concise; detailed variants live in shallow references; deterministic work lives in tested scripts.
- **Portability**: personal paths and unnecessary model-specific tool names are avoided.
- **Validation**: YAML, folder/name alignment, links, scripts, and realistic trigger examples are verified.

Treat line count, duplicate names, stale tool tokens, risky command strings, or missing links as leads to inspect, not proof of a defect.

## Verdicts

| Verdict | Meaning |
| --- | --- |
| Keep | Useful, current, well-scoped, and worth its context cost |
| Improve | Identity is sound; wording, workflow, safety, or resources need a bounded change |
| Update | External technology, tool interface, or runtime assumption is stale |
| Retire | Little unique value remains, or risk and maintenance cost exceed the benefit |
| Merge into X | Another Skill owns the same job; name the exact material to preserve in X |

Every verdict must name concrete evidence and its user-visible or operational impact. For Retire, name the covering alternative; for Merge, name the exact target and transferable material; for Improve or Update, propose the smallest useful change.

## Validation

Run the runtime's official Skill validator with UTF-8 enabled. A typical Codex layout is:

```text
<codex-home>/skills/.system/skill-creator/scripts/quick_validate.py
```

For changed scripts, run syntax checks and safe representative executions. Do not execute deletion, network submission, credential access, installers, services, or persistent background-process paths merely to test them.

## Privacy

Reports contain absolute paths, descriptions, hashes, and local structure. Keep raw reports local unless they have been reviewed and redacted.

## Completion

Report roots and exclusions, inventory totals, duplicate or drift findings, verdicts with evidence, files changed, the preserved baseline, validation results, deferred retirements or merges, and unresolved risk.
