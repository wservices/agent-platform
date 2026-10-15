# agents/platform

Foundation for the Hermes Agent cybersecurity ecosystem: shared conventions,
reusable GitLab CI, security policy, the cross-agent handoff format, and the
central implementation progress document. Every repo under
`agents/cybersecurity/` and `agents/shared/cybersecurity/` depends on this one.

## Contents

| Path | What |
|---|---|
| `docs/HERMES-INTEGRATION.md` | How skills install/load/run in Hermes + the Kali sandbox (verified) |
| `docs/GITLAB-ARCHITECTURE.md` | Group/repo layout, provisioning, shared-skill dependency mechanism |
| `policies/SECURITY-POLICY.md` | The 14 non-negotiable rules + container privilege model |
| `policies/HANDOFF-FORMAT.md` | `handoff.yaml` schema for cross-agent work |
| `templates/ROLE.template.md` | Starting point for a role's `ROLE.md` |
| `templates/SKILL.template.md` | Starting point for a `SKILL.md` (Hermes format) |
| `ci/validate_skills.py` | SKILL.md frontmatter/format validator (used by CI) |
| `ci/secret_scan.py` | Conservative committed-secret scanner (used by CI) |
| `ci/skill-ci.gitlab-ci.yml` | Reusable CI template repos `include:` |
| `scripts/gitlab_provision.sh` | Idempotent group/subgroup/project creation via API |
| `IMPLEMENTATION.md` | Central progress tracker (completed/tested/published/blocked/planned) |

## Using the CI template

In any role/shared repo's `.gitlab-ci.yml`:

```yaml
include:
  - project: 'agents/platform'
    ref: v0.1.0
    file: '/ci/skill-ci.gitlab-ci.yml'
```

## Using the validator locally

```bash
python3 ci/validate_skills.py path/to/skills      # human output
python3 ci/validate_skills.py --json path/to/skills
python3 ci/secret_scan.py .
```

## Status

Phase 1 (foundation) + an exemplar vertical are implemented. See
`IMPLEMENTATION.md` for exactly what is completed, tested, published, blocked,
and planned. Nothing is marked complete on the strength of placeholder content.

## License

MIT. See the security policy for authorization and usage restrictions that bind
every agent in this ecosystem.
