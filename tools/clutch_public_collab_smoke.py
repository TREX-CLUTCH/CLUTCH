#!/usr/bin/env python3
"""Run a local public smoke test for the file-based CLUTCH collab transport."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA = "clutch.public_collab_smoke.v1"
STATUS_SCHEMA = "clutch.public_collab.status.v1"
PROJECT_ID = "public-collab-smoke"
MAIN_MACHINE = "public-main"
WORKER_MACHINE = "public-worker"
REQUEST_ID = "req-public-smoke"
EXPECTED_EVENTS = ("machine_init", "request_opened", "request_result")


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_json_output(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def run_transport_step(name: str, command: list[str], *, cwd: Path) -> dict[str, Any]:
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
    ok = completed.returncode == 0 and payload_ok is not False and payload is not None
    return {
        "name": name,
        "ok": ok,
        "returncode": completed.returncode,
        "command": command,
        "payload": payload,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def transport_command(root: Path, shared_root: Path, action: str, extra: list[str]) -> list[str]:
    return [
        sys.executable,
        str(root / "collab_transport" / "scripts" / "clutch_collab_file_transport.py"),
        action,
        "--shared-root",
        str(shared_root),
        "--project-id",
        PROJECT_ID,
        *extra,
    ]


def validate_status(status_payload: dict[str, Any] | None) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not status_payload:
        return False, ["status command did not return JSON"]
    if status_payload.get("schema") != STATUS_SCHEMA:
        failures.append("status schema mismatch")
    if status_payload.get("ok") is not True:
        failures.append("status ok flag is not true")
    if status_payload.get("machine_count") != 2:
        failures.append("expected two machines")
    if status_payload.get("open_request_count") != 0:
        failures.append("expected no open requests after worker result")

    machine_ids = {str(item.get("machine_id")) for item in status_payload.get("machines", [])}
    if {MAIN_MACHINE, WORKER_MACHINE} - machine_ids:
        failures.append("main and worker machine states are not both present")

    requests = status_payload.get("requests", [])
    request = next((item for item in requests if item.get("request_id") == REQUEST_ID), None)
    if not request:
        failures.append("request record is missing")
    elif request.get("status") != "completed":
        failures.append("request did not move to completed")

    results = status_payload.get("results", [])
    result = next((item for item in results if item.get("request_id") == REQUEST_ID), None)
    if not result:
        failures.append("result record is missing")
    elif result.get("status") != "completed":
        failures.append("result status is not completed")

    recent_events = status_payload.get("recent_events", [])
    event_names = {str(item.get("event")) for item in recent_events}
    missing_events = [event for event in EXPECTED_EVENTS if event not in event_names]
    if missing_events:
        failures.append(f"missing recent events: {', '.join(missing_events)}")

    return not failures, failures


def run_smoke(*, root: Path, keep_temp: bool) -> dict[str, Any]:
    root = root.expanduser().resolve()
    temp_root = Path(tempfile.mkdtemp(prefix="clutch-public-collab-smoke."))
    shared_root = temp_root / "shared"
    steps: list[dict[str, Any]] = []
    status_payload: dict[str, Any] | None = None
    validation_failures: list[str] = []
    temp_preserved = bool(keep_temp)

    try:
        steps.append(
            run_transport_step(
                "main_init",
                transport_command(
                    root,
                    shared_root,
                    "init",
                    [
                        "--machine-id",
                        MAIN_MACHINE,
                        "--display-name",
                        "Public Main",
                        "--role",
                        "main",
                    ],
                ),
                cwd=root,
            )
        )
        if steps[-1]["ok"]:
            steps.append(
                run_transport_step(
                    "worker_init",
                    transport_command(
                        root,
                        shared_root,
                        "init",
                        [
                            "--machine-id",
                            WORKER_MACHINE,
                            "--display-name",
                            "Public Worker",
                            "--role",
                            "worker",
                        ],
                    ),
                    cwd=root,
                )
            )
        if steps[-1]["ok"]:
            steps.append(
                run_transport_step(
                    "main_request",
                    transport_command(
                        root,
                        shared_root,
                        "request",
                        [
                            "--from-machine",
                            MAIN_MACHINE,
                            "--to-machine",
                            WORKER_MACHINE,
                            "--kind",
                            "inspect",
                            "--summary",
                            "Check public collab transport",
                            "--body",
                            "Confirm request and result evidence are visible to the monitor.",
                            "--request-id",
                            REQUEST_ID,
                        ],
                    ),
                    cwd=root,
                )
            )
        if steps[-1]["ok"]:
            steps.append(
                run_transport_step(
                    "worker_result",
                    transport_command(
                        root,
                        shared_root,
                        "result",
                        [
                            "--request-id",
                            REQUEST_ID,
                            "--from-machine",
                            WORKER_MACHINE,
                            "--status",
                            "completed",
                            "--summary",
                            "Collab transport smoke completed",
                            "--body",
                            "The public file transport recorded machine state, request, result, and events.",
                        ],
                    ),
                    cwd=root,
                )
            )
        if steps[-1]["ok"]:
            steps.append(
                run_transport_step(
                    "status_monitor",
                    transport_command(root, shared_root, "status", ["--recent-limit", "20", "--json"]),
                    cwd=root,
                )
            )
            status_payload = steps[-1]["payload"]
            status_ok, validation_failures = validate_status(status_payload)
            if not status_ok:
                steps[-1]["ok"] = False

        recent_event_names = {
            str(item.get("event"))
            for item in (status_payload or {}).get("recent_events", [])
            if isinstance(item, dict)
        }
        missing_event_types = [event for event in EXPECTED_EVENTS if event not in recent_event_names]
        ok = bool(steps) and all(step["ok"] for step in steps) and not validation_failures
        return {
            "schema": SCHEMA,
            "ok": ok,
            "status": "passed" if ok else "failed",
            "root": str(root),
            "temp_root": str(temp_root),
            "temp_preserved": temp_preserved,
            "shared_root": str(shared_root),
            "project_id": PROJECT_ID,
            "machines": [MAIN_MACHINE, WORKER_MACHINE],
            "request_id": REQUEST_ID,
            "step_count": len(steps),
            "steps": steps,
            "status_payload": status_payload,
            "expected_event_types": list(EXPECTED_EVENTS),
            "missing_event_types": missing_event_types,
            "validation_failures": validation_failures,
            "next_actions": []
            if ok
            else [
                "inspect the failed step payload",
                "rerun with --keep-temp to inspect the generated shared collab folder",
            ],
        }
    finally:
        if not keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root_from_script())
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_smoke(root=args.root, keep_temp=args.keep_temp)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"clutch_public_collab_smoke status={payload['status']} steps={payload['step_count']}")
        for step in payload["steps"]:
            marker = "ok" if step["ok"] else "failed"
            print(f"[{marker}] {step['name']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
