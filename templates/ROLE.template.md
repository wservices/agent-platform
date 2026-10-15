# <Role Name>

> Copy this file to a role repo's `ROLE.md` and fill every section. Delete the
> blockquote guidance lines. Keep it factual and specific — no marketing.

## Purpose

One paragraph: what this agent is for and the single outcome it owns.

## Responsibilities

- Bullet list of concrete, recurring responsibilities.

## Expected expertise

- Domains, tools, standards (e.g. NIST SP 800-61, MITRE ATT&CK, Wazuh) the agent
  is expected to apply fluently.

## Supported tasks

- Enumerate the task types this agent handles, phrased as triggers.

## Available skills

| Skill | Status | Summary |
|---|---|---|
| `skill-name` | implemented / planned | one line |

Shared skills consumed (with pinned version):

| Shared skill | Source | Pin |
|---|---|---|
| `cve-research` | `agents/shared/cybersecurity/cve-research` | `v0.1.0` |

## Required tools

Required and optional CLI tools with purpose; see `tools/README.md` and
`tools/packages.txt`. State any required container capability (Security Policy §4).

## Permitted actions

- Read-only operations this agent may always perform.

## Prohibited actions

- Actions this agent must never take autonomously (map to Security Policy rules).

## Escalation conditions

- When this agent escalates and to whom (default: Security Team Lead).

## Interaction with other agents

- Upstream/downstream agents and the handoff triggers (see `HANDOFF-FORMAT.md`).

## Reporting formats

- The report/evidence artifacts this agent produces and where they are stored.
