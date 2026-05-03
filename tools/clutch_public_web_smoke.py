#!/usr/bin/env python3
"""Run a clean first-run Web console smoke for CLUTCH public.

The smoke installs the exported tree into a temporary CLUTCH_HOME, writes
first-run config with Web console auto-start enabled, runs session-entry, checks
the local Web backend, fetches the public UI assets, and then stops the Web
process it started.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


SMOKE_MACHINE_ID = "public-web-smoke-01"
REPEATED_SETUP_PROMPT_MARKERS = (
    "machine_default_needs_user_choice=True",
    "이 PC의 새 Codex 세션을 CLUTCH에 기본적으로 auto / prompt / manual 중 무엇으로 둘까?",
    "first-run config missing",
    "clutch_first_run_wizard.py",
)
HTML_REQUIRED_MARKERS = (
    "CLUTCH",
    "Dashboard",
    "Sessions",
    "Monitor",
    "Projects",
    "Backups",
    "Machines",
    "Commands",
    "Help",
    "CLUTCH Operating Protocol",
    "Core Differentiators",
    "Visible Collab Monitor",
    "Away Development",
    "Approval and Safety Boundary",
)
ASSET_PATHS = (
    "/assets/styles.css",
    "/assets/app.js",
    "/assets/clutch-mark.png",
)
HEALTH_REQUIRED_COMMANDS = (
    "web-console-status",
    "project-refresh-preview",
    "project-checkpoint-write",
    "collab-monitor-status",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run_step(
    name: str,
    command: list[str],
    *,
    env: dict[str, str],
    cwd: Path | None = None,
    input_text: str | None = None,
    ok_returncodes: tuple[int, ...] = (0,),
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload: dict[str, Any] | None = None
    if completed.stdout.strip().startswith("{"):
        try:
            parsed = json.loads(completed.stdout)
            payload = parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            payload = None
    return {
        "name": name,
        "ok": completed.returncode in ok_returncodes,
        "returncode": completed.returncode,
        "ok_returncodes": list(ok_returncodes),
        "command": command,
        "payload": payload,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def enforce_no_repeated_setup_prompt(step: dict[str, Any]) -> dict[str, Any]:
    output = f"{step.get('stdout_tail', '')}\n{step.get('stderr_tail', '')}"
    markers = [marker for marker in REPEATED_SETUP_PROMPT_MARKERS if marker in output]
    step["repeated_setup_prompt_checked"] = True
    step["forbidden_repeat_prompt_markers"] = markers
    if markers:
        step["ok"] = False
        step["details"] = "session-entry repeated first-run setup prompts after config was written"
    return step


def fetch_url(base_url: str, path: str, *, timeout: float = 3.0) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    try:
        with urlopen(url, timeout=timeout) as response:
            body = response.read()
            content_type = str(response.headers.get("Content-Type") or "")
            status = int(response.status)
    except HTTPError as exc:
        return {"ok": False, "url": url, "status": int(exc.code), "error": f"HTTP {exc.code}"}
    except (OSError, URLError) as exc:
        return {"ok": False, "url": url, "status": 0, "error": str(exc)}
    return {
        "ok": 200 <= status < 300 and bool(body),
        "url": url,
        "status": status,
        "content_type": content_type,
        "byte_count": len(body),
        "text": body.decode("utf-8", errors="replace")
        if "text" in content_type or "json" in content_type or path.endswith((".html", ".css", ".js"))
        else "",
    }


def check_health(base_url: str) -> dict[str, Any]:
    fetched = fetch_url(base_url, "/api/health", timeout=5.0)
    if not fetched["ok"]:
        return {"name": "web_health", "ok": False, "returncode": 1, "fetch": fetched, "details": "health fetch failed"}
    try:
        payload = json.loads(str(fetched.get("text") or ""))
    except json.JSONDecodeError as exc:
        return {
            "name": "web_health",
            "ok": False,
            "returncode": 1,
            "fetch": {key: value for key, value in fetched.items() if key != "text"},
            "details": f"invalid health JSON: {exc}",
        }
    command_keys = set(payload.get("default_command_keys", [])) | set(payload.get("advanced_command_keys", []))
    missing_commands = [key for key in HEALTH_REQUIRED_COMMANDS if key not in command_keys]
    checks = {
        "health_ok": bool(payload.get("ok")),
        "ready": bool(payload.get("ready")),
        "status_ready": str(payload.get("status") or "") == "ready",
        "command_registry_available": bool(payload.get("command_registry_available")),
        "command_registry_integrity_ok": bool(payload.get("command_registry_integrity_ok")),
        "command_surface_integrity_ok": bool(payload.get("command_surface_integrity_ok")),
        "command_surface_render_ready": bool(payload.get("command_surface_render_ready")),
        "required_commands_present": not missing_commands,
    }
    ok = all(checks.values())
    return {
        "name": "web_health",
        "ok": ok,
        "returncode": 0 if ok else 1,
        "checks": checks,
        "missing_required_commands": missing_commands,
        "payload_summary": {
            "schema": payload.get("schema"),
            "status": payload.get("status"),
            "machine_id": payload.get("machine_id"),
            "command_count": payload.get("command_registry_command_count"),
            "default_command_count": payload.get("default_command_count"),
            "advanced_command_count": payload.get("advanced_command_count"),
            "web_backend_version": payload.get("web_backend_version"),
        },
    }


def check_static_ui(base_url: str) -> dict[str, Any]:
    index = fetch_url(base_url, "/", timeout=5.0)
    asset_results = [fetch_url(base_url, path, timeout=5.0) for path in ASSET_PATHS]
    text = str(index.get("text") or "")
    missing_markers = [marker for marker in HTML_REQUIRED_MARKERS if marker not in text]
    checks = {
        "index_ok": bool(index.get("ok")),
        "assets_ok": all(item.get("ok") for item in asset_results),
        "required_markers_present": not missing_markers,
    }
    ok = all(checks.values())
    return {
        "name": "web_static_ui",
        "ok": ok,
        "returncode": 0 if ok else 1,
        "checks": checks,
        "missing_html_markers": missing_markers,
        "index": {key: value for key, value in index.items() if key != "text"},
        "assets": [{key: value for key, value in item.items() if key != "text"} for item in asset_results],
        "required_html_markers": list(HTML_REQUIRED_MARKERS),
    }


def web_console_process_candidates(port: int) -> list[dict[str, Any]]:
    proc_root = Path("/proc")
    if not proc_root.exists():
        return []
    candidates: list[dict[str, Any]] = []
    for item in proc_root.iterdir():
        if not item.name.isdigit():
            continue
        try:
            raw = (item / "cmdline").read_bytes()
        except OSError:
            continue
        if not raw:
            continue
        argv = [part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part]
        if not any("clutch_web.py" in part for part in argv):
            continue
        observed_port = ""
        for index, part in enumerate(argv):
            if part == "--port" and index + 1 < len(argv):
                observed_port = argv[index + 1]
                break
        if observed_port == str(port):
            candidates.append({"pid": int(item.name), "command": " ".join(argv)})
    return candidates


def terminate_pid(pid: int, *, timeout: float = 3.0) -> dict[str, Any]:
    result: dict[str, Any] = {"pid": pid, "ok": False, "status": "not_attempted"}
    try:
        process_group = os.getpgid(pid)
    except OSError as exc:
        result.update({"ok": True, "status": "not_running", "details": str(exc)})
        return result
    try:
        os.killpg(process_group, signal.SIGTERM)
    except OSError as exc:
        result.update({"status": "terminate_failed", "details": str(exc)})
        return result
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            result.update({"ok": True, "status": "terminated"})
            return result
        time.sleep(0.1)
    try:
        os.killpg(process_group, signal.SIGKILL)
    except OSError:
        pass
    result.update({"ok": True, "status": "killed_after_timeout"})
    return result


def cleanup_web_processes(port: int) -> dict[str, Any]:
    candidates = web_console_process_candidates(port)
    results = [terminate_pid(int(item["pid"])) for item in candidates]
    return {
        "name": "web_process_cleanup",
        "ok": all(item.get("ok") for item in results),
        "returncode": 0 if all(item.get("ok") for item in results) else 1,
        "process_count": len(candidates),
        "candidates": candidates,
        "results": results,
    }


def smoke(*, root: Path, keep_temp: bool) -> dict[str, Any]:
    root = root.expanduser().resolve()
    temp_root = Path(tempfile.mkdtemp(prefix="clutch-public-web-smoke."))
    clutch_home = temp_root / "clutch-home"
    projects_root = temp_root / "projects"
    artifact_store = temp_root / "artifacts"
    port = free_local_port()
    web_url = f"http://127.0.0.1:{port}"
    env = {**os.environ, "CLUTCH_HOME": str(clutch_home)}
    steps: list[dict[str, Any]] = []
    cleanup: dict[str, Any] = {"name": "web_process_cleanup", "ok": True, "process_count": 0, "results": []}

    try:
        steps.append(
            run_step(
                "install",
                ["bash", str(root / "installer" / "install.sh"), "--prefix", str(clutch_home)],
                env=env,
            )
        )
        installed_root = clutch_home / "foundation" / "current"
        if steps[-1]["ok"]:
            steps.append(
                run_step(
                    "first_run_web_auto_start",
                    [
                        sys.executable,
                        str(installed_root / "installer" / "clutch_first_run_wizard.py"),
                        "--clutch-home",
                        str(clutch_home),
                        "--projects-root",
                        str(projects_root),
                        "--artifact-store",
                        str(artifact_store),
                        "--machine-display-name",
                        "Public Web Smoke",
                        "--machine-id",
                        SMOKE_MACHINE_ID,
                        "--session-attach-default",
                        "manual",
                        "--online-sync-mode",
                        "off",
                        "--github-setup",
                        "skip",
                        "--web-console-auto-start",
                        "--web-console-auto-open",
                        "never",
                        "--web-console-host",
                        "127.0.0.1",
                        "--web-console-port",
                        str(port),
                        "--admin-token-stdin",
                        "--non-interactive",
                        "--write",
                        "--json",
                    ],
                    env=env,
                    input_text="public-web-smoke-token\n",
                )
            )
        if steps and steps[-1]["ok"]:
            steps.append(
                run_step(
                    "doctor",
                    [
                        sys.executable,
                        str(installed_root / "installer" / "clutch_doctor.py"),
                        "--root",
                        str(installed_root),
                        "--clutch-home",
                        str(clutch_home),
                        "--json",
                    ],
                    env=env,
                )
            )
        if steps and steps[-1]["ok"]:
            session_entry = enforce_no_repeated_setup_prompt(
                run_step(
                    "session_entry_web_auto_start",
                    [sys.executable, str(installed_root / "scripts" / "clutch_ctl.py"), "session-entry"],
                    env=env,
                    cwd=installed_root,
                )
            )
            output = f"{session_entry.get('stdout_tail', '')}\n{session_entry.get('stderr_tail', '')}"
            session_entry["web_auto_start_checked"] = True
            session_entry["web_url"] = web_url
            session_entry["web_auto_start_ready"] = (
                "web_console_auto_status=ready" in output
                or "Web console ready:" in output
                or f"Web console ready: {web_url}" in output
            )
            if not session_entry["web_auto_start_ready"]:
                session_entry["ok"] = False
                session_entry["details"] = "session-entry did not report Web console auto-start readiness"
            steps.append(session_entry)
        if steps and steps[-1]["ok"]:
            steps.append(
                run_step(
                    "web_console_status",
                    [
                        sys.executable,
                        str(installed_root / "scripts" / "clutch_ctl.py"),
                        "web-console-status",
                        "--web-url",
                        web_url,
                        "--json",
                    ],
                    env=env,
                    cwd=installed_root,
                )
            )
            status_payload = steps[-1].get("payload") if isinstance(steps[-1].get("payload"), dict) else {}
            status_ready = bool(status_payload.get("ready")) and str(status_payload.get("status") or "") == "ready"
            steps[-1]["web_console_ready_checked"] = True
            if not status_ready:
                steps[-1]["ok"] = False
                steps[-1]["details"] = "web-console-status did not report ready"
        if steps and steps[-1]["ok"]:
            steps.append(check_health(web_url))
        if steps and steps[-1]["ok"]:
            steps.append(check_static_ui(web_url))
    finally:
        cleanup = cleanup_web_processes(port)
        if not keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)

    ok = bool(steps) and all(step["ok"] for step in steps) and bool(cleanup.get("ok"))
    forbidden_repeat_prompt_markers = sorted(
        {
            marker
            for step in steps
            for marker in step.get("forbidden_repeat_prompt_markers", [])
            if isinstance(marker, str)
        }
    )
    return {
        "schema": "clutch.public_web_smoke.v1",
        "ok": ok,
        "status": "passed" if ok else "failed",
        "root": str(root),
        "temp_root": str(temp_root),
        "temp_preserved": bool(keep_temp),
        "clutch_home": str(clutch_home),
        "web_url": web_url,
        "port": port,
        "first_run_repeat_prompt_check": {
            "checked": True,
            "ok": not forbidden_repeat_prompt_markers,
            "forbidden_markers": forbidden_repeat_prompt_markers,
        },
        "web_process_cleanup": cleanup,
        "step_count": len(steps),
        "steps": steps,
        "next_actions": []
        if ok
        else ["inspect the failed step output; rerun with --keep-temp to preserve the temporary install"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root_from_script())
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = smoke(root=args.root, keep_temp=args.keep_temp)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"clutch_public_web_smoke status={payload['status']} steps={payload['step_count']}")
        for step in payload["steps"]:
            marker = "ok" if step["ok"] else "failed"
            print(f"[{marker}] {step['name']}")
        cleanup = payload["web_process_cleanup"]
        print(f"[{'ok' if cleanup['ok'] else 'failed'}] web_process_cleanup")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
