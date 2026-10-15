#!/usr/bin/env python3
"""Fail CI if a committed file looks like it contains a real secret.

Conservative, low-false-positive patterns only: private keys, AWS keys,
GitLab/GitHub PATs, Wazuh/NVD-style bearer tokens assigned to obvious keys,
and generic `password =`/`token =` assignments with a long literal value.

Placeholders are allowed: values that are clearly templated (<...>, ${...},
CHANGEME, example, redacted, xxxx) never fail.

Usage: python3 secret_scan.py [path ...]   # defaults to "."
Exit 0 = clean, 1 = suspected secret found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(
    r"<[^>]+>|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|change[_-]?me|example|redacted|placeholder"
    r"|your[_-]|xxx+|\.\.\.|REPLACE|os\.environ|getenv|environ\[",
    re.IGNORECASE,
)

# Honor an inline allowlist pragma (same convention as detect-secrets) so
# deliberate test fixtures / fake sample values don't fail CI.
PRAGMA = re.compile(r"pragma:\s*allowlist\s+secret", re.IGNORECASE)

# Values that are obviously code, not a literal secret.
_NOT_A_LITERAL = re.compile(r"[(){}]|^(None|True|False|null|nil)$|^[A-Za-z_][A-Za-z0-9_.]*\($")

PATTERNS = {
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    "aws access key id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "gitlab PAT": re.compile(r"\bglpat-[0-9A-Za-z_-]{20,}\b"),
    "github PAT": re.compile(r"\bgh[pousr]_[0-9A-Za-z]{36,}\b"),
    "slack token": re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
    "generic secret assignment": re.compile(
        r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?([^\s'\"]{12,})['\"]?"
    ),
}

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", ".pytest_cache"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".pcap", ".bin"}


def iter_files(roots: list[str]):
    for root in roots:
        p = Path(root)
        if p.is_file():
            yield p
            continue
        for f in p.rglob("*"):
            if f.is_dir():
                continue
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            if f.suffix.lower() in SKIP_SUFFIXES:
                continue
            yield f


def scan_line(line: str) -> list[str]:
    if PRAGMA.search(line):
        return []
    hits = []
    for label, rx in PATTERNS.items():
        m = rx.search(line)
        if not m:
            continue
        # For the generic assignment, the captured value must look like a real
        # literal secret — not a placeholder, env var, or code expression.
        if label == "generic secret assignment":
            value = m.group(2)
            if PLACEHOLDER.search(value) or PLACEHOLDER.search(line):
                continue
            if _NOT_A_LITERAL.search(value):
                continue
        hits.append(label)
    return hits


def main(argv: list[str] | None = None) -> int:
    roots = argv if argv else sys.argv[1:] or ["."]
    found = 0
    for f in iter_files(roots):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for label in scan_line(line):
                print(f"SECRET? {f}:{i} [{label}]")
                found += 1
    if found:
        print(f"\n{found} suspected secret(s) found", file=sys.stderr)
        return 1
    print("secret scan clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
