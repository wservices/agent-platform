#!/usr/bin/env python3
"""Validate Hermes-Agent SKILL.md files against repo conventions.

This mirrors the hard requirements of Hermes' own validator
(`tools/skill_manager_tool.py::_validate_frontmatter`) plus the stricter
"hardline" authoring standards used across the agents/ GitLab group:

  * frontmatter starts at byte 0 with `---` (no BOM, no leading blank line)
  * frontmatter closes with a line containing only `---`
  * frontmatter parses as a YAML mapping
  * required keys: name, description, version, author, license, platforms
  * description <= 60 chars and ends with a period
  * name is lowercase, hyphen-separated, <= 64 chars
  * version is semver (X.Y.Z)
  * platforms is a non-empty list drawn from {linux, macos, windows}
  * body after the closing `---` is non-empty
  * total file <= 100_000 chars

Exit code 0 => all SKILL.md files valid. Non-zero => at least one failure.

Usage:
    python3 validate_skills.py [root ...]        # defaults to "skills"
    python3 validate_skills.py --json skills

Pure stdlib except PyYAML; falls back to a tiny frontmatter parser when
PyYAML is unavailable so the script still runs in a minimal CI image.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
VALID_PLATFORMS = {"linux", "macos", "windows"}
MAX_SKILL_CHARS = 100_000
MAX_NAME_LEN = 64
MAX_DESC_LEN = 60
REQUIRED_KEYS = ("name", "description", "version", "author", "license", "platforms")


def _parse_frontmatter(text: str):
    """Return (frontmatter_dict, body_str). Raises ValueError on structure errors."""
    if not text.startswith("---"):
        raise ValueError("file must start with '---' (no BOM or leading blank line)")
    # Find the closing '---' on its own line, after the opening fence.
    m = re.search(r"\n---[ \t]*\n", text[3:])
    if not m:
        raise ValueError("frontmatter not closed with a line containing only '---'")
    fm_text = text[3 : m.start() + 3]
    body = text[m.end() + 3 :]
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(fm_text)
    except ImportError:
        data = _naive_yaml(fm_text)
    if not isinstance(data, dict):
        raise ValueError("frontmatter does not parse as a YAML mapping")
    return data, body


def _naive_yaml(fm_text: str) -> dict:
    """Minimal YAML subset parser: top-level 'key: value' and inline [lists].

    Only used when PyYAML is absent. Good enough for the flat frontmatter this
    repo mandates; nested 'metadata:' blocks are ignored (not validated here).
    """
    out: dict = {}
    for line in fm_text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":  # nested (e.g. under metadata:) -> skip
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            out[key] = items
        else:
            out[key] = val.strip().strip("'\"")
    return out


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    raw = path.read_text(encoding="utf-8", errors="replace")
    if len(raw) > MAX_SKILL_CHARS:
        errors.append(f"file is {len(raw)} chars (> {MAX_SKILL_CHARS})")
    try:
        fm, body = _parse_frontmatter(raw)
    except ValueError as exc:
        return [str(exc)]

    for key in REQUIRED_KEYS:
        if key not in fm:
            errors.append(f"missing required frontmatter key: {key}")

    name = fm.get("name", "")
    if name and not NAME_RE.match(str(name)):
        errors.append(f"name '{name}' must be lowercase/hyphenated")
    if name and len(str(name)) > MAX_NAME_LEN:
        errors.append(f"name is {len(str(name))} chars (> {MAX_NAME_LEN})")

    desc = fm.get("description", "")
    if desc:
        if len(str(desc)) > MAX_DESC_LEN:
            errors.append(f"description is {len(str(desc))} chars (hardline <= {MAX_DESC_LEN})")
        if not str(desc).rstrip().endswith("."):
            errors.append("description must end with a period")

    version = fm.get("version", "")
    if version and not SEMVER_RE.match(str(version)):
        errors.append(f"version '{version}' is not semver X.Y.Z")

    platforms = fm.get("platforms")
    if platforms is not None:
        if not isinstance(platforms, list) or not platforms:
            errors.append("platforms must be a non-empty list")
        else:
            bad = sorted(set(map(str, platforms)) - VALID_PLATFORMS)
            if bad:
                errors.append(f"platforms has invalid entries: {bad}")

    if not body.strip():
        errors.append("body after frontmatter is empty")

    return errors


def discover(roots: list[str]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        p = Path(root)
        if p.is_file() and p.name == "SKILL.md":
            found.append(p)
        elif p.is_dir():
            found.extend(sorted(p.rglob("SKILL.md")))
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Hermes SKILL.md files")
    ap.add_argument("roots", nargs="*", default=["skills"], help="files or dirs to scan")
    ap.add_argument("--json", action="store_true", help="emit a JSON report")
    args = ap.parse_args(argv)

    files = discover(args.roots or ["skills"])
    report = {}
    failed = 0
    for f in files:
        errs = validate_file(f)
        report[str(f)] = errs
        if errs:
            failed += 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if not files:
            print("WARNING: no SKILL.md files found", file=sys.stderr)
        for f in files:
            errs = report[str(f)]
            if errs:
                print(f"FAIL {f}")
                for e in errs:
                    print(f"      - {e}")
            else:
                print(f"OK   {f}")
        print(f"\n{len(files) - failed}/{len(files)} SKILL.md files valid")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
