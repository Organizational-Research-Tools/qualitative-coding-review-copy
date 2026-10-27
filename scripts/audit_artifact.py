#!/usr/bin/env python3
"""Check the exact local artifact allowlist and common accidental disclosures.

This heuristic audit supplements manual review; it does not clear publication
rights. It reports filenames and categories, never matching secret contents.
"""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from interpretive_map.contracts import load_bundle


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def audit():
    allowlist = (ROOT / "allowlist.txt").read_text().splitlines()
    if len(allowlist) != len(set(allowlist)):
        raise ValueError("Duplicate allowlist entries")
    allowed = set(allowlist)
    tracked = set(git("ls-files").splitlines())
    candidates = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    inventory = tracked | candidates
    problems = []
    if inventory != allowed:
        problems.append({"inventory_mismatch": {"unexpected": sorted(inventory - allowed), "missing": sorted(allowed - inventory)}})
    permitted_remote = re.compile(r"^(?:https://github\.com/|git@github\.com:)[A-Za-z0-9-]+/[A-Za-z0-9._-]+?(?:\.git)?$")
    for remote in git("remote").splitlines():
        for direction in ([], ["--push"]):
            urls = git("remote", "get-url", *direction, "--all", remote).splitlines()
            if not urls or any(not permitted_remote.match(url) for url in urls):
                problems.append({"remote": remote, "reason": "Remote is not a GitHub repository"})
    patterns = {
        "absolute_personal_path": re.compile(r"/(?:Users|Volumes|home)/[^\s\"']+"),
        "provider_key_shape": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
        "aws_access_key_shape": re.compile(r"AKIA[A-Z0-9]{16}"),
        "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "credential_url": re.compile(r"https?://[^\s/:]+:[^\s/@]+@"),
        "email_address": re.compile(r"[A-Za-z0-9._%+-]+@(?!example\.invalid\b)[A-Za-z0-9-]+\.[A-Za-z0-9.-]*[A-Za-z]"),
    }
    forbidden = re.compile(r"(?:\.env|cookie|credential|secret|\.db(?:-|$)|\.sqlite|\.pdf$|\.docx$|\.xlsx$|\.parquet$)", re.I)
    total_bytes = 0
    for name in sorted(inventory):
        path = ROOT / name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
            problems.append({"file": name, "reason": "symlink or escaped path"})
            continue
        if forbidden.search(name):
            problems.append({"file": name, "reason": "restricted filename"})
        content = path.read_bytes()
        total_bytes += len(content)
        if len(content) > (3_000_000 if name.startswith("data/empirical/") else 250_000):
            problems.append({"file": name, "reason": "unexpected bulk file"})
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            problems.append({"file": name, "reason": "non-text file"})
            continue
        for label, pattern in patterns.items():
            if pattern.search(text):
                problems.append({"file": name, "reason": label})
    load_bundle(ROOT)
    report = {"status": "PASS" if not problems else "FAIL", "allowed_files": len(allowed),
              "tracked_files": len(tracked), "untracked_allowlisted_files": len(candidates),
              "bytes_reviewed": total_bytes, "frozen_synthetic_fixture_valid": True, "problems": problems,
              "scope": "Exact file allowlist, UTF-8/size checks, frozen synthetic provenance, common secrets, email addresses and personal paths, GitHub-only remotes. Not a licensing clearance."}
    print(json.dumps(report, indent=2))
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(audit())
