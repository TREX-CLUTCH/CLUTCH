#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any


SCHEMA_EVENT = "clutch.public_collab.event.v1"
SCHEMA_STATE = "clutch.public_collab.machine_state.v1"
SCHEMA_REQUEST = "clutch.public_collab.request.v1"
SCHEMA_RESULT = "clutch.public_collab.result.v1"
SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,80}$")


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def require_id(value: str, label: str) -> str:
    if not SAFE_ID.match(value):
        raise ValueError(f"{label} must be a short id using letters, numbers, dot, dash, or underscore")
    return value


def project_root(shared_root: Path, project_id: str) -> Path:
    return shared_root.expanduser().resolve() / "projects" / require_id(project_id, "project id")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def event_path(root: Path) -> Path:
    return root / "events.jsonl"


def machine_state_path(root: Path, machine_id: str) -> Path:
    return root / "machines" / require_id(machine_id, "machine id") / "state.json"


def emit_event(root: Path, payload: dict[str, Any]) -> None:
    event = {
        "schema": SCHEMA_EVENT,
        "created_at": now_iso(),
        **payload,
    }
    append_jsonl(event_path(root), event)


def command_init(args: argparse.Namespace) -> int:
    root = project_root(Path(args.shared_root), args.project_id)
    machine_id = require_id(args.machine_id, "machine id")
    state = {
        "schema": SCHEMA_STATE,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "project_id": args.project_id,
        "machine_id": machine_id,
        "display_name": args.display_name or machine_id,
        "role": args.role,
        "status": "online",
        "notes": [],
    }
    atomic_write_json(machine_state_path(root, machine_id), state)
    emit_event(root, {"event": "machine_init", "machine_id": machine_id, "role": args.role})
    print(json.dumps({"ok": True, "project_root": str(root), "machine_id": machine_id}, indent=2, sort_keys=True))
    return 0


def command_note(args: argparse.Namespace) -> int:
    root = project_root(Path(args.shared_root), args.project_id)
    from_machine = require_id(args.from_machine, "from machine")
    to_machine = require_id(args.to_machine, "to machine") if args.to_machine else ""
    emit_event(
        root,
        {
            "event": "note",
            "from_machine": from_machine,
            "to_machine": to_machine,
            "message": args.message,
        },
    )
    print(json.dumps({"ok": True, "event": "note"}, indent=2, sort_keys=True))
    return 0


def command_request(args: argparse.Namespace) -> int:
    root = project_root(Path(args.shared_root), args.project_id)
    request_id = args.request_id or f"req-{uuid.uuid4().hex[:12]}"
    payload = {
        "schema": SCHEMA_REQUEST,
        "created_at": now_iso(),
        "project_id": args.project_id,
        "request_id": require_id(request_id, "request id"),
        "from_machine": require_id(args.from_machine, "from machine"),
        "to_machine": require_id(args.to_machine, "to machine"),
        "kind": args.kind,
        "summary": args.summary,
        "body": args.body,
        "status": "open",
    }
    atomic_write_json(root / "requests" / f"{payload['request_id']}.json", payload)
    emit_event(
        root,
        {
            "event": "request_opened",
            "request_id": payload["request_id"],
            "from_machine": payload["from_machine"],
            "to_machine": payload["to_machine"],
            "kind": args.kind,
            "summary": args.summary,
        },
    )
    print(json.dumps({"ok": True, "request_id": payload["request_id"]}, indent=2, sort_keys=True))
    return 0


def command_result(args: argparse.Namespace) -> int:
    root = project_root(Path(args.shared_root), args.project_id)
    request_id = require_id(args.request_id, "request id")
    payload = {
        "schema": SCHEMA_RESULT,
        "created_at": now_iso(),
        "project_id": args.project_id,
        "request_id": request_id,
        "from_machine": require_id(args.from_machine, "from machine"),
        "status": args.status,
        "summary": args.summary,
        "body": args.body,
    }
    atomic_write_json(root / "results" / f"{request_id}.json", payload)
    request_path = root / "requests" / f"{request_id}.json"
    request = load_json(request_path)
    if request:
        request["status"] = args.status
        request["result_created_at"] = payload["created_at"]
        atomic_write_json(request_path, request)
    emit_event(
        root,
        {
            "event": "request_result",
            "request_id": request_id,
            "from_machine": payload["from_machine"],
            "status": args.status,
            "summary": args.summary,
        },
    )
    print(json.dumps({"ok": True, "request_id": request_id, "status": args.status}, indent=2, sort_keys=True))
    return 0


def read_recent_events(root: Path, limit: int) -> list[dict[str, Any]]:
    path = event_path(root)
    if not path.exists():
        return []
    rows: deque[dict[str, Any]] = deque(maxlen=max(limit, 1))
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return list(rows)


def gather_status(shared_root: Path, project_id: str, recent_limit: int) -> dict[str, Any]:
    root = project_root(shared_root, project_id)
    machines = sorted(
        [payload for payload in (load_json(path) for path in root.glob("machines/*/state.json")) if payload],
        key=lambda item: str(item.get("machine_id", "")),
    )
    requests = sorted(
        [payload for payload in (load_json(path) for path in root.glob("requests/*.json")) if payload],
        key=lambda item: str(item.get("created_at", "")),
    )
    results = sorted(
        [payload for payload in (load_json(path) for path in root.glob("results/*.json")) if payload],
        key=lambda item: str(item.get("created_at", "")),
    )
    return {
        "schema": "clutch.public_collab.status.v1",
        "ok": True,
        "project_id": project_id,
        "project_root": str(root),
        "machine_count": len(machines),
        "open_request_count": len([item for item in requests if item.get("status") == "open"]),
        "machines": machines,
        "requests": requests,
        "results": results,
        "recent_events": read_recent_events(root, recent_limit),
    }


def render_status(payload: dict[str, Any]) -> str:
    lines = [
        f"CLUTCH collab monitor: {payload['project_id']}",
        f"root: {payload['project_root']}",
        "",
        "Machines",
    ]
    for machine in payload["machines"]:
        lines.append(
            f"- {machine.get('machine_id')}: role={machine.get('role')} status={machine.get('status')} "
            f"updated={machine.get('updated_at')}"
        )
    if not payload["machines"]:
        lines.append("- none")
    lines.extend(["", "Requests"])
    for request in payload["requests"][-8:]:
        lines.append(
            f"- {request.get('request_id')} {request.get('kind')} {request.get('status')} "
            f"{request.get('from_machine')} -> {request.get('to_machine')}: {request.get('summary')}"
        )
    if not payload["requests"]:
        lines.append("- none")
    lines.extend(["", "Recent Events"])
    for event in payload["recent_events"][-8:]:
        lines.append(f"- {event.get('created_at')} {event.get('event')} {event.get('summary') or event.get('message') or ''}")
    if not payload["recent_events"]:
        lines.append("- none")
    return "\n".join(lines)


def command_status(args: argparse.Namespace) -> int:
    payload = gather_status(Path(args.shared_root), args.project_id, args.recent_limit)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_status(payload))
    return 0


def command_monitor(args: argparse.Namespace) -> int:
    while True:
        payload = gather_status(Path(args.shared_root), args.project_id, args.recent_limit)
        print("\033[2J\033[H", end="")
        print(render_status(payload), flush=True)
        if args.once:
            return 0
        time.sleep(max(float(args.refresh_sec), 0.5))


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--shared-root", required=True)
    parser.add_argument("--project-id", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe file-based CLUTCH public collab transport helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Register this machine in a shared collab folder.")
    add_common(init)
    init.add_argument("--machine-id", required=True)
    init.add_argument("--display-name", default="")
    init.add_argument("--role", choices=["main", "worker", "observer"], required=True)
    init.set_defaults(func=command_init)

    note = subparsers.add_parser("note", help="Append a note for another machine or for the project timeline.")
    add_common(note)
    note.add_argument("--from-machine", required=True)
    note.add_argument("--to-machine", default="")
    note.add_argument("--message", required=True)
    note.set_defaults(func=command_note)

    request = subparsers.add_parser("request", help="Create a task or question for another machine.")
    add_common(request)
    request.add_argument("--from-machine", required=True)
    request.add_argument("--to-machine", required=True)
    request.add_argument("--kind", choices=["question", "inspect", "edit", "task"], default="task")
    request.add_argument("--summary", required=True)
    request.add_argument("--body", required=True)
    request.add_argument("--request-id", default="")
    request.set_defaults(func=command_request)

    result = subparsers.add_parser("result", help="Record a result for an existing request.")
    add_common(result)
    result.add_argument("--request-id", required=True)
    result.add_argument("--from-machine", required=True)
    result.add_argument("--status", choices=["completed", "blocked", "failed", "cancelled"], required=True)
    result.add_argument("--summary", required=True)
    result.add_argument("--body", required=True)
    result.set_defaults(func=command_result)

    status = subparsers.add_parser("status", help="Print collab state once.")
    add_common(status)
    status.add_argument("--recent-limit", type=int, default=20)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_status)

    monitor = subparsers.add_parser("monitor", help="Render a simple terminal monitor.")
    add_common(monitor)
    monitor.add_argument("--recent-limit", type=int, default=20)
    monitor.add_argument("--refresh-sec", type=float, default=2.0)
    monitor.add_argument("--once", action="store_true")
    monitor.set_defaults(func=command_monitor)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
