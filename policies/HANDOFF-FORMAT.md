# Cross-Agent Handoff Format

A single, machine-parseable handoff object every cybersecurity agent uses when
passing work to another agent or escalating to the Security Team Lead. Store it
as `handoff.yaml` in the case directory and attach the human-readable rendering
to the report.

## Schema

```yaml
handoff:
  task_id:          "CASE-2026-0142"        # stable across the whole chain
  originating_agent: "security-analyst"
  receiving_agent:   "threat-intelligence-analyst"
  created_at:        "2026-10-15T11:42:00Z" # UTC
  scope:             "Host web01 (10.0.4.11); Wazuh alert 1.2M event window 10:00-11:30Z"
  summary:           "SSH brute force from 198.51.100.23 followed by a successful auth"
  findings:
    - id: F1
      observation: "87 failed sshd auths then 1 success for user deploy from 198.51.100.23"
      confidence: high            # high | medium | low
      basis: observed             # observed | inferred | assumed
      evidence_refs: ["evidence/auth.log.gz#L4411", "wazuh/alert_5710_5715.json"]
      attack_mapping: ["T1110.001"]   # MITRE ATT&CK technique IDs
  indicators:
    - type: ipv4
      value: "198.51.100.23"      # defanged in prose, raw in structured field
      disposition: suspicious     # malicious | suspicious | benign | unknown
  recommended_next_action: "Enrich 198.51.100.23 reputation; confirm whether deploy login is expected"
  required_approval: none         # none | human-approval | authorization-record
  status: open                    # open | in-progress | blocked | closed
  blockers: []
```

## Rules

- `task_id` is created by the first agent in the chain and never changes.
- Every finding carries `confidence` and `basis` (Security Policy rule 9).
- `evidence_refs` are reproducible pointers (file + line/offset, or stored API
  response), not prose descriptions.
- `required_approval` must be `human-approval` or `authorization-record` for any
  action the receiving agent would take that is intrusive or production-impacting.
- Indicators are defanged in all human-readable text; the structured `value`
  field keeps the raw form for tooling.

## Reference chains (from the task spec)

```
Suspicious Wazuh alert:
  security-analyst -> threat-intelligence-analyst -> incident-responder
    -> digital-forensics-analyst -> security-team-lead

New critical CVE:
  vulnerability-manager -> vulnerability-researcher -> security-engineer
    -> security-team-lead

Web application finding:
  web-security-specialist -> application-security-engineer
    -> vulnerability-manager -> security-team-lead
```

## Hermes delegation note

Hermes exposes a `delegate_task` tool and a `kanban` board for multi-profile
collaboration. Until the orchestration layer is validated end-to-end (tracked in
`platform/IMPLEMENTATION.md`), handoffs are produced as `handoff.yaml` artifacts
and routed either by a human or by the Security Team Lead profile. Do not assume
automatic agent-to-agent dispatch that has not been verified.
