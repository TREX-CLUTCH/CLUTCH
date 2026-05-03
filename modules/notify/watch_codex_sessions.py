#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from common import (
    CONFIG_PATH,
    STATE_PATH,
    build_task_complete_notification,
    consume_suppressed_task_complete,
    get_session_pref,
    load_config,
    load_state,
    save_state,
    send_ntfy_notification,
    session_label,
    should_notify_for_task_complete,
)


RUNNING = True


def request_stop(signum, frame) -> None:
    del signum, frame
    global RUNNING
    RUNNING = False


signal.signal(signal.SIGINT, request_stop)
signal.signal(signal.SIGTERM, request_stop)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch Codex session logs and send phone notifications on task completion.")
    parser.add_argument("--config-file", default=str(CONFIG_PATH))
    parser.add_argument("--state-file", default=str(STATE_PATH))
    parser.add_argument("--poll-sec", type=float, default=0.0)
    parser.add_argument("--idle-exit-sec", type=float, default=0.0)
    return parser.parse_args()


def discover_session_files(config: dict[str, Any]) -> list[Path]:
    files: set[Path] = set()
    for pattern in config.get("session_root_globs", []):
        for root in glob.glob(pattern):
            root_path = Path(root)
            if not root_path.exists():
                continue
            for file_path in root_path.rglob("*.jsonl"):
                files.add(file_path)
    return sorted(files)


def read_new_rows(path: Path, offset: int) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows, 0
    size = path.stat().st_size
    if size < offset:
        offset = 0
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        while True:
            line = handle.readline()
            if not line:
                break
            offset = handle.tell()
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows, offset


def bootstrap_session_meta(path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    if not path.exists():
        return meta
    try:
        with path.open("r", encoding="utf-8") as handle:
            for _ in range(40):
                line = handle.readline()
                if not line:
                    break
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue
                row_type = row.get("type")
                payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
                if row_type == "session_meta":
                    thread_id = payload.get("id")
                    cwd = payload.get("cwd")
                    if isinstance(thread_id, str) and thread_id:
                        meta["thread_id"] = thread_id
                    if isinstance(cwd, str) and cwd:
                        meta["cwd"] = cwd
                elif row_type == "turn_context":
                    cwd = payload.get("cwd")
                    if isinstance(cwd, str) and cwd:
                        meta["cwd"] = cwd
                if "thread_id" in meta and "cwd" in meta:
                    break
    except OSError:
        return meta
    return meta


def trim_notified(keys: list[str], limit: int) -> list[str]:
    if limit <= 0:
        return []
    if len(keys) <= limit:
        return keys
    return keys[-limit:]


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def lookup_turn_start_timestamp(path: Path, turn_id: str) -> str | None:
    if not turn_id or not path.exists():
        return None
    found: str | None = None
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict) or row.get("type") != "event_msg":
                    continue
                payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
                if payload.get("type") != "task_started":
                    continue
                if payload.get("turn_id") != turn_id:
                    continue
                stamp = row.get("timestamp")
                if isinstance(stamp, str) and stamp:
                    found = stamp
    except OSError:
        return None
    return found


def derive_duration_ms(
    *,
    path: Path,
    meta: dict[str, Any],
    turn_id: str,
    complete_timestamp: Any,
    payload_duration_ms: Any,
) -> int | None:
    try:
        if payload_duration_ms is not None:
            return int(payload_duration_ms)
    except (TypeError, ValueError):
        pass

    turn_starts = meta.setdefault("turn_start_timestamps", {})
    start_timestamp = turn_starts.get(turn_id)
    if not isinstance(start_timestamp, str) or not start_timestamp:
        start_timestamp = lookup_turn_start_timestamp(path, turn_id)
        if start_timestamp:
            turn_starts[turn_id] = start_timestamp

    start_dt = parse_timestamp(start_timestamp)
    end_dt = parse_timestamp(complete_timestamp)
    if start_dt is None or end_dt is None:
        return None
    return max(0, int((end_dt - start_dt).total_seconds() * 1000))


def process_rows(
    *,
    path: Path,
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    state: dict[str, Any],
) -> tuple[int, bool]:
    file_key = str(path)
    meta_store = state.setdefault("session_meta", {})
    meta = meta_store.get(file_key, {})
    notified = state.setdefault("notified_task_keys", [])
    notification_count = 0
    changed = False

    for row in rows:
        row_type = row.get("type")
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        if row_type == "session_meta":
            thread_id = payload.get("id")
            cwd = payload.get("cwd")
            if isinstance(thread_id, str) and thread_id:
                meta["thread_id"] = thread_id
                changed = True
            if isinstance(cwd, str) and cwd:
                meta["cwd"] = cwd
                changed = True
            continue

        if row_type == "turn_context":
            cwd = payload.get("cwd")
            if isinstance(cwd, str) and cwd:
                meta["cwd"] = cwd
                changed = True
            continue

        if row_type == "event_msg" and payload.get("type") == "task_started":
            turn_id = payload.get("turn_id")
            stamp = row.get("timestamp")
            if isinstance(turn_id, str) and turn_id and isinstance(stamp, str) and stamp:
                turn_starts = meta.setdefault("turn_start_timestamps", {})
                turn_starts[turn_id] = stamp
                if len(turn_starts) > 64:
                    for key in list(turn_starts)[:-64]:
                        del turn_starts[key]
                changed = True
            continue

        if row_type != "event_msg":
            continue
        if payload.get("type") != "task_complete":
            continue

        thread_id = meta.get("thread_id")
        turn_id = payload.get("turn_id")
        if not isinstance(thread_id, str) or not isinstance(turn_id, str):
            continue
        task_key = f"{thread_id}:{turn_id}"
        if task_key in notified:
            continue
        if consume_suppressed_task_complete(state, thread_id):
            changed = True
            continue
        if not should_notify_for_task_complete(
            config,
            state,
            thread_id=thread_id,
            duration_ms=derive_duration_ms(
                path=path,
                meta=meta,
                turn_id=turn_id,
                complete_timestamp=row.get("timestamp"),
                payload_duration_ms=payload.get("duration_ms"),
            ),
        ):
            continue

        cwd = meta.get("cwd")
        label = session_label(cwd if isinstance(cwd, str) else None, thread_id)
        title, message = build_task_complete_notification(
            config,
            session_name=label,
            cwd=cwd if isinstance(cwd, str) else None,
            duration_ms=derive_duration_ms(
                path=path,
                meta=meta,
                turn_id=turn_id,
                complete_timestamp=row.get("timestamp"),
                payload_duration_ms=payload.get("duration_ms"),
            ),
            last_agent_message=payload.get("last_agent_message"),
        )
        try:
            send_ntfy_notification(config, title=title, message=message)
        except RuntimeError as exc:
            print(f"codex-notify send failed for {task_key}: {exc}", file=sys.stderr)
            continue
        notified.append(task_key)
        state["notified_task_keys"] = trim_notified(notified, int(config.get("dedupe_limit", 256)))
        notification_count += 1
        changed = True

    if changed:
        meta_store[file_key] = meta
    return notification_count, changed


def main() -> int:
    args = parse_args()
    config_path = Path(args.config_file)
    state_path = Path(args.state_file)
    idle_start = time.time()

    while RUNNING:
        config = load_config(config_path)
        state = load_state(state_path)
        changed = False
        notifications_sent = 0
        poll_sec = args.poll_sec if args.poll_sec > 0.0 else float(config.get("poll_seconds", 2.0))

        for path in discover_session_files(config):
            file_offsets = state.setdefault("file_offsets", {})
            file_key = str(path)
            if file_key not in file_offsets:
                file_offsets[file_key] = path.stat().st_size if path.exists() else 0
                boot_meta = bootstrap_session_meta(path)
                if boot_meta:
                    session_meta = state.setdefault("session_meta", {})
                    merged = session_meta.get(file_key, {})
                    merged.update(boot_meta)
                    session_meta[file_key] = merged
                changed = True
                continue
            offset = int(file_offsets.get(str(path), 0))
            rows, new_offset = read_new_rows(path, offset)
            if new_offset != offset:
                file_offsets[str(path)] = new_offset
                changed = True
            if not rows:
                continue
            count, rows_changed = process_rows(path=path, rows=rows, config=config, state=state)
            notifications_sent += count
            changed = changed or rows_changed

        if changed:
            save_state(state, state_path)
            idle_start = time.time()
        elif notifications_sent:
            idle_start = time.time()

        if args.idle_exit_sec > 0.0 and (time.time() - idle_start) >= args.idle_exit_sec:
            return 0

        time.sleep(max(poll_sec, 0.2))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
