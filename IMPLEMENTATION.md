# Cybersecurity Agent Ecosystem — Implementation Progress

Central tracker for the Hermes cybersecurity agent/skills ecosystem on
`gitlab.wservices.ch` under the `agents` group. Status legend:

- ✅ **complete** — implemented, deep (not placeholder), tested, pushed
- 🧪 **tested** — unit tests pass locally (mocked; no live integration)
- 🚀 **published** — pushed to GitLab and remote commit verified
- ⛔ **blocked** — see blocker note
- 📋 **planned** — scaffold/spec exists; not yet implemented

> Policy: a role is **not** marked complete while it holds only placeholder
> skills. Integrations are not claimed working until tested against a real or
> faithfully-mocked target.

## Architecture

- **Roles are Hermes profiles** (distributions) at `agents/<team>/<role>` —
  installed via `hermes profile install`. Each carries `distribution.yaml` +
  `SOUL.md` + `skills/`. See `docs/HERMES-INTEGRATION.md` §6.
- **Skills** live in a dedicated top-level group `skills/<category>/<skill>`
  (e.g. `skills/security/cve-research`), consumed by profiles and pinned to a
  tag. (Moved out of the former `agents/shared/...` on 2026-10-15.)
- **Open-core:** private GitLab (`gitlab.wservices.ch`) stays the source of truth;
  the framework + defensive/generic skills are mirrored to **public GitHub**
  (`github.com/wservices/agent-*`, `skill-*`, `platform`) for one-command
  anonymous-HTTPS install. `secret_scan` gates any publish; a `gh`-based mirror
  publisher is a follow-up (gh not yet installed). Public install URLs use the
  default branch so `hermes profile/skills update` keeps them current.

## Strategy

Chosen approach: **exemplar vertical first** — foundation + one fully-worked
role profile + the skills it needs, proven end to end (GitLab publish + CI),
then replicate across the remaining 28 roles and 4 skills. This doc is the record.

## Environment facts (verified)

| Item | Value |
|---|---|
| Hermes | v0.21.7+279.g63d0b94 (2026.9.24) |
| Skill format | `~/.hermes/skills/<cat>/<name>/SKILL.md`; desc ≤60 chars; fixed section order |
| Skill install | `hermes skills install <id\|URL> --category`; `tap`; `trust` (project-local) |
| Sandbox | docker; image `kalilinux/kali-rolling`; cwd→/workspace; `container_persistent: true` |
| GitLab auth | SSH as `@pascal`; API via `glab` (token, `can_create_group: true`) |
| `agents` group | exists (id 94); `agents/cybersecurity` subgroup exists |
| Docker daemon | not running locally → live Kali package/image checks deferred |

## Phase 1 — Foundation  ✅ (pending publish)

| Deliverable | Status | Notes |
|---|---|---|
| `agents/platform` repo | ✅ 🧪 | conventions, CI, policies, templates, progress doc |
| Security policy (14 rules + capability model) | ✅ | `policies/SECURITY-POLICY.md` |
| Cross-agent handoff format | ✅ | `policies/HANDOFF-FORMAT.md` + validator in security-analyst |
| Hermes integration guide | ✅ | `docs/HERMES-INTEGRATION.md` (verified mechanisms) |
| GitLab architecture + shared-skill dependency mechanism | ✅ | `docs/GITLAB-ARCHITECTURE.md` |
| Reusable CI template | ✅ 🧪 | `ci/skill-ci.gitlab-ci.yml` + `validate_skills.py` + `secret_scan.py` |
| ROLE/SKILL templates | ✅ | `templates/` |
| Idempotent GitLab provisioner | ✅ | `scripts/gitlab_provision.sh` (API) |
| Kali base image + tooling (`shared/.../security-tooling`) | ✅ 🧪 | Dockerfile + manifest + install/verify scripts; **image build deferred** (no local docker) |

Foundation tests: `platform` 11 passed; `security-tooling` 7 passed.

## Phase 2 — Core SOC

| Role | Status | Notes |
|---|---|---|
| `security-analyst` | ✅ 🧪 | 6 deep skills + 4 tested scripts (Wazuh client, auth-log, IOC, handoff); 23 tests pass |
| `incident-responder` | 📋 | skills specced in task §6.4 |
| `detection-engineer` | 📋 | Sigma/YARA/Suricata/Wazuh rule skills |
| `threat-intelligence-analyst` | 📋 | OSINT/IOC enrichment (shares `security-osint`) |

Shared skills:

| Shared skill | Status | Notes |
|---|---|---|
| `skills/security/cve-research` | ✅ 🧪 | NVD/KEV/EPSS/OSV consolidation; 8 tests; KEV/EPSS/CVSS distinction enforced |
| `skills/security/security-tooling` | ✅ 🧪 | base image + install framework |
| `security-osint` | 📋 | VirusTotal/AbuseIPDB/URLhaus/Shodan (optional, key-gated) |
| `mitre-attack` | 📋 | technique lookup/mapping |
| `security-reporting` | 📋 | report rendering/handoff helpers |
| `evidence-handling` | 📋 | hashing/chain-of-custody (used by forensics) |

### security-analyst skills detail

Implemented (deep, tested): `wazuh-authentication`, `wazuh-alert-search`,
`wazuh-alert-triage`, `linux-auth-log-analysis`, `ioc-extraction`,
`soc-investigation-reporting`.

Planned (task §6.1): wazuh-event-investigation, ssh-brute-force-detection
(covered partly by linux-auth-log-analysis), web/firewall/DNS log analysis,
email-security/phishing, network-traffic-analysis, suspicious-process-analysis,
timeline-reconstruction, security-event-correlation, false-positive-id,
incident-escalation. Wazuh set (task §6.2) remaining: agent-inventory,
threat-hunting, vulnerability-detection, FIM/syscheck, rootcheck, SCA,
compliance-reporting, active-response-analysis (read-only), rule/decoder
development (Detection Engineer owns the authoring variants).

## Phases 3–6 — 📋 planned

Phase 3 (Vuln/Pentest): vulnerability-manager, vulnerability-researcher,
penetration-tester, web-security-specialist. Phase 4 (Forensics):
digital-forensics-analyst, malware-analyst, threat-hunter. Phase 5
(Eng/AppSec): security/network/cloud/identity/application/devsecops/
security-automation engineers, software-supply-chain-analyst, ai-security-engineer.
Phase 6 (Governance/Lead): security-risk-analyst, compliance-analyst,
privacy-security-specialist, business-continuity-specialist, security-auditor,
security-architect, security-advisor, security-team-lead, red-team-operator.

All 29 roles + 6 shared repos are enumerated in `docs/GITLAB-ARCHITECTURE.md`.

## Phase 7 — Integration & verification

| Check | Status |
|---|---|
| Repo structure | ✅ for the exemplar vertical |
| Commits + remote branches | 🚀 see "Publish log" |
| Skills discoverable by Hermes | 📋 (format validated; live `hermes skills` load untested this session) |
| CLI tool install (Kali) | 📋 (package names verified via web; live install deferred — no local docker) |
| SOC workflow w/ mocked Wazuh | ✅ 🧪 (wazuh_api summary + query tests) |
| CVE lookup vs public resources | 🧪 mocked; live smoke documented in SKILL |
| Forensic workflow (synthetic) | 📋 |
| Safe pentest vs local target | 📋 |

## Blockers / deferred

1. **Local Docker daemon not running** → could not build the Kali base image or
   verify packages in a live container. Package names verified against the Kali
   web index; `zeek`/`osv-scanner` confirmed NOT apt-installable and handled
   accordingly. Live build is a follow-up (CI job `base-image` gated on a docker
   runner).
2. **Shared-skill install via single raw SKILL.md URL** doesn't carry
   `scripts/`/`references/`. Mitigation documented (clone + `hermes skills trust`,
   or submodule). A packaged-install path is a follow-up.
3. **Multi-agent auto-delegation** (`delegate_task`) not yet validated
   end-to-end; handoffs are artifact-based until proven.

## Publish log

All four exemplar repos pushed to `gitlab.wservices.ch` and remote commits
verified via `git ls-remote` (2026-10-15):

Current layout (after the 2026-10-15 profile+skills restructure); remote commits
verified via `git ls-remote`:

| Repo | main commit | tag | GitLab CI |
|---|---|---|---|
| `agents/platform` | 19b330c | v0.1.0/1/2 | self-test green |
| `agents/cybersecurity/security-analyst` (profile) | 209b28a | v0.1.0 | pipeline 1289 ✅ 7 jobs |
| `skills/security/cve-research` | 9e504ac | v0.1.0 | pipeline 1288 ✅ |
| `skills/security/security-tooling` | b990020 | v0.1.0 | pipeline 1287 ✅ |

All three consumer pipelines pass against the portable template
`agents/platform@v0.1.2` (clones helpers via `CI_SERVER_HOST`+`CI_JOB_TOKEN`;
consumers in platform's inbound job-token allowlist, project ids 38/39/40). Jobs:
skill-metadata, repo-structure, yaml-lint, shell-lint, python-syntax, secret-scan,
unit-tests — on runner `grun.wservices.ch`.

security-analyst is a **profile distribution** (`distribution.yaml` + `SOUL.md`);
shared skills relocated from `agents/shared/...` to `skills/security/...` via the
transfer API (history preserved); empty `agents/shared` subgroups deleted.

Local verification (venv, PyYAML+pytest): platform 11, cve-research 8,
security-tooling 7, security-analyst 23 = **49 tests pass**; 8/8 SKILL.md valid;
secret-scan clean.
