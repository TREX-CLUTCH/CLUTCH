#!/usr/bin/env python3
"""Run a clean temporary install and first-project smoke for CLUTCH public.

The smoke runs installer/install.sh, installer/clutch_first_run_wizard.py,
installer/clutch_doctor.py, scripts/clutch_ctl.py session-entry twice, a
throwaway git project, project-create, session-attach, project-backup,
project-snapshot, project-refresh, and project workspace hygiene checks in a
temporary CLUTCH_HOME.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SMOKE_MACHINE_ID = "public-install-smoke-01"
SMOKE_PROJECT_ID = "public-smoke-project"
SMOKE_REPO_ID = "public-smoke-project"
REPEATED_SETUP_PROMPT_MARKERS = (
    "machine_default_needs_user_choice=True",
    "이 PC의 새 Codex 세션을 CLUTCH에 기본적으로 auto / prompt / manual 중 무엇으로 둘까?",
    "first-run config missing",
    "clutch_first_run_wizard.py",
)
FORBIDDEN_PROJECT_WORKSPACE_PATHS = (
    ".clutch",
    "machines",
    "snapshots",
    "backups",
    "runtime",
    "registry",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


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
    return {
        "name": name,
        "ok": completed.returncode in ok_returncodes,
        "returncode": completed.returncode,
        "ok_returncodes": list(ok_returncodes),
        "command": command,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def run_sequence(
    name: str,
    commands: list[list[str]],
    *,
    env: dict[str, str],
    cwd: Path | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    ok = True
    for command in commands:
        result = run_step(name, command, env=env, cwd=cwd)
        results.append(
            {
                "ok": result["ok"],
                "returncode": result["returncode"],
                "command": result["command"],
                "stdout_tail": result["stdout_tail"],
                "stderr_tail": result["stderr_tail"],
            }
        )
        if not result["ok"]:
            ok = False
            break
    return {
        "name": name,
        "ok": ok,
        "returncode": 0 if ok else results[-1]["returncode"],
        "commands": commands,
        "results": results,
        "stdout_tail": results[-1]["stdout_tail"] if results else "",
        "stderr_tail": results[-1]["stderr_tail"] if results else "",
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


def check_project_workspace_hygiene(project_root: Path, *, env: dict[str, str]) -> dict[str, Any]:
    forbidden_paths = [name for name in FORBIDDEN_PROJECT_WORKSPACE_PATHS if (project_root / name).exists()]
    status = run_step(
        "project_workspace_git_status",
        ["git", "status", "--porcelain"],
        env=env,
        cwd=project_root,
    )
    dirty_entries = [line for line in status.get("stdout_tail", "").splitlines() if line.strip()]
    ok = not forbidden_paths and status["ok"] and not dirty_entries
    return {
        "name": "project_workspace_hygiene",
        "ok": ok,
        "returncode": 0 if ok else 1,
        "workspace": str(project_root),
        "forbidden_project_workspace_paths": forbidden_paths,
        "git_status_clean": status["ok"] and not dirty_entries,
        "git_status_entries": dirty_entries,
        "checked_forbidden_paths": list(FORBIDDEN_PROJECT_WORKSPACE_PATHS),
        "details": ""
        if ok
        else "CLUTCH wrote metadata into the sample project workspace or left git status dirty",
    }


def smoke(*, root: Path, keep_temp: bool) -> dict[str, Any]:
    root = root.expanduser().resolve()
    temp_root = Path(tempfile.mkdtemp(prefix="clutch-public-install-smoke."))
    clutch_home = temp_root / "clutch-home"
    projects_root = temp_root / "projects"
    artifact_store = temp_root / "artifacts"
    project_root = projects_root / SMOKE_PROJECT_ID
    env = {**os.environ, "CLUTCH_HOME": str(clutch_home)}
    steps: list[dict[str, Any]] = []

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
                    "first_run",
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
                        "Public Install Smoke",
                        "--machine-id",
                        SMOKE_MACHINE_ID,
                        "--session-attach-default",
                        "manual",
                        "--online-sync-mode",
                        "off",
                        "--github-setup",
                        "skip",
                        "--no-web-console-auto-start",
                        "--web-console-auto-open",
                        "never",
                        "--admin-token-stdin",
                        "--non-interactive",
                        "--write",
                        "--json",
                    ],
                    env=env,
                    input_text="public-install-smoke-token\n",
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
            steps.append(
                enforce_no_repeated_setup_prompt(
                    run_step(
                        "session_entry",
                        [sys.executable, str(installed_root / "scripts" / "clutch_ctl.py"), "session-entry"],
                        env=env,
                        cwd=installed_root,
                    )
                )
            )
        if steps and steps[-1]["ok"]:
            steps.append(
                enforce_no_repeated_setup_prompt(
                    run_step(
                        "session_entry_repeat",
                        [sys.executable, str(installed_root / "scripts" / "clutch_ctl.py"), "session-entry"],
                        env=env,
                        cwd=installed_root,
                    )
                )
            )
        if steps and steps[-1]["ok"]:
            project_root.mkdir(parents=True, exist_ok=True)
            (project_root / "README.md").write_text("# Public Smoke Project\n", encoding="utf-8")
            steps.append(
                run_sequence(
                    "sample_project_git",
                    [
                        ["git", "init"],
                        ["git", "config", "user.name", "CLUTCH Public Smoke"],
                        ["git", "config", "user.email", "smoke@example.invalid"],
                        ["git", "add", "README.md"],
                        ["git", "commit", "-m", "Initial public smoke project"],
                        ["git", "branch", "-M", "main"],
                    ],
                    env=env,
                    cwd=project_root,
                )
            )
        if steps and steps[-1]["ok"]:
            steps.append(
                run_step(
                    "project_create",
                    [
                        sys.executable,
                        str(installed_root / "scripts" / "clutch_ctl.py"),
                        "project-create",
                        "--project",
                        SMOKE_PROJECT_ID,
                        "--display-name",
                        "Public Smoke Project",
                        "--machine-workspace",
                        f"{SMOKE_MACHINE_ID}={project_root}",
                        "--repo-source",
                        f"{SMOKE_REPO_ID}:{SMOKE_MACHINE_ID}={project_root}",
                        "--primary-repo",
                        SMOKE_REPO_ID,
                        "--participant-machine",
                        SMOKE_MACHINE_ID,
                        "--owner-machine",
                        SMOKE_MACHINE_ID,
                        "--preferred-main-machine",
                        SMOKE_MACHINE_ID,
                        "--role-policy",
                        "none",
                        "--binding-policy",
                        "manual",
                        "--no-admin-guard-required",
                        "--yes",
                        "--json",
                    ],
                    env=env,
                    cwd=installed_root,
                )
            )
        if steps and steps[-1]["ok"]:
            steps.append(
                run_step(
                    "session_attach",
                    [
                        sys.executable,
                        str(installed_root / "scripts" / "clutch_ctl.py"),
                        "session-attach",
                        "--project",
                        SMOKE_PROJECT_ID,
                        "--cwd",
                        str(project_root),
                        "--bind-role",
                        "main",
                        "--yes",
                        "--json",
                    ],
                    env=env,
                    cwd=installed_root,
                )
            )
        if steps and steps[-1]["ok"]:
            steps.append(
                run_step(
                    "project_backup",
                    [
                        sys.executable,
                        str(installed_root / "scripts" / "clutch_ctl.py"),
                        "project-backup",
                        "--project",
                        SMOKE_PROJECT_ID,
                        "--label",
                        "public-install-smoke",
                        "--json",
                    ],
                    env=env,
                    cwd=installed_root,
                )
            )
        if steps and steps[-1]["ok"]:
            steps.append(
                run_step(
                    "project_snapshot",
                    [
                        sys.executable,
                        str(installed_root / "scripts" / "clutch_ctl.py"),
                        "project-snapshot",
                        "--project",
                        SMOKE_PROJECT_ID,
                        "--label",
                        "public-install-smoke",
                        "--skip-runtime",
                        "--write",
                        "--json",
                    ],
                    env=env,
                    cwd=installed_root,
                )
            )
        if steps and steps[-1]["ok"]:
            steps.append(
                run_step(
                    "project_refresh",
                    [
                        sys.executable,
                        str(installed_root / "scripts" / "clutch_ctl.py"),
                        "project-refresh",
                        "--project",
                        SMOKE_PROJECT_ID,
                        "--skip-runtime",
                        "--dry-run",
                        "--json",
                    ],
                    env=env,
                    cwd=installed_root,
                    ok_returncodes=(0, 1),
                )
            )
        if steps and steps[-1]["ok"]:
            steps.append(check_project_workspace_hygiene(project_root, env=env))
    finally:
        if not keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)

    ok = bool(steps) and all(step["ok"] for step in steps)
    forbidden_repeat_prompt_markers = sorted(
        {
            marker
            for step in steps
            for marker in step.get("forbidden_repeat_prompt_markers", [])
            if isinstance(marker, str)
        }
    )
    project_workspace_hygiene = next(
        (step for step in steps if step.get("name") == "project_workspace_hygiene"),
        {
            "ok": False,
            "forbidden_project_workspace_paths": [],
            "git_status_clean": False,
            "git_status_entries": [],
            "checked_forbidden_paths": list(FORBIDDEN_PROJECT_WORKSPACE_PATHS),
        },
    )
    return {
        "schema": "clutch.public_install_smoke.v1",
        "ok": ok,
        "status": "passed" if ok else "failed",
        "root": str(root),
        "temp_root": str(temp_root),
        "temp_preserved": bool(keep_temp),
        "clutch_home": str(clutch_home),
        "projects_root": str(projects_root),
        "first_project": {
            "project_id": SMOKE_PROJECT_ID,
            "repo_id": SMOKE_REPO_ID,
            "machine_id": SMOKE_MACHINE_ID,
            "workspace": str(project_root),
        },
        "first_run_repeat_prompt_check": {
            "checked": True,
            "ok": not forbidden_repeat_prompt_markers,
            "forbidden_markers": forbidden_repeat_prompt_markers,
        },
        "project_workspace_hygiene": {
            "checked": True,
            "ok": bool(project_workspace_hygiene.get("ok")),
            "forbidden_project_workspace_paths": project_workspace_hygiene.get(
                "forbidden_project_workspace_paths",
                [],
            ),
            "git_status_clean": bool(project_workspace_hygiene.get("git_status_clean")),
            "git_status_entries": project_workspace_hygiene.get("git_status_entries", []),
        },
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
        print(f"clutch_public_install_smoke status={payload['status']} steps={payload['step_count']}")
        for step in payload["steps"]:
            marker = "ok" if step["ok"] else "failed"
            print(f"[{marker}] {step['name']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
