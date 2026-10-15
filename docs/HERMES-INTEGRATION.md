# Hermes Agent Integration Guide

How the `agents/cybersecurity` ecosystem plugs into Hermes Agent. Everything
here was verified against a live install (Hermes `v0.21.7`, Python 3.14) — see
`## Verified against` at the end. Where this differs from the generic
"ChatGPT-style" SKILL.md the task brief assumed, the difference is called out.

## 1. Skill format (Hermes-specific)

Hermes skills live in `~/.hermes/skills/<category>/<name>/SKILL.md` (user-local)
or `skills/<category>/<name>/SKILL.md` inside a project/repo. The validator of
record is `tools/skill_manager_tool.py::_validate_frontmatter` in the
hermes-agent source; the authoring standards are in that repo's
`hermes-agent-skill-authoring` skill.

**Required frontmatter** (stricter than the brief's generic spec):

```yaml
---
name: wazuh-alert-triage               # lowercase-hyphen, <= 64 chars
description: Triage a Wazuh alert into noise, benign, or incident.   # <= 60 chars, ends with '.'
version: 0.1.0                         # semver
author: Pascal (pascal), Hermes Agent  # human first
license: MIT
platforms: [linux, macos]              # audited, not guessed
metadata:
  hermes:
    tags: [wazuh, soc, triage]
    related_skills: [wazuh-authentication, cve-research]
---
```

**Body section order** Hermes expects: `# <Skill> Skill` intro, then
`## When to Use`, `## Prerequisites`, `## How to Run`, `## Quick Reference`,
`## Procedure` (numbered, each step with a completion criterion), `## Pitfalls`,
`## Verification`.

**Deltas from the brief's generic SKILL.md spec:**

| Brief said | Hermes reality |
|---|---|
| free-form metadata/description | `description` **hard-capped at 60 chars**, must end with `.` |
| "triggering conditions", "error handling" sections | expressed as `## When to Use` and `## Pitfalls` / `## Procedure` steps |
| raw CLI prose ("run `foo`") | frame as the `terminal` tool: `terminal(command="foo ...", timeout=...)`; Hermes wraps `grep`→`search_files`, `cat`→`read_file` |
| one big SKILL.md | entrypoint ~100–200 lines; bulk goes to `references/*.md`, logic to `scripts/` (progressive loading) |

The brief's richer requirements (input validation, security precautions,
evidence/reporting) are satisfied *inside* the Hermes sections rather than as
extra top-level headings.

## 2. Installing a skill from the public mirror (GitHub)

Hermes installs skills with `hermes skills install <identifier | URL>`. The
open-core skills are published as flat repos on `github.com/wservices/skill-*`,
so install from the raw SKILL.md on the default branch:

```bash
hermes skills install \
  "https://raw.githubusercontent.com/wservices/skill-cve-research/main/skills/cve-research/SKILL.md" \
  --category security --name cve-research
```

`hermes skills check` / `hermes skills update` re-fetch this exact URL and
compare content hashes, so a `main` URL stays current on `update` (locally
edited skills are skipped unless `--force`). Swap `main` for a tag or commit SHA
in the URL when you want a pinned, reproducible revision. `hermes skills inspect`
previews before install; `hermes skills audit` re-scans installed skills.

> A raw SKILL.md URL installs only that file. For a skill that ships `scripts/`
> or `references/` (e.g. `cve-research`), install the full bundle by cloning its
> repo and `hermes skills trust`-ing it — see the skill's README.

> Caveat: `hermes skills install` from a single raw URL fetches the SKILL.md. If
> a skill ships `scripts/` or `references/`, prefer the project-local method
> (next section) or a packaged install so the supporting files come along. This
> is tracked as a follow-up in `platform/IMPLEMENTATION.md`.

## 3. Project-local (repo-trusted) skills

Hermes loads repo-local skills from `./.hermes/skills` or `./.agents/skills` in a
**trusted** project:

```bash
git clone git@gitlab.wservices.ch:agents/cybersecurity/security-analyst.git
cd security-analyst
hermes skills trust .      # trust this project so its repo-local skills load
```

For a role repo, symlink or copy its `skills/` into `./.hermes/skills/` (or lay
the repo out with a top-level `.hermes/skills/`). This keeps the full skill
bundle (scripts, references) intact and version-controlled with the role.

## 4. Running inside the Kali sandbox

The install already uses a Docker sandbox with the official Kali image. Relevant
config (`~/.hermes/config.yaml`, `terminal:` section), verified present:

```yaml
terminal:
  backend: "docker"
  docker_image: "kalilinux/kali-rolling"
  docker_mount_cwd_to_workspace: true    # launch cwd -> /workspace in container
  docker_run_as_host_user: true          # files owned by host user; SETUID dropped
  docker_forward_env: ["GITHUB_TOKEN", "NPM_TOKEN"]
  container_persistent: true             # filesystem persists across sessions
```

Implications for these skills:

- **Tool persistence:** with `container_persistent: true`, APT/pipx installs
  persist across sessions. If a deployment uses an **ephemeral** container, tools
  must be reinstalled — hence every role ships `tools/install.sh` + `packages.txt`
  so the environment is reproducible either way. Do not assume tools survive a
  container *recreation*.
- **Secrets:** pass API credentials (Wazuh, NVD, VirusTotal, …) by adding their
  env var names to `docker_forward_env` and defining them in `~/.hermes/.env` or
  the host shell — never in a repo or image.
- **Capabilities:** raw-socket tools (`tcpdump`, `nmap -sS`, `masscan`) need
  `--cap-add NET_RAW` via `docker_extra_args`. See `policies/SECURITY-POLICY.md`
  §4. Never `--privileged`.
- **Working dir:** skills write case artifacts under `/workspace/cases/<id>/`.

## 5. Base image

The shared base image (`skills/security/security-tooling`) layers common CLI
utilities onto `kalilinux/kali-rolling`. Roles add only their own tool layer via
`tools/install.sh`. The Kali default-everything metapackage is **not** installed.

## 6. Roles are profiles (distributions)

A security *role* is modeled as a Hermes **profile**, not a loose bundle of
skills. A profile is an isolated agent instance with its own home (`SOUL.md`
persona, `config.yaml`, `skills/`, memory, `cron/`, messaging identity). Verified
mechanics (`hermes profile --help`, `hermes_cli/profile_distribution.py`):

- **Create locally:** `hermes profile create security-analyst --description "..."`.
- **Install from Git (public):** `hermes profile install https://github.com/wservices/agent-security-analyst.git`
  — reads `distribution.yaml` at the repo root; `hermes profile update` re-pulls
  the default branch (no pin needed).
- **Manifest fields** (confirmed): `name`, `version`, `description`,
  `hermes_requires`, `author`, `license`, `env_requires` (list of
  `{name, required, description, default}` → generates `.env.EXAMPLE`),
  `distribution_owned` (files the dist replaces on update; default
  `SOUL.md, config.yaml, mcp.json, skills, cron, distribution.yaml`).
- **Keep `config.yaml` out of `distribution_owned`** so installing a role does
  not overwrite the user's model/provider choice.
- **Update:** `hermes profile update <name>` re-pulls; user data (`.env`, memory,
  history) is preserved.
- **Run:** `hermes -p <name> <cmd>` (e.g. `chat`, `gateway`).

### Orchestration

`distribution.yaml.description` (and `hermes profile describe`) feeds the
**kanban decomposer**, which routes tasks to profiles **by role**. Combined with
`delegate_task` and the handoff schema (`policies/HANDOFF-FORMAT.md`), the
Security Team Lead profile acts as orchestrator. The auto-routing path is not
claimed working until tested end-to-end — tracked in `IMPLEMENTATION.md`; until
then handoffs are `handoff.yaml` artifacts routed by the Lead or a human.

## Verified against

- `hermes --version` → `v0.21.7+279.g63d0b94 (2026.9.24)`
- `hermes skills --help` → subcommands incl. `install`, `tap`, `trust`, `inspect`
- `hermes skills install --help` → accepts an identifier or a direct SKILL.md URL, `--category`, `--name`
- `~/.hermes/config.yaml` `terminal:` block (Docker/Kali settings quoted above)
- `~/.hermes/skills/software-development/hermes-agent-skill-authoring/SKILL.md` (format rules)
