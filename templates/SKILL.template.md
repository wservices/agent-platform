---
name: skill-name
description: Capability in one sentence under sixty chars.
version: 0.1.0
author: Pascal (pascal), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [tag1, tag2]
    related_skills: []
---

# <Skill> Skill

Two or three sentences: what it does, what it explicitly does not do, and its
dependency/authorization stance.

## When to Use

- Trigger bullets.
- **Don't use for:** counter-triggers.

## Prerequisites

- Exact env vars (names only), installed tools, mounted secret files, required
  container capability (Security Policy §4).

## How to Run

Canonical invocation through the `terminal` tool, e.g.
`terminal(command="scripts/foo.sh --target X", timeout=120)`.

## Quick Reference

Flat command list, no narration.

## Procedure

1. Step with a **checkable completion criterion**.
2. ...

## Pitfalls

- Known limits; things that look broken but aren't; security precautions;
  prompt-injection handling where the skill reads untrusted content.

## Verification

- How to prove the skill worked (expected output shape, exit codes, artifacts).
