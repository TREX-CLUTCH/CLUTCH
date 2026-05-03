#!/usr/bin/env python3
"""Run the public CLUTCH verification path from one command.

This wrapper runs the private-data scanner, public release gate, read-only
visibility review, landing-page HTTP smoke, file-based collab transport smoke,
and optional install/first-project smoke for an exported CLUTCH public tree.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_json_output(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def run_step(name: str, command: list[str], *, cwd: Path) -> dict[str, Any]:
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
    ok = completed.returncode == 0 and payload_ok is not False
    return {
        "name": name,
        "ok": ok,
        "returncode": completed.returncode,
        "command": command,
        "payload": payload,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def verify(*, root: Path, skip_install_smoke: bool, keep_temp: bool) -> dict[str, Any]:
    root = root.expanduser().resolve()
    steps: list[dict[str, Any]] = []

    steps.append(
        run_step(
            "scanner",
            [sys.executable, str(root / "tools" / "clutch_distribution_scan.py"), str(root), "--json"],
            cwd=root,
        )
    )
    if steps[-1]["ok"]:
        steps.append(
            run_step(
                "release_gate",
                [sys.executable, str(root / "tools" / "clutch_public_release_gate.py"), "--root", str(root), "--json"],
                cwd=root,
            )
        )
    if steps[-1]["ok"]:
        steps.append(
            run_step(
                "visibility_review",
                [
                    sys.executable,
                    str(root / "tools" / "clutch_public_visibility_review.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                cwd=root,
            )
        )
    if steps[-1]["ok"]:
        steps.append(
            run_step(
                "landing_page_smoke",
                [sys.executable, str(root / "tools" / "clutch_public_landing_smoke.py"), "--root", str(root), "--json"],
                cwd=root,
            )
        )
    if steps[-1]["ok"]:
        command = [
            sys.executable,
            str(root / "tools" / "clutch_public_collab_smoke.py"),
            "--root",
            str(root),
            "--json",
        ]
        if keep_temp:
            command.append("--keep-temp")
        steps.append(run_step("collab_transport_smoke", command, cwd=root))
    if steps[-1]["ok"] and not skip_install_smoke:
        command = [
            sys.executable,
            str(root / "tools" / "clutch_public_install_smoke.py"),
            "--root",
            str(root),
            "--json",
        ]
        if keep_temp:
            command.append("--keep-temp")
        steps.append(run_step("install_first_project_smoke", command, cwd=root))

    ok = bool(steps) and all(step["ok"] for step in steps)
    return {
        "schema": "clutch.public_verify.v1",
        "ok": ok,
        "status": "passed" if ok else "failed",
        "root": str(root),
        "step_count": len(steps),
        "skip_install_smoke": bool(skip_install_smoke),
        "steps": steps,
        "next_actions": []
        if ok
        else ["inspect the failed step payload; rerun with --keep-temp if collab or install smoke failed"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root_from_script())
    parser.add_argument("--skip-install-smoke", action="store_true")
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = verify(root=args.root, skip_install_smoke=args.skip_install_smoke, keep_temp=args.keep_temp)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"clutch_public_verify status={payload['status']} steps={payload['step_count']}")
        for step in payload["steps"]:
            marker = "ok" if step["ok"] else "failed"
            print(f"[{marker}] {step['name']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
