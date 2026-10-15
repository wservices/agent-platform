# GitLab Repository Architecture

Two homes: the **private source of truth** is `gitlab.wservices.ch` (nested
subgroups, shown in the tree below); the **public open-core mirror** is
`github.com/wservices` (flat `agent-*`/`skill-*` repos — see "Open-core mirror").
Internal/dev commands use the private GitLab paths; public install commands use
the GitHub URLs.

## Two kinds of repository

1. **Profiles** — one per role, under `agents/<team>/<role>`. A profile is an
   installable Hermes agent (persona + model/toolsets + its own skills + cron +
   messaging identity). Installed with `hermes profile install`.
2. **Skills** — reusable capabilities, under a dedicated top-level `skills/`
   group by category (`skills/<category>/<skill>`). Consumed by many profiles,
   maintained once.

```
gitlab.wservices.ch/                  # PRIVATE source of truth
├── agents/                           # PROFILES (one repo per role)
│   └── cybersecurity/
│       ├── security-analyst/         # profile distribution
│       ├── incident-responder/
│       └── … (29 roles)
│   └── <future teams: development, infrastructure, marketing, finance, legal>/
├── skills/                           # reusable skills (NEW top-level group)
│   └── security/
│       ├── cve-research/
│       ├── security-tooling/         # + Kali base image
│       ├── security-osint/
│       ├── mitre-attack/
│       ├── security-reporting/
│       └── evidence-handling/
└── agents/platform/                  # framework: conventions, CI, policies, templates
```

Future teams slot in as `agents/<team>/`; future skill domains as
`skills/<domain>/` (e.g. `skills/dev/`, `skills/infra/`).

## Profile distribution (role repo)

Each role repo is a **profile distribution** — a `distribution.yaml` manifest at
the root plus the distribution-owned files:

```
agents/cybersecurity/security-analyst/
├── distribution.yaml        # name, version, description (kanban routing), env_requires
├── SOUL.md                  # the role persona / system prompt (from ROLE.md)
├── ROLE.md                  # human-readable role definition (source for SOUL.md)
├── skills/                  # the profile's own skills
├── cron/jobs.json           # optional scheduled tasks (paused on install)
├── tools/                   # Kali tool manifest + installer
└── .gitlab-ci.yml
```

`config.yaml` is deliberately **not** distribution-owned (it would overwrite the
user's model/provider). The profile inherits the user's base config and layers
`SOUL.md`, `skills/`, and `env_requires` on top.

Install / run / update (public mirror):

```bash
hermes profile install "https://github.com/wservices/agent-security-analyst.git"
hermes -p security-analyst chat
hermes profile update security-analyst        # re-pull default branch, preserves .env/memory
```

`distribution.yaml`'s `description` feeds the **kanban decomposer**, which routes
tasks to profiles by role — the basis for cross-agent orchestration (the
Security Team Lead profile is the orchestrator).

## Creating groups and repositories

Provision with the API (`glab` or a token with `api` scope). SSH alone cannot
create subgroups.

```bash
# top-level skills group + category subgroup
glab api -X POST groups -f name=skills -f path=skills
glab api -X POST groups -f name=security -f path=security -F parent_id=<SKILLS_ID>
# a role profile repo
glab api -X POST projects -f name=security-analyst -F namespace_id=<CYBERSEC_ID> -f visibility=private
```

`scripts/gitlab_provision.sh` wraps group/subgroup/project creation idempotently.
To move an existing project between groups, use the transfer API (preserves
history): `glab api -X PUT "projects/<id>/transfer" -f "namespace=<group path or id>"`.

## Shared-skill dependency mechanism

Skills live once (private: `skills/<category>/<skill>`; public mirror:
`github.com/wservices/skill-<name>`) and are consumed by many profiles:

- **SKILL.md only (auto-updatable):**
  `hermes skills install "https://raw.githubusercontent.com/wservices/skill-cve-research/main/skills/cve-research/SKILL.md" --category security`
  — `hermes skills update` re-fetches this URL; use `main` for latest or a
  tag/commit SHA for a pinned revision.
- **Full bundle (scripts + references):** clone the skill repo and
  `hermes skills trust` it, or add it as a git submodule pinned to a tag inside
  the profile's `skills/`.
- **Update:** bump the pinned tag in the profile's `ROLE.md`/`distribution.yaml`
  dependency table; `hermes skills update` for hub-tracked skills.

Roles pin to a tag, never `main`. Breaking changes bump MAJOR; announced in the
skill repo's `CHANGELOG.md`.

## CI

Repos `include` the shared template from `agents/platform` (instance-relative,
no host needed). The template clones platform helpers using `CI_JOB_TOKEN` and
`CI_SERVER_HOST`, so it is portable. Consumer projects must be in platform's
inbound job-token allowlist (set via the provisioner / API).

## Branch protection & publishing

Default branch `main`. Never force-push or bypass protection. If `main` is
protected, push a feature branch and open an MR; CI must pass before merge.

## Open-core mirror (public GitHub)

The private GitLab instance (`gitlab.wservices.ch`, nested subgroups) stays the
source of truth. The open-core subset is mirrored to **public** repos on
**`github.com/wservices/`** so anyone can install over anonymous HTTPS:

```bash
hermes profile install "https://github.com/wservices/agent-security-analyst.git"
```

GitHub has no nested groups, so names encode the hierarchy (flat under the org):

| Private (gitlab.wservices.ch, source of truth) | Public mirror (github.com) |
|---|---|
| `agents/cybersecurity/security-analyst` | `wservices/agent-security-analyst` |
| `agents/cybersecurity/<role>` | `wservices/agent-<role>` |
| `skills/security/cve-research` | `wservices/skill-cve-research` |
| `skills/security/<skill>` | `wservices/skill-<skill>` |
| `agents/platform` | `wservices/agent-platform` |

Only the open-core subset is mirrored: internal integrations, real
endpoints/credentials, and sensitive/offensive content are not. Each public repo
carries a **self-contained `.gitlab-ci.yml`→GitHub Actions** CI (no private
cross-project `include`) and a README install command pointing at its GitHub URL.

> Publishing automation: `scripts/publish_mirror.sh` currently targets a GitLab
> API (`glab`). A **GitHub variant (using `gh`) is a follow-up** — `gh` is not
> yet installed/authed here. Until then, publishing to GitHub is manual
> (create repo on github.com/wservices, push), still gated by `secret_scan`.
