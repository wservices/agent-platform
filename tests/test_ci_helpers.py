"""Unit tests for the platform CI helpers. Stdlib + pytest only, no network."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(mod_name, rel):
    spec = importlib.util.spec_from_file_location(mod_name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


vs = _load("validate_skills", "ci/validate_skills.py")
ss = _load("secret_scan", "ci/secret_scan.py")

GOOD = """---
name: wazuh-alert-triage
description: Triage a Wazuh alert into noise, benign, or incident.
version: 0.1.0
author: Pascal (pascal), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [wazuh, soc]
---

# Wazuh Alert Triage Skill

## When to Use
- body present
"""


def write(tmp_path, text):
    d = tmp_path / "skills" / "x"
    d.mkdir(parents=True)
    f = d / "SKILL.md"
    f.write_text(text)
    return f


def test_good_skill_passes(tmp_path):
    f = write(tmp_path, GOOD)
    assert vs.validate_file(f) == []


def test_description_too_long(tmp_path):
    bad = GOOD.replace(
        "Triage a Wazuh alert into noise, benign, or incident.",
        "Triage a Wazuh alert into noise, benign, or an incident requiring response now.",
    )
    f = write(tmp_path, bad)
    errs = vs.validate_file(f)
    assert any("description is" in e for e in errs)


def test_description_missing_period(tmp_path):
    bad = GOOD.replace("or incident.", "or incident")
    f = write(tmp_path, bad)
    assert any("end with a period" in e for e in vs.validate_file(f))


def test_bad_semver(tmp_path):
    bad = GOOD.replace("version: 0.1.0", "version: 1.0")
    f = write(tmp_path, bad)
    assert any("semver" in e for e in vs.validate_file(f))


def test_leading_blank_line_fails(tmp_path):
    f = write(tmp_path, "\n" + GOOD)
    assert vs.validate_file(f)  # non-empty errors


def test_invalid_platform(tmp_path):
    bad = GOOD.replace("[linux, macos]", "[linux, solaris]")
    f = write(tmp_path, bad)
    assert any("invalid entries" in e for e in vs.validate_file(f))


# Secret-shaped fixtures are built at runtime so no token/key literal ships in
# source (keeps GitHub push protection happy on the public mirror); the scanner
# still sees the full string via scan_line.
def test_secret_scan_detects_private_key(tmp_path):
    header = "-----BEGIN " + "OPENSSH PRIVATE KEY" + "-----"
    f = tmp_path / "leak.txt"
    f.write_text(header + "\nabc\n")
    assert ss.scan_line(header)


def test_secret_scan_allows_placeholder(tmp_path):
    assert ss.scan_line('password = "<your-password-here>"') == []
    assert ss.scan_line('api_key = "${NVD_API_KEY}"') == []


def test_secret_scan_flags_real_looking_token():
    fake_pat = "glpat-" + "abcdef1234567890XYZ0"  # assembled so no PAT literal is in source
    assert ss.scan_line(f'gitlab_token = "{fake_pat}"')


def test_secret_scan_allows_env_var_and_calls():
    # shell / python env references and code expressions are not literal secrets
    assert ss.scan_line('--header "PRIVATE-TOKEN: $GITLAB_TOKEN"') == []
    assert ss.scan_line('pw = os.environ.get("WAZUH_API_PASSWORD")') == []
    assert ss.scan_line('token = authenticate(insecure)') == []


def test_secret_scan_pragma_allowlist():
    assert ss.scan_line('api_key = "AbCdEf0123456789xyz"  # pragma: allowlist secret') == []
