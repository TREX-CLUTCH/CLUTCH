#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from common import (
    ALLOWED_THRESHOLD_MINUTES,
    CONFIG_PATH,
    STATE_PATH,
    current_thread_id,
    get_session_pref,
    load_config,
    load_state,
    save_config,
    save_state,
    send_ntfy_notification,
    session_label,
    set_session_pref,
    suppress_next_task_complete,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CLUTCH Codex phone notification control.")
    parser.add_argument("--config-file", default=str(CONFIG_PATH))
    parser.add_argument("--state-file", default=str(STATE_PATH))
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("enable-session", "disable-session"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--thread-id", default="")
    mode_on = subparsers.add_parser("mode-on")
    mode_on.add_argument("--thread-id", default="")
    mode_off = subparsers.add_parser("mode-off")
    mode_off.add_argument("--thread-id", default="")
    mode_long = subparsers.add_parser("mode-long")
    mode_long.add_argument("--thread-id", default="")
    mode_long.add_argument("--minutes", type=int, choices=ALLOWED_THRESHOLD_MINUTES, required=True)

    subparsers.add_parser("status")
    test = subparsers.add_parser("send-test")
    test.add_argument("--thread-id", default="")
    test.add_argument("--message", default="")
    send_message = subparsers.add_parser("send-message")
    send_message.add_argument("--title", default="Main Codex notice")
    send_message.add_argument("--message", required=True)
    configure = subparsers.add_parser("configure")
    configure.add_argument("--enabled", action=argparse.BooleanOptionalAction, default=None)
    configure.add_argument("--topic", default=None)
    configure.add_argument("--server-url", default=None)
    configure.add_argument("--title", default=None)
    configure.add_argument("--machine-label", default=None)
    configure.add_argument("--message-template", default=None)
    configure.add_argument("--default-session-mode", choices=["off", "on", "long_only"], default=None)
    configure.add_argument("--default-session-threshold-minutes", type=int, choices=ALLOWED_THRESHOLD_MINUTES, default=0)
    configure.add_argument("--collab-completed-threshold-minutes", type=int, default=-1)
    return parser.parse_args()


def resolve_thread_id(explicit: str) -> str:
    thread_id = current_thread_id(explicit)
    if not thread_id:
        raise RuntimeError("No CODEX_THREAD_ID found; pass --thread-id explicitly.")
    return thread_id


def service_state() -> str:
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "clutch-notify.service"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "unknown"
    text = (result.stdout or result.stderr).strip()
    return text or "unknown"


def cmd_set_mode(args: argparse.Namespace, *, mode: str, threshold_minutes: int | None = None) -> int:
    state = load_state(Path(args.state_file))
    thread_id = resolve_thread_id(args.thread_id)
    set_session_pref(state, thread_id, mode=mode, threshold_minutes=threshold_minutes)
    save_state(state, Path(args.state_file))
    print(f"thread_id={thread_id}")
    print(f"session_notification_mode={mode}")
    if mode == "long_only":
        print(f"threshold_minutes={threshold_minutes}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config_file))
    state = load_state(Path(args.state_file))
    thread_id = current_thread_id()
    current_pref = get_session_pref(config, state, thread_id)
    topic = str(config.get("topic", "") or "")
    server_url = str(config.get("server_url", "") or "").rstrip("/")

    print(f"service_state={service_state()}")
    print(f"config_file={args.config_file}")
    print(f"state_file={args.state_file}")
    print(f"enabled={config.get('enabled', True)}")
    print(f"server_url={server_url}")
    print(f"topic={topic}")
    print(f"topic_url={server_url}/{topic}" if topic else "topic_url=")
    print(f"default_session_mode={config.get('default_session_mode', 'off')}")
    print(f"default_session_threshold_minutes={config.get('default_session_threshold_minutes', 10)}")
    print(f"collab_completed_threshold_minutes={config.get('collab_completed_threshold_minutes', 0)}")
    if thread_id:
        print(f"current_thread_id={thread_id}")
        print(f"current_session_mode={current_pref.get('mode')}")
        print(f"current_session_threshold_minutes={current_pref.get('threshold_minutes')}")
    else:
        print("current_thread_id=")
        print("current_session_mode=unknown")
        print("current_session_threshold_minutes=unknown")
    return 0


def cmd_send_test(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config_file))
    state = load_state(Path(args.state_file))
    thread_id = current_thread_id(args.thread_id)
    if thread_id:
        suppress_next_task_complete(state, thread_id)
        save_state(state, Path(args.state_file))
    label = session_label(os.getcwd(), thread_id)
    machine_label = str(config.get("machine_label", "CLUTCH"))
    message = args.message or f"{machine_label}의 {label} 세션 Codex가 작동 완료"
    status, _ = send_ntfy_notification(
        config,
        title=f"{machine_label} Codex test",
        message=message,
    )
    print(f"ntfy_status={status}")
    print(f"topic={config.get('topic', '')}")
    return 0


def cmd_send_message(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config_file))
    status, _ = send_ntfy_notification(
        config,
        title=args.title,
        message=args.message,
    )
    print(f"ntfy_status={status}")
    print(f"topic={config.get('topic', '')}")
    return 0


def cmd_configure(args: argparse.Namespace) -> int:
    config_path = Path(args.config_file)
    config = load_config(config_path)
    if args.enabled is not None:
        config["enabled"] = bool(args.enabled)
    if args.topic is not None:
        config["topic"] = str(args.topic).strip()
    if args.server_url is not None:
        config["server_url"] = str(args.server_url).strip() or "https://ntfy.sh"
    if args.title is not None:
        config["title"] = str(args.title).strip()
    if args.machine_label is not None:
        config["machine_label"] = str(args.machine_label).strip()
    if args.message_template is not None:
        config["message_template"] = str(args.message_template)
    if args.default_session_mode is not None:
        config["default_session_mode"] = args.default_session_mode
    if args.default_session_threshold_minutes:
        config["default_session_threshold_minutes"] = args.default_session_threshold_minutes
    if args.collab_completed_threshold_minutes >= 0:
        config["collab_completed_threshold_minutes"] = args.collab_completed_threshold_minutes
    save_config(config, config_path)
    print(f"config_file={config_path}")
    print(f"topic={config.get('topic', '')}")
    print(f"server_url={config.get('server_url', '')}")
    print(f"collab_completed_threshold_minutes={config.get('collab_completed_threshold_minutes', 0)}")
    return 0


def main() -> int:
    args = parse_args()
    command = args.command
    if command == "enable-session":
        return cmd_set_mode(args, mode="on")
    if command == "disable-session":
        return cmd_set_mode(args, mode="off")
    if command == "mode-on":
        return cmd_set_mode(args, mode="on")
    if command == "mode-off":
        return cmd_set_mode(args, mode="off")
    if command == "mode-long":
        return cmd_set_mode(args, mode="long_only", threshold_minutes=args.minutes)
    if command == "status":
        return cmd_status(args)
    if command == "send-test":
        return cmd_send_test(args)
    if command == "send-message":
        return cmd_send_message(args)
    if command == "configure":
        return cmd_configure(args)
    raise RuntimeError(f"Unknown command: {command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
