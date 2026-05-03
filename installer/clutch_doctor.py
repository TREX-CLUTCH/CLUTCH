#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def default_clutch_home() -> Path:
    return Path(os.environ.get("CLUTCH_HOME") or (Path.home() / ".clutch"))


def check_item(name: str, ok: bool, *, severity: str, summary: str, details: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "severity": severity,
        "summary": summary,
        "details": details,
    }


def file_exists(root: Path, relative_path: str) -> bool:
    return (root / relative_path).exists()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def web_health(url: str, timeout: float) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(4096).decode("utf-8", errors="replace")
            return 200 <= response.status < 300, body[:300]
    except (OSError, urllib.error.URLError) as exc:
        return False, str(exc)


def run_checks(*, root: Path, clutch_home: Path, web_url: str, timeout: float) -> dict[str, Any]:
    root = root.expanduser().resolve()
    clutch_home = clutch_home.expanduser().resolve()
    checks: list[dict[str, Any]] = []

    checks.append(
        check_item(
            "python",
            sys.version_info >= (3, 10),
            severity="error",
            summary=f"Python {sys.version_info.major}.{sys.version_info.minor}",
            details="Python 3.10 or newer is recommended for CLUTCH.",
        )
    )
    checks.append(
        check_item(
            "git",
            shutil.which("git") is not None,
            severity="warning",
            summary="git CLI available" if shutil.which("git") else "git CLI not found",
            details="Git is required for online sync and project reproducibility checks.",
        )
    )
    checks.append(
        check_item(
            "codex",
            shutil.which("codex") is not None,
            severity="warning",
            summary="Codex CLI available" if shutil.which("codex") else "Codex CLI not found",
            details="CLUTCH can still install, but Codex session orchestration needs the Codex CLI.",
        )
    )
    checks.append(
        check_item(
            "root",
            root.exists(),
            severity="error",
            summary=str(root),
            details="Distribution root must exist.",
        )
    )

    required_files = {
        "README.md": "public README",
        "assets/clutch.png": "representative image",
        "scripts/clutch_ctl.py": "core CLI",
        "scripts/clutch_web.py": "Web backend",
        "modules/web/static/index.html": "Web UI",
        "registry/projects.json": "default project registry",
        "installer/clutch_first_run_wizard.py": "first-run wizard",
        "installer/install.sh": "source installer",
        "collab_transport/scripts/clutch_collab_file_transport.py": "public collab transport helper",
    }
    for relative_path, label in required_files.items():
        checks.append(
            check_item(
                f"file:{relative_path}",
                file_exists(root, relative_path),
                severity="error",
                summary=f"{label} present" if file_exists(root, relative_path) else f"{label} missing",
            )
        )

    settings_path = clutch_home / "config" / "machine_settings.json"
    guard_path = clutch_home / "config" / "admin_guard.json"
    checks.append(
        check_item(
            "first_run_config",
            settings_path.exists(),
            severity="warning",
            summary="first-run config present" if settings_path.exists() else "first-run config not created yet",
            details="Run installer/clutch_first_run_wizard.py before normal use.",
        )
    )
    if settings_path.exists():
        try:
            settings = load_json(settings_path)
            web_console = settings.get("web_console", {}) if isinstance(settings, dict) else {}
            web_console_configured = isinstance(web_console, dict) and "auto_start_on_session_entry" in web_console
        except Exception:
            web_console_configured = False
        checks.append(
            check_item(
                "web_console_preference",
                web_console_configured,
                severity="warning",
                summary="Web console session-entry preference configured"
                if web_console_configured
                else "Web console session-entry preference missing",
                details="The first-run wizard records whether session-entry should start/open the local Web console.",
            )
        )
    if guard_path.exists():
        try:
            guard = load_json(guard_path)
            token_guard = isinstance(guard, dict) and guard.get("mode") == "token" and bool(guard.get("token_hash"))
        except Exception:
            token_guard = False
        checks.append(
            check_item(
                "admin_guard",
                token_guard,
                severity="error",
                summary="token admin guard configured" if token_guard else "admin guard exists but is not token-ready",
            )
        )
    else:
        checks.append(
            check_item(
                "admin_guard",
                False,
                severity="warning",
                summary="admin guard not created yet",
                details="The first-run wizard creates a local token guard.",
            )
        )

    if web_url:
        ok, details = web_health(web_url, timeout)
        checks.append(
            check_item(
                "web_health",
                ok,
                severity="warning",
                summary="Web console responded" if ok else "Web console not reachable",
                details=details,
            )
        )

    errors = [item for item in checks if item["severity"] == "error" and not item["ok"]]
    warnings = [item for item in checks if item["severity"] == "warning" and not item["ok"]]
    return {
        "schema": "clutch.public_doctor.v1",
        "ok": not errors,
        "root": str(root),
        "clutch_home": str(clutch_home),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "checks": checks,
        "next_actions": [
            "Run installer/clutch_first_run_wizard.py if first-run config is missing.",
            "Configure GitHub and multi-PC peers only with user-owned accounts and addresses.",
            "Run scripts/clutch_ctl.py session-entry after first-run setup.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a CLUTCH public installation without mutating state.")
    parser.add_argument("--root", type=Path, default=repo_root_from_script())
    parser.add_argument("--clutch-home", type=Path, default=default_clutch_home())
    parser.add_argument("--web-url", default="")
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_checks(root=args.root, clutch_home=args.clutch_home, web_url=args.web_url, timeout=args.timeout)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        status = "ok" if payload["ok"] else "failed"
        print(f"clutch_doctor status={status} warnings={payload['warning_count']} errors={payload['error_count']}")
        for item in payload["checks"]:
            marker = "ok" if item["ok"] else item["severity"]
            print(f"[{marker}] {item['name']}: {item['summary']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
