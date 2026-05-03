#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path
from typing import Any


TOKEN_HASH_SCHEME = "pbkdf2_sha256"
TOKEN_HASH_ITERATIONS = 260_000


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "clutch-machine"


def expand_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def hash_token(value: str, *, salt: bytes | None = None, iterations: int = TOKEN_HASH_ITERATIONS) -> str:
    salt_bytes = salt if salt is not None else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt_bytes, max(int(iterations), 1))
    return "$".join(
        [
            TOKEN_HASH_SCHEME,
            str(max(int(iterations), 1)),
            base64.b64encode(salt_bytes).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        ]
    )


def verify_token(value: str, stored_hash: str) -> bool:
    stored = str(stored_hash or "")
    if not stored.startswith(f"{TOKEN_HASH_SCHEME}$"):
        return False
    try:
        _scheme, iterations_text, salt_text, digest_text = stored.split("$", 3)
        iterations = int(iterations_text)
        salt = base64.b64decode(salt_text.encode("ascii"), validate=True)
        expected = base64.b64decode(digest_text.encode("ascii"), validate=True)
    except (TypeError, ValueError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt, max(iterations, 1))
    return hmac.compare_digest(actual, expected)


def generated_machine_id(display_name: str) -> str:
    return f"{slugify(display_name)}-{secrets.token_hex(4)}"


def generated_pairing_code() -> str:
    return "-".join(secrets.token_hex(2) for _ in range(3))


def prompt_text(label: str, default: str) -> str:
    print(f"{label} [{default}]: ", end="", file=sys.stderr, flush=True)
    answer = input().strip()
    return answer or default


def prompt_choice(label: str, choices: list[str], default: str) -> str:
    choice_text = "/".join(choices)
    while True:
        print(f"{label} ({choice_text}) [{default}]: ", end="", file=sys.stderr, flush=True)
        answer = input().strip() or default
        if answer in choices:
            return answer
        print(f"Choose one of: {choice_text}", file=sys.stderr)


def prompt_bool(label: str, default: bool) -> bool:
    default_text = "y" if default else "n"
    while True:
        print(f"{label} (y/n) [{default_text}]: ", end="", file=sys.stderr, flush=True)
        answer = input().strip().lower() or default_text
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Choose y or n.", file=sys.stderr)


def prompt_int(label: str, default: int) -> int:
    while True:
        print(f"{label} [{default}]: ", end="", file=sys.stderr, flush=True)
        answer = input().strip() or str(default)
        try:
            return int(answer)
        except ValueError:
            print("Choose a whole number.", file=sys.stderr)


def resolve_admin_token(*, token_stdin: bool, non_interactive: bool) -> str:
    if token_stdin:
        token = sys.stdin.readline().rstrip("\n")
    elif non_interactive:
        raise ValueError("--non-interactive requires --admin-token-stdin")
    else:
        token = getpass("CLUTCH admin token: ")
    if not token:
        raise ValueError("admin token must not be empty")
    return token


def collect_config(args: argparse.Namespace) -> dict[str, Any]:
    home_default = str(Path(os.environ.get("CLUTCH_HOME") or (Path.home() / ".clutch")))
    clutch_home = str(args.clutch_home or home_default)
    projects_root = str(args.projects_root or str(Path.home() / "clutch-projects"))
    artifact_store = str(args.artifact_store or str(Path.home() / "clutch-artifacts"))
    display_name = str(args.machine_display_name or "My CLUTCH Workstation")
    session_default = str(args.session_attach_default or "prompt")
    sync_mode = str(args.online_sync_mode or "off")
    github_setup = str(args.github_setup or "skip")
    enable_collab = bool(args.enable_collab)
    machine_id = str(args.machine_id or "")
    pairing_code = str(args.pairing_code or "")
    web_console_auto_start = bool(args.web_console_auto_start)
    web_console_auto_open = str(args.web_console_auto_open or "safe")
    web_console_host = str(args.web_console_host or "127.0.0.1")
    web_console_port = int(args.web_console_port or 8765)

    if not args.non_interactive:
        clutch_home = prompt_text("CLUTCH home directory", clutch_home)
        projects_root = prompt_text("Project workspace root directory", projects_root)
        artifact_store = prompt_text("Local artifact store directory", artifact_store)
        display_name = prompt_text("Machine display name", display_name)
        machine_id = prompt_text("Machine id (leave auto value unless you know you need a stable id)", machine_id or generated_machine_id(display_name))
        session_default = prompt_choice("Session attach default", ["prompt", "manual", "auto"], session_default)
        sync_mode = prompt_choice("Online sync mode", ["off", "best_effort", "required"], sync_mode)
        github_setup = prompt_choice("GitHub setup", ["skip", "existing_git", "gh_auth"], github_setup)
        enable_collab = prompt_bool("Enable multi-PC collaboration setup guide now", enable_collab)
        web_console_auto_start = prompt_bool("Start the local Web console from session-entry", web_console_auto_start)
        web_console_auto_open = prompt_choice("Browser open mode for the Web console", ["safe", "never", "always"], web_console_auto_open)
        web_console_host = prompt_text("Web console host", web_console_host)
        web_console_port = prompt_int("Web console port", web_console_port)
        if enable_collab:
            pairing_code = prompt_text("Collab pairing code", pairing_code or generated_pairing_code())

    if not machine_id:
        machine_id = generated_machine_id(display_name)
    if enable_collab and not pairing_code:
        pairing_code = generated_pairing_code()

    return {
        "clutch_home": expand_path(clutch_home),
        "projects_root": expand_path(projects_root),
        "artifact_store": expand_path(artifact_store),
        "display_name": display_name,
        "machine_id": slugify(machine_id),
        "session_attach_default": session_default,
        "online_sync_mode": sync_mode,
        "github_setup": github_setup,
        "enable_collab": enable_collab,
        "pairing_code": pairing_code,
        "web_console_auto_start": web_console_auto_start,
        "web_console_auto_open": web_console_auto_open,
        "web_console_host": web_console_host,
        "web_console_port": web_console_port,
    }


def build_install_plan(config: dict[str, Any], admin_token: str) -> dict[str, Any]:
    clutch_home = Path(config["clutch_home"])
    projects_root = Path(config["projects_root"])
    artifact_store = Path(config["artifact_store"])
    machine_id = str(config["machine_id"])
    now = datetime.now(timezone.utc).isoformat()

    machine_settings = {
        "schema": "clutch.public_machine_settings.v1",
        "created_at": now,
        "session_attach_default": config["session_attach_default"],
        "session_attach_default_configured": True,
        "sync_on_session_entry": config["online_sync_mode"] != "off",
        "sync_policy": config["online_sync_mode"],
        "local_customization": {
            "projects_root": str(clutch_home / "local" / "projects"),
            "workspace_projects_root": str(projects_root),
            "artifact_store": str(artifact_store),
        },
        "online_git": {
            "mode": config["online_sync_mode"],
            "github_setup": config["github_setup"],
            "foundation": {"remote_url": "", "branch": "main"},
            "ops": {"remote_url": "", "branch": "main"},
            "collab_transport": {"remote_url": "", "branch": "main"},
        },
        "collab": {
            "enabled": bool(config["enable_collab"]),
            "setup_status": "pairing_required" if config["enable_collab"] else "disabled",
            "peer_addresses_configured": False,
        },
        "web_console": {
            "auto_start_on_session_entry": bool(config["web_console_auto_start"]),
            "auto_open_browser_on_session_entry": str(config["web_console_auto_open"]),
            "host": str(config["web_console_host"]),
            "port": int(config["web_console_port"]),
        },
    }
    machine_profile = {
        "schema": "clutch.local_machine_profile.v1",
        "created_at": now,
        "created_by": "clutch_public_first_run_wizard",
        "machine_id": machine_id,
        "display_name": config["display_name"],
        "clutch_home": str(clutch_home),
        "projects_root": str(projects_root),
        "artifact_store": str(artifact_store),
    }
    admin_guard = {
        "schema": "clutch.admin_guard.v1",
        "enabled": True,
        "mode": "token",
        "token_hash": hash_token(admin_token),
        "token_sha256": "",
    }
    artifact_store_pointer = {
        "schema": "clutch.artifact_store_pointer.v1",
        "created_at": now,
        "artifact_store": str(artifact_store),
        "policy": "large datasets, model weights, media, and caches stay outside git unless the user explicitly stages them",
    }

    files: dict[str, Any] = {
        str(clutch_home / "config" / "machine_settings.json"): machine_settings,
        str(clutch_home / "profiles" / "local_machine_profile.json"): machine_profile,
        str(clutch_home / "runtime" / "local_machine_id.txt"): machine_id + "\n",
        str(clutch_home / "config" / "admin_guard.json"): admin_guard,
        str(clutch_home / "config" / "artifact_store.json"): artifact_store_pointer,
    }
    if config["enable_collab"]:
        files[str(clutch_home / "config" / "collab_pairing.json")] = {
            "schema": "clutch.collab_pairing.v1",
            "created_at": now,
            "enabled": True,
            "pairing_code": config["pairing_code"],
            "peer_addresses": [],
            "operator_guidance": [
                "Run the first-run wizard on each PC.",
                "Use the same project id and pairing code on both PCs.",
                "Configure peer addresses only in local machine config after the operator chooses a transport.",
            ],
        }

    return {
        "schema": "clutch.public_first_run_plan.v1",
        "clutch_home": str(clutch_home),
        "machine_id": machine_id,
        "display_name": config["display_name"],
        "write_paths": sorted(files.keys()),
        "directories": sorted({str(clutch_home), str(projects_root), str(artifact_store)}),
        "files": files,
    }


def write_plan(plan: dict[str, Any], *, force: bool) -> list[str]:
    written: list[str] = []
    for directory in plan.get("directories", []):
        Path(directory).mkdir(parents=True, exist_ok=True)
    for path_text, payload in plan.get("files", {}).items():
        path = Path(path_text)
        if path.exists() and not force:
            raise FileExistsError(f"refusing to overwrite existing file without --force: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    return written


def public_result(plan: dict[str, Any], *, write: bool, written: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema": "clutch.public_first_run_result.v1",
        "ok": True,
        "write": write,
        "clutch_home": plan["clutch_home"],
        "machine_id": plan["machine_id"],
        "display_name": plan["display_name"],
        "planned_file_count": len(plan.get("write_paths", [])),
        "write_paths": plan.get("write_paths", []),
        "written_paths": written or [],
        "next_actions": [
            "Run CLUTCH session entry from a new shell after installation.",
            "The Web console will start from session-entry; safe desktop sessions may open a browser automatically.",
            "Configure online git remotes with your own account if online sync is enabled.",
            "Use the collab pairing guide on each PC if multi-PC collaboration is enabled.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create local first-run CLUTCH configuration from user-owned values.")
    parser.add_argument("--clutch-home")
    parser.add_argument("--projects-root")
    parser.add_argument("--artifact-store")
    parser.add_argument("--machine-display-name")
    parser.add_argument("--machine-id")
    parser.add_argument("--session-attach-default", choices=["prompt", "manual", "auto"], default="prompt")
    parser.add_argument("--online-sync-mode", choices=["off", "best_effort", "required"], default="off")
    parser.add_argument("--github-setup", choices=["skip", "existing_git", "gh_auth"], default="skip")
    parser.add_argument("--enable-collab", action="store_true")
    parser.add_argument("--pairing-code")
    parser.add_argument("--web-console-auto-start", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--web-console-auto-open", choices=["safe", "never", "always"], default="safe")
    parser.add_argument("--web-console-host", default="127.0.0.1")
    parser.add_argument("--web-console-port", type=int, default=8765)
    parser.add_argument("--admin-token-stdin", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--write", action="store_true", help="Write first-run config. Non-interactive mode stays dry-run unless this is set.")
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Preview the first-run plan without writing files. Interactive mode writes by default unless this is set.",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = collect_config(args)
        admin_token = resolve_admin_token(token_stdin=args.admin_token_stdin, non_interactive=args.non_interactive)
        plan = build_install_plan(config, admin_token)
        should_write = bool(args.write or (not args.non_interactive and not args.plan_only))
        if args.write and args.plan_only:
            raise ValueError("--write and --plan-only cannot be used together")
        written = write_plan(plan, force=args.force) if should_write else []
        result = public_result(plan, write=should_write, written=written)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        action = "wrote" if result["write"] else "planned"
        print(f"{action} CLUTCH first-run config for {result['machine_id']}")
        for path in result["written_paths"] if result["write"] else result["write_paths"]:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
