#!/usr/bin/env python3
"""Read-only final visibility review for a CLUTCH public staging tree.

This tool never changes GitHub repository visibility and never uploads release
artifacts. It records whether the exported tree has enough scanner, release
gate, and documentation evidence for a human operator to perform the final
public visibility review.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "README.md",
    "SECURITY.md",
    "Makefile",
    ".github/workflows/public-ci.yml",
    ".github/pull_request_template.md",
    "docs/github-publication.md",
    "docs/privacy-and-redaction.md",
    "docs/public-release-checklist.md",
    "docs/release-artifacts.md",
    "docs/release-notes-template.md",
    "docs/public-demo-script.md",
    "tools/clutch_distribution_scan.py",
    "tools/clutch_public_release_gate.py",
    "tools/clutch_public_verify.py",
    "tools/clutch_public_visibility_review.py",
)

REQUIRED_TEXT = {
    "README.md": (
        "Trust And Verification",
        "https://trex-clutch.github.io/CLUTCH/",
        "make verify",
        "make web-smoke",
    ),
    "SECURITY.md": (
        "operator explicitly approves",
        "repository visibility change",
        "Privacy And Redaction",
    ),
    "Makefile": (
        "make visibility-review",
        "clutch_public_visibility_review.py",
    ),
    ".github/workflows/public-ci.yml": (
        "clutch_public_visibility_review.py",
        "make verify",
    ),
    ".github/pull_request_template.md": (
        "clutch_public_visibility_review.py",
        "explicit operator approval",
    ),
    "docs/github-publication.md": (
        "Visibility Change",
        "explicit operator approval",
        "make visibility-review",
        "tools/clutch_public_visibility_review.py --root . --json",
    ),
    "docs/privacy-and-redaction.md": (
        "Private Machine Identity",
        "private denylist",
        "tools/clutch_public_visibility_review.py --root . --json",
        "explicit operator approval",
    ),
    "docs/public-release-checklist.md": (
        "Final Visibility Gate",
        "ready_for_manual_visibility_review",
        "tools/clutch_public_visibility_review.py --root . --json",
        "remote_visibility_change_performed",
        "manual operator action",
    ),
    "docs/release-artifacts.md": (
        "ready_for_private_release_upload",
        "explicit operator approval",
    ),
    "docs/release-notes-template.md": (
        "visibility review",
        "ready_for_manual_visibility_review",
        "explicit operator approval",
    ),
    "docs/public-demo-script.md": (
        "explicit operator approval",
        "repository visibility change",
    ),
    "tools/clutch_public_verify.py": (
        "visibility_review",
        "clutch_public_visibility_review.py",
    ),
}

MANUAL_REVIEW_ITEMS = (
    "Confirm the private staging repository is still private.",
    "Review scanner JSON and private denylist scanner output.",
    "Review the public release gate JSON.",
    "Review release zip, checksum, manifest, and generated release notes.",
    "Review landing page first screen and GitHub repository first screen.",
    "Confirm no private machine ids, hostnames, paths, IPs, SSH aliases, tokens, or hardware profiles remain.",
    "Obtain explicit operator approval before changing repository visibility.",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_json_output(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def run_json_step(name: str, command: list[str], *, cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload = parse_json_output(completed.stdout)
    payload_ok = payload.get("ok") if payload else None
    return {
        "name": name,
        "ok": completed.returncode == 0 and payload is not None and payload_ok is not False,
        "returncode": completed.returncode,
        "command": command,
        "payload": payload,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def compact_step(step: dict[str, Any]) -> dict[str, Any]:
    payload = step.get("payload") or {}
    compact_payload: dict[str, Any] = {}
    for key in ("schema", "ok", "status", "finding_count", "scanner_finding_count"):
        if key in payload:
            compact_payload[key] = payload[key]
    return {
        "name": step["name"],
        "ok": step["ok"],
        "returncode": step["returncode"],
        "payload": compact_payload,
    }


def required_text_findings(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if not path.exists():
            findings.append(
                {
                    "kind": "visibility_review_required_file_missing",
                    "path": relative_path,
                    "message": f"required final visibility review file is missing: {relative_path}",
                }
            )

    for relative_path, required_terms in REQUIRED_TEXT.items():
        path = root / relative_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for term in required_terms:
            if term not in text:
                findings.append(
                    {
                        "kind": "visibility_review_required_text_missing",
                        "path": relative_path,
                        "message": f"required final visibility review text missing from {relative_path}: {term}",
                    }
                )
    return findings


def review(*, root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    steps: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    scanner = run_json_step(
        "scanner",
        [sys.executable, str(root / "tools" / "clutch_distribution_scan.py"), str(root), "--json"],
        cwd=root,
    )
    steps.append(scanner)
    if not scanner["ok"]:
        findings.append(
            {
                "kind": "visibility_review_scanner_failed",
                "path": ".",
                "message": "scanner did not pass; keep the repository private",
            }
        )

    release_gate = run_json_step(
        "release_gate",
        [sys.executable, str(root / "tools" / "clutch_public_release_gate.py"), "--root", str(root), "--json"],
        cwd=root,
    )
    steps.append(release_gate)
    if not release_gate["ok"]:
        findings.append(
            {
                "kind": "visibility_review_release_gate_failed",
                "path": ".",
                "message": "public release gate did not pass; keep the repository private",
            }
        )

    findings.extend(required_text_findings(root))
    ok = not findings

    return {
        "schema": "clutch.public_visibility_review.v1",
        "ok": ok,
        "status": "ready_for_manual_visibility_review" if ok else "failed",
        "root": str(root),
        "remote_visibility_change_performed": False,
        "remote_upload_performed": False,
        "public_visibility_requires_operator_approval": True,
        "steps": [compact_step(step) for step in steps],
        "manual_review_items": list(MANUAL_REVIEW_ITEMS),
        "findings": findings,
        "finding_count": len(findings),
        "next_actions": [
            "Keep the staging repository private until the operator explicitly approves public visibility.",
            "Attach this JSON with scanner, release gate, smoke, package, and release-note evidence.",
        ]
        if ok
        else ["fix the listed findings and rerun this read-only visibility review"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root_from_script())
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = review(root=args.root)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"clutch_public_visibility_review status={payload['status']} findings={payload['finding_count']}")
        print("remote_visibility_change_performed=false")
        print("public_visibility_requires_operator_approval=true")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
