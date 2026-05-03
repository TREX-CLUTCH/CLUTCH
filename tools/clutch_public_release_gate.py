#!/usr/bin/env python3
"""Read-only public release gate for an exported CLUTCH distribution tree."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    ".gitignore",
    "CONTRIBUTING.md",
    "Makefile",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/pull_request_template.md",
    ".github/workflows/pages.yml",
    ".github/workflows/public-ci.yml",
    "README.md",
    "SECURITY.md",
    "PUBLIC_DISTRIBUTION_BUILD.json",
    "assets/clutch.png",
    "site/index.html",
    "site/styles.css",
    "installer/install.sh",
    "installer/clutch_first_run_wizard.py",
    "installer/clutch_doctor.py",
    "scripts/clutch_ctl.py",
    "scripts/clutch_web.py",
    "modules/web/static/index.html",
    "tools/clutch_distribution_scan.py",
    "tools/clutch_public_release_gate.py",
    "tools/clutch_public_landing_smoke.py",
    "tools/clutch_public_web_smoke.py",
    "tools/clutch_public_collab_smoke.py",
    "tools/clutch_public_install_smoke.py",
    "tools/clutch_public_visibility_review.py",
    "tools/clutch_public_verify.py",
    "collab_transport/scripts/clutch_collab_file_transport.py",
    "docs/getting-started.md",
    "docs/command-cheatsheet.md",
    "docs/faq.md",
    "docs/privacy-and-redaction.md",
    "docs/verification-matrix.md",
    "docs/prompt-cookbook.md",
    "docs/launch-readiness-brief.md",
    "docs/first-use-acceptance.md",
    "docs/codex-session-entry.md",
    "docs/multi-pc-collab.md",
    "docs/two-pc-lab-tutorial.md",
    "docs/backup-and-restore.md",
    "docs/away-development.md",
    "docs/landing-page.md",
    "docs/github-publication.md",
    "docs/public-demo-script.md",
    "docs/troubleshooting.md",
    "docs/release-artifacts.md",
    "docs/public-release-checklist.md",
    "docs/release-notes-template.md",
    "templates/AGENTS.clutch.example.md",
)
PUBLIC_GITHUB_REPO_URL = "https://github.com/TREX-CLUTCH/CLUTCH"
FORBIDDEN_CACHE_DIR_NAMES = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
FORBIDDEN_ARTIFACT_DIR_NAMES = FORBIDDEN_CACHE_DIR_NAMES | {
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "releases",
    "restore-smoke",
}
FORBIDDEN_ARTIFACT_FILE_NAMES = {
    ".coverage",
    ".DS_Store",
}
FORBIDDEN_BYTECODE_SUFFIXES = {
    ".pyc",
    ".pyo",
}
FORBIDDEN_ARTIFACT_SUFFIXES = FORBIDDEN_BYTECODE_SUFFIXES | {
    ".log",
    ".tmp",
}

REQUIRED_TEXT = {
    ".gitignore": (
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        "node_modules/",
        ".coverage",
        "htmlcov/",
        "build/",
        "dist/",
        "*.egg-info/",
        ".DS_Store",
        "releases/",
        "restore-smoke/",
        "*.log",
        "*.tmp",
    ),
    ".github/workflows/public-ci.yml": (
        "permissions:",
        "contents: read",
        "pull_request:",
        "make verify",
        "clutch_distribution_scan.py",
        "clutch_public_release_gate.py",
        "clutch_public_landing_smoke.py",
        "clutch_public_web_smoke.py",
        "clutch_public_collab_smoke.py",
        "clutch_public_install_smoke.py",
        "clutch_public_visibility_review.py",
        "clutch_public_verify.py",
        "--root . --json",
    ),
    ".github/workflows/pages.yml": (
        "Deploy CLUTCH Pages",
        "workflow_dispatch:",
        "pages: write",
        "id-token: write",
        "actions/configure-pages",
        "actions/upload-pages-artifact",
        "actions/deploy-pages",
        "site/index.html",
        "site/styles.css",
        "cp -R assets",
        "cp -R docs",
        ".pages-build",
    ),
    ".github/pull_request_template.md": (
        "make verify",
        "clutch_distribution_scan.py",
        "clutch_public_release_gate.py",
        "clutch_public_landing_smoke.py",
        "clutch_public_web_smoke.py",
        "clutch_public_collab_smoke.py",
        "clutch_public_install_smoke.py",
        "clutch_public_visibility_review.py",
        "clutch_public_verify.py",
        "No private machine ids",
        "explicit operator approval",
    ),
    ".github/ISSUE_TEMPLATE/bug_report.yml": (
        "Do not include secrets",
        "Reproduction steps",
        "Validation output",
        "Public boundary confirmation",
    ),
    ".github/ISSUE_TEMPLATE/feature_request.yml": (
        "Feature request",
        "Multi-PC collab",
        "Backup and snapshots",
        "Safety and privacy boundary",
    ),
    ".github/ISSUE_TEMPLATE/config.yml": (
        "blank_issues_enabled: false",
        "Security boundary",
    ),
    "CONTRIBUTING.md": (
        "Contributing To CLUTCH",
        "public distribution boundary",
        "make verify",
        "make landing-smoke",
        "make web-smoke",
        "make collab-smoke",
        "clutch_distribution_scan.py",
        "clutch_public_release_gate.py",
        "clutch_public_landing_smoke.py",
        "clutch_public_web_smoke.py",
        "clutch_public_collab_smoke.py",
        "clutch_public_install_smoke.py",
        "clutch_public_visibility_review.py",
        "clutch_public_verify.py",
        "Pull Request Checklist",
        "Security Reports",
    ),
    "Makefile": (
        "make verify",
        "make scan",
        "make gate",
        "make visibility-review",
        "make landing-smoke",
        "make web-smoke",
        "make collab-smoke",
        "make install-smoke",
        "make serve-landing",
        "http://127.0.0.1:$(PORT)/site/",
        "clutch_public_verify.py",
        "clutch_distribution_scan.py",
        "clutch_public_release_gate.py",
        "clutch_public_landing_smoke.py",
        "clutch_public_web_smoke.py",
        "clutch_public_collab_smoke.py",
        "clutch_public_install_smoke.py",
        "clutch_public_visibility_review.py",
    ),
    "installer/install.sh": (
        "--exclude='__pycache__'",
        "--exclude='.pytest_cache'",
        "--exclude='.mypy_cache'",
        "--exclude='.ruff_cache'",
        "--exclude='node_modules'",
        "--exclude='.coverage'",
        "--exclude='htmlcov'",
        "--exclude='build'",
        "--exclude='dist'",
        "--exclude='*.egg-info'",
        "--exclude='releases'",
        "--exclude='restore-smoke'",
        "--exclude='*.pyc'",
        "--exclude='*.pyo'",
        "--exclude='.DS_Store'",
        "--exclude='*.log'",
        "--exclude='*.tmp'",
    ),
    "README.md": (
        "CLUTCH is a local-first Codex orchestration layer",
        "https://trex-clutch.github.io/CLUTCH/",
        "official CLUTCH landing page",
        "10-Minute First Use Path",
        "Project re-entry",
        "Multi-PC Collab",
        "Multi-PC collab",
        "Collab monitor",
        "Web console",
        "Backup and reproducibility",
        "Away-development plans",
        "Public first-run wizard",
        "Lab Patterns",
        "backup/snapshot evidence",
        "static source",
        "First-Use Acceptance Runbook",
        "Command Cheat Sheet",
        "Verification Matrix",
        "Prompt Cookbook",
        "FAQ",
        "Privacy And Redaction",
        "Contributing",
        "Public Demo Script",
        "Trust And Verification",
        "docs/verification-matrix.md",
        "docs/prompt-cookbook.md",
        "docs/first-use-acceptance.md",
        "Release zip, SHA256 checksum, release notes, and manifest files",
        "make verify",
        "make landing-smoke",
        "make web-smoke",
        "make collab-smoke",
        "clutch_public_landing_smoke.py",
        "clutch_public_web_smoke.py",
        "clutch_public_collab_smoke.py",
        "installer/clutch_doctor.py",
        "clean first-project path",
    ),
    "site/index.html": (
        "Multi-PC Codex orchestration",
        "View on GitHub",
        "AI and robotics labs",
        "Example operator prompts",
        "Prompt Cookbook",
        "Multi-PC collab",
        "Visible monitor",
        "Large-project recovery",
        "Away development",
        "Web console",
        "Private by design",
        "Guided first run",
        "collab transport",
        "Safety boundary",
        "User verification",
        "Inspect CLUTCH before you depend on it.",
        "Clean first run",
        "Local smoke checks",
        "Artifact boundaries",
        "First-Use Acceptance Runbook",
        "../docs/first-use-acceptance.md",
        "Verification Matrix",
        "../docs/verification-matrix.md",
        "../docs/prompt-cookbook.md",
    ),
    "SECURITY.md": (
        "tools/clutch_distribution_scan.py .",
        "Public Release Checklist",
        "Privacy And Redaction",
        "operator explicitly approves",
    ),
    "docs/public-release-checklist.md": (
        "finding_count=0",
        "docs/verification-matrix.md",
        "docs/prompt-cookbook.md",
        "docs/launch-readiness-brief.md",
        "docs/first-use-acceptance.md",
        "Clean Install Smoke",
        "tools/clutch_public_install_smoke.py",
        "tools/clutch_public_web_smoke.py",
        "tools/clutch_public_collab_smoke.py",
        "tools/clutch_public_visibility_review.py",
        "First Project Smoke",
        "Landing Page Smoke",
        "clutch_public_landing_smoke.py",
        "Web Console Smoke",
        "Multi-PC Collab Smoke",
        "fetches the linked Prompt Cookbook, First-Use Acceptance",
        "2-4 word hook title",
        "only the landing page hero H1 uses the sans-serif face",
        "all other landing",
        "10-minute first-use path",
        "release zip checksum",
        "SHA256 values for the checksum file, release notes, and release manifest",
        "operator explicitly approves",
        "Final Visibility Gate",
        "GitHub Actions",
        "visibility review",
        "Web smoke, collab smoke,",
        "issue templates",
        "CONTRIBUTING.md",
        "docs/github-publication.md",
        "repository metadata",
        "make verify",
        "make visibility-review",
        "make landing-smoke",
        "make web-smoke",
        "make collab-smoke",
        "private staging repository",
        "manual operator action",
        "official landing page",
        "docs/release-artifacts.md",
    ),
    "docs/verification-matrix.md": (
        "Verification Matrix",
        "Release Tree Gates",
        "First Install Gates",
        "Core Workflow Gates",
        "Web And Monitor Gates",
        "Multi-PC Collab Gates",
        "Away Development Gates",
        "Publication Gates",
        "make verify",
        "clutch_public_visibility_review.py",
        "remote_visibility_change_performed=false",
        "clutch_public_install_smoke.py",
        "clutch_public_web_smoke.py",
        "clutch_public_collab_smoke.py",
        "project-backup",
        "project-snapshot",
        "project-refresh --project <project_id> --dry-run",
        "web-console-start",
        "collab-monitor-status",
        "notify-mode-long",
        "collab_transport/scripts/clutch_collab_file_transport.py",
        "direct wired LAN",
        "explicitly approves the visibility change",
    ),
    "docs/prompt-cookbook.md": (
        "Prompt Cookbook",
        "First Install",
        "First Project",
        "Multi-PC Collab",
        "Backup And Artifacts",
        "Away Development",
        "Web UI And Help",
        "Public Release Review",
        "Safety Prompts",
        "clutch_public_visibility_review.py",
        "remote_visibility_change_performed",
        "Web smoke, collab smoke, install smoke",
        "first-project smoke",
        "project-backup",
        "project-snapshot",
        "artifact pointers",
        "collab monitor",
        "direct wired LAN",
        "explicit approval",
    ),
    "docs/launch-readiness-brief.md": (
        "Public Launch Readiness Brief",
        "local-first Codex orchestration layer",
        "multi-PC Codex collab",
        "Collab monitor evidence",
        "Backup and snapshot workflow",
        "Away-development plans",
        "Web UI",
        "First-run wizard",
        "First Visitor Path",
        "First-Use Acceptance Runbook",
        "GitHub Page Review",
        "Required Evidence",
        "make verify",
        "clutch_public_release_gate.py",
        "clutch_public_visibility_review.py",
        "ready_for_manual_visibility_review",
        "remote_visibility_change_performed=false",
        "clutch_public_landing_smoke.py",
        "clutch_public_web_smoke.py",
        "clutch_public_collab_smoke.py",
        "clutch_public_install_smoke.py",
        "private staging repository remains private",
        "explicit approval",
    ),
    "docs/first-use-acceptance.md": (
        "First-Use Acceptance Runbook",
        "make verify",
        "clutch_public_install_smoke.py",
        "session_entry_repeat",
        "project_workspace_hygiene",
        "collect first-run choices once",
        "Acceptance Criteria",
        "session-entry",
        "project-create",
        "session-attach",
        "project-backup",
        "project-snapshot --write",
        "project-refresh --dry-run",
        "git status --porcelain",
        "does not ask for the same first-run decisions again",
        "without configuring multi-PC collab",
        "No-Go Signals",
        "private GitHub remote",
        "LAN IP",
        "remote_visibility_change_performed=false",
        "private staging repository remains private",
    ),
    "docs/release-artifacts.md": (
        "sha256sum -c clutch-public-<version>.sha256",
        "ready_for_private_release_upload",
        "manifest_sha256",
        "remote_visibility_change_performed=false",
        "explicit operator approval",
    ),
    "docs/github-publication.md": (
        "GitHub Publication Guide",
        "Repository Metadata",
        "https://trex-clutch.github.io/CLUTCH/",
        "First Screen Review",
        "make verify",
        "make visibility-review",
        "make landing-smoke",
        "make web-smoke",
        "make collab-smoke",
        "Release Artifacts",
        "Visibility Change",
        "explicit operator approval",
        "private hostnames",
    ),
    "docs/landing-page.md": (
        "site/index.html",
        "assets/clutch.png",
        "GitHub Pages",
        "first-use verification path",
        "operator explicitly approves",
        "tools/clutch_public_landing_smoke.py --root . --json",
        "tools/clutch_public_release_gate.py --root . --json",
        "key linked public docs",
        "hero H1 is the only landing page",
        "Every other heading, control, caption, and",
        "artifact boundaries",
    ),
    "docs/public-demo-script.md": (
        "Public Demo Script",
        "Demo Boundary",
        "Prompt Cookbook",
        "Verification Matrix",
        "single-PC proof",
        "Web console",
        "project-backup",
        "project-snapshot",
        "project-refresh --project my-project --dry-run",
        "Optional Two-PC Collab Demo",
        "wired LAN",
        "collab_transport/scripts/clutch_collab_file_transport.py",
        "tools/clutch_public_web_smoke.py --root . --json",
        "tools/clutch_public_collab_smoke.py --root . --json",
        "Collab monitor",
        "Away Development Demo",
        "Public Launch Talking Points",
        "No hardware motion",
        "explicit operator approval",
    ),
    "tools/clutch_public_install_smoke.py": (
        "clutch.public_install_smoke.v1",
        "REPEATED_SETUP_PROMPT_MARKERS",
        "session_entry_repeat",
        "first_run_repeat_prompt_check",
        "project_workspace_hygiene",
        "FORBIDDEN_PROJECT_WORKSPACE_PATHS",
        "installer/install.sh",
        "clutch_first_run_wizard.py",
        "clutch_doctor.py",
        "session-entry",
        "project-create",
        "session-attach",
        "project-backup",
        "project-snapshot",
        "project-refresh",
        "--keep-temp",
    ),
    "tools/clutch_public_landing_smoke.py": (
        "clutch.public_landing_smoke.v1",
        "ThreadingHTTPServer",
        "site/index.html",
        "site/styles.css",
        "assets/clutch.png",
        "docs/prompt-cookbook.md",
        "docs/first-use-acceptance.md",
        "docs/verification-matrix.md",
        "docs/faq.md",
        "CLUTCH for Research Agents",
        "https://github.com/TREX-CLUTCH/CLUTCH",
        "PNG_HEADER",
    ),
    "tools/clutch_public_web_smoke.py": (
        "clutch.public_web_smoke.v1",
        "first_run_web_auto_start",
        "session_entry_web_auto_start",
        "web_console_status",
        "web_health",
        "web_static_ui",
        "web_process_cleanup",
        "REPEATED_SETUP_PROMPT_MARKERS",
        "HTML_REQUIRED_MARKERS",
        "HEALTH_REQUIRED_COMMANDS",
        "web-console-status",
        "collab-monitor-status",
        "project-checkpoint-write",
        "CLUTCH Operating Protocol",
        "--keep-temp",
    ),
    "tools/clutch_public_collab_smoke.py": (
        "clutch.public_collab_smoke.v1",
        "clutch_collab_file_transport.py",
        "public-main",
        "public-worker",
        "req-public-smoke",
        "machine_init",
        "request_opened",
        "request_result",
        "open_request_count",
        "recent_events",
        "--keep-temp",
    ),
    "tools/clutch_public_verify.py": (
        "clutch.public_verify.v1",
        "clutch_distribution_scan.py",
        "clutch_public_release_gate.py",
        "clutch_public_landing_smoke.py",
        "clutch_public_web_smoke.py",
        "clutch_public_collab_smoke.py",
        "clutch_public_install_smoke.py",
        "clutch_public_visibility_review.py",
        "scanner",
        "release_gate",
        "visibility_review",
        "landing_page_smoke",
        "web_console_smoke",
        "collab_transport_smoke",
        "install_first_project_smoke",
        "--skip-install-smoke",
        "--keep-temp",
    ),
    "tools/clutch_public_visibility_review.py": (
        "clutch.public_visibility_review.v1",
        "ready_for_manual_visibility_review",
        "remote_visibility_change_performed",
        "public_visibility_requires_operator_approval",
        "clutch_public_release_gate.py",
        "clutch_distribution_scan.py",
        "visibility_review_required_text_missing",
    ),
    "docs/getting-started.md": (
        "What This First Run Should Prove",
        "project-refresh --project my-project --dry-run",
        "Read The First Status Like An Operator",
        "artifact store",
    ),
    "docs/command-cheatsheet.md": (
        "Command Cheat Sheet",
        "Verify A Release Tree",
        "Verification Matrix",
        "make verify",
        "make web-smoke",
        "make collab-smoke",
        "clutch_public_visibility_review.py",
        "ready_for_manual_visibility_review",
        "session-entry",
        "project-create",
        "session-attach",
        "project-backup",
        "project-snapshot",
        "project-refresh --project my-project --dry-run",
        "web-console-start",
        "collab_transport/scripts/clutch_collab_file_transport.py",
        "project-status --project my-project",
        "Approval Boundary",
        "explicit operator approval",
    ),
    "docs/faq.md": (
        "Frequently Asked Questions",
        "Does CLUTCH include private lab settings?",
        "No.",
        "How do I connect GitHub?",
        "first-run wizard",
        "How do I choose an artifact store?",
        "Multi-PC collab",
        "wired LAN",
        "Web console",
        "backup and snapshot",
        "away development",
        "operator approval",
        "public repository visibility",
    ),
    "docs/privacy-and-redaction.md": (
        "Privacy And Redaction",
        "Scanner-Covered Risks",
        "Manual Review Risks",
        "Private Machine Identity",
        "Network And Transport",
        "GitHub And Credentials",
        "Artifacts And Large Files",
        "Release Notes Review",
        "tools/clutch_distribution_scan.py . --json",
        "private denylist",
        "Do Not Publish",
        "explicit operator approval",
    ),
    "docs/release-notes-template.md": (
        "CLUTCH is a local-first Codex orchestration layer",
        "10-Minute First Use Path",
        "2-4 word hook hero",
        "public landing page source",
        "tools/clutch_public_landing_smoke.py --root . --json",
        "tools/clutch_public_web_smoke.py --root . --json",
        "tools/clutch_public_collab_smoke.py --root . --json",
        "Multi-PC collab guidance",
        "Visible collab monitor",
        "Backup and reproducibility workflow",
        "Large artifact policy",
        "Away-development plans",
        "Public first-run flow",
        "release zip SHA256",
        "checksum file SHA256",
        "release notes SHA256",
        "release manifest SHA256",
        "Release Artifacts",
        "Verification Matrix",
        "Prompt Cookbook",
        "First-Use Acceptance Runbook",
        "finding_count=0",
        "visibility review",
        "ready_for_manual_visibility_review",
        "fresh explicit operator approval",
    ),
    "modules/web/static/index.html": (
        "CLUTCH Operating Protocol",
        "Core Differentiators",
        "Visible Collab Monitor",
        "Away Development",
        "Approval and Safety Boundary",
    ),
}


def add_finding(findings: list[dict[str, str]], kind: str, path: str, message: str) -> None:
    findings.append({"kind": kind, "path": path, "message": message})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_files(root: Path, findings: list[dict[str, str]]) -> None:
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            add_finding(findings, "missing_required_file", rel, "required public distribution file is missing")


def check_required_text(root: Path, findings: list[dict[str, str]]) -> None:
    for rel, needles in REQUIRED_TEXT.items():
        path = root / rel
        if not path.exists():
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            add_finding(findings, "text_read_error", rel, "required text file is not valid UTF-8")
            continue
        for needle in needles:
            if needle not in text:
                add_finding(findings, "missing_required_text", rel, f"missing required text: {needle}")


def first_line_containing(lines: list[str], needle: str) -> int | None:
    for index, line in enumerate(lines, start=1):
        if needle in line:
            return index
    return None


def check_readme_first_screen(root: Path, findings: list[dict[str, str]]) -> None:
    readme = root / "README.md"
    if not readme.exists():
        return
    try:
        lines = read_text(readme).splitlines()
    except UnicodeDecodeError:
        return

    first_non_empty = next((line.strip() for line in lines if line.strip()), "")
    if first_non_empty != "# CLUTCH":
        add_finding(
            findings,
            "readme_first_screen_title",
            "README.md",
            "README must open with the CLUTCH title for GitHub first-screen clarity",
        )

    required_positions = (
        ("<img src=\"assets/clutch.png\"", 6, "brand image must appear before the first screen scroll"),
        (
            "local-first Codex orchestration layer",
            12,
            "core product description must appear before the first screen scroll",
        ),
        (
            "https://trex-clutch.github.io/CLUTCH/",
            18,
            "official landing page link must appear before the first screen scroll",
        ),
    )
    for needle, max_line, message in required_positions:
        line_number = first_line_containing(lines, needle)
        if line_number is None or line_number > max_line:
            detail = f"{message}; expected by line {max_line}"
            if line_number is not None:
                detail += f", found line {line_number}"
            add_finding(findings, "readme_first_screen_missing", "README.md", detail)


INSTALL_GUIDANCE_FILES = (
    "README.md",
    "docs/getting-started.md",
    "site/index.html",
)
INSTALL_COMMAND_SEQUENCE = (
    "unzip clutch-public-*.zip",
    "cd clutch-public-*",
    'export CLUTCH_HOME="${CLUTCH_HOME:-$HOME/.clutch}"',
    'bash installer/install.sh --prefix "$CLUTCH_HOME"',
    'cd "$CLUTCH_HOME/foundation/current"',
    "python3 installer/clutch_first_run_wizard.py",
    "python3 installer/clutch_doctor.py",
    "python3 scripts/clutch_ctl.py session-entry",
)


def check_install_guidance_sequence(root: Path, findings: list[dict[str, str]]) -> None:
    for rel in INSTALL_GUIDANCE_FILES:
        path = root / rel
        if not path.exists():
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        cursor = 0
        for command in INSTALL_COMMAND_SEQUENCE:
            index = text.find(command, cursor)
            if index == -1:
                add_finding(
                    findings,
                    "install_guidance_command_missing",
                    rel,
                    f"install guidance must include command in order: {command}",
                )
                break
            cursor = index + len(command)


def normalize_markdown_link_target(target: str) -> str:
    target = target.strip()
    if not target:
        return ""
    if target.startswith("<"):
        closing = target.find(">")
        if closing != -1:
            return target[1:closing].strip()
    return target.split()[0].strip()


def check_markdown_links(root: Path, findings: list[dict[str, str]]) -> None:
    for markdown_path in sorted(root.rglob("*.md")):
        if any(part in {".git", "__pycache__"} for part in markdown_path.relative_to(root).parts):
            continue
        text = read_text(markdown_path)
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            link_target = normalize_markdown_link_target(target)
            if link_target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = link_target.split("#", 1)[0].strip()
            if not target_path:
                continue
            candidate = (markdown_path.parent / target_path).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                add_finding(
                    findings,
                    "markdown_link_escapes_root",
                    str(markdown_path.relative_to(root)),
                    f"link escapes release root: {target}",
                )
                continue
            if not candidate.exists():
                add_finding(
                    findings,
                    "markdown_link_missing",
                    str(markdown_path.relative_to(root)),
                    f"link target is missing: {target}",
                )


class HtmlReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str, str]] = []
        self.ids: set[str] = set()
        self.h1_texts: list[str] = []
        self._h1_depth = 0
        self._h1_chunks: list[str] = []
        self.script_seen = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)
        if tag.lower() == "h1":
            self._h1_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "h1" or self._h1_depth <= 0:
            return
        self._h1_depth -= 1
        if self._h1_depth == 0:
            title = " ".join(" ".join(self._h1_chunks).split())
            self.h1_texts.append(title)
            self._h1_chunks = []

    def handle_data(self, data: str) -> None:
        if self._h1_depth > 0:
            self._h1_chunks.append(data)

    def _record(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if normalized_tag == "script":
            self.script_seen = True
        for name, value in attrs:
            normalized_name = name.lower()
            if normalized_name == "id" and value:
                self.ids.add(value.strip())
            if normalized_name in {"href", "src"} and value:
                self.references.append((normalized_tag, name.lower(), value.strip()))


def html_reference_is_local(target: str) -> bool:
    lowered = target.lower()
    if (
        not target
        or lowered.startswith(("mailto:", "tel:", "data:"))
        or lowered.startswith(("http://", "https://"))
    ):
        return False
    return True


def split_html_reference(target: str) -> tuple[str, str]:
    without_query = target.split("?", 1)[0].strip()
    if "#" not in without_query:
        return without_query, ""
    path_text, fragment = without_query.split("#", 1)
    return path_text.strip(), fragment.strip()


def html_document_ids(path: Path) -> set[str]:
    parser = HtmlReferenceParser()
    parser.feed(read_text(path))
    return parser.ids


def normalize_external_link(target: str) -> str:
    return target.split("#", 1)[0].split("?", 1)[0].rstrip("/")


def check_static_site_public_links(root: Path, findings: list[dict[str, str]]) -> None:
    for html_path in sorted((root / "site").glob("*.html")):
        relative_html = str(html_path.relative_to(root))
        try:
            text = read_text(html_path)
        except UnicodeDecodeError:
            continue
        parser = HtmlReferenceParser()
        parser.feed(text)
        public_repo_seen = False
        for tag, attr, target in parser.references:
            if tag != "a" or attr != "href":
                continue
            normalized = normalize_external_link(target)
            if normalized == PUBLIC_GITHUB_REPO_URL:
                public_repo_seen = True
                continue
            if normalized.startswith("https://github.com/") or normalized.startswith("http://github.com/"):
                add_finding(
                    findings,
                    "site_public_github_link_unexpected",
                    relative_html,
                    f"public landing page GitHub links must point to {PUBLIC_GITHUB_REPO_URL}: {target}",
                )
        if relative_html == "site/index.html" and not public_repo_seen:
            add_finding(
                findings,
                "site_public_github_cta_missing",
                relative_html,
                f"public landing page must link to {PUBLIC_GITHUB_REPO_URL}",
            )


TITLE_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")


def check_static_site_hero_titles(root: Path, findings: list[dict[str, str]]) -> None:
    for html_path in sorted((root / "site").glob("*.html")):
        relative_html = str(html_path.relative_to(root))
        try:
            text = read_text(html_path)
        except UnicodeDecodeError:
            continue
        parser = HtmlReferenceParser()
        parser.feed(text)
        if not parser.h1_texts:
            add_finding(findings, "site_hero_missing_h1", relative_html, "public landing page needs one H1 title")
            continue
        if len(parser.h1_texts) > 1:
            add_finding(
                findings,
                "site_hero_multiple_h1",
                relative_html,
                f"public landing page must keep exactly one H1 title, found {len(parser.h1_texts)}",
            )
        title = parser.h1_texts[0]
        words = TITLE_WORD_RE.findall(title)
        if not re.search(r"\bCLUTCH\b", title):
            add_finding(
                findings,
                "site_hero_title_missing_brand",
                relative_html,
                "public landing H1 must include the CLUTCH brand",
            )
        if not 2 <= len(words) <= 4:
            add_finding(
                findings,
                "site_hero_title_word_count",
                relative_html,
                f"public landing H1 must be 2-4 words, found {len(words)}: {title}",
            )
        if len(title) > 48:
            add_finding(
                findings,
                "site_hero_title_too_long",
                relative_html,
                "public landing H1 should stay concise enough for first-viewport scanning",
            )


def check_static_site_assets(root: Path, findings: list[dict[str, str]]) -> None:
    for html_path in sorted((root / "site").glob("*.html")):
        relative_html = str(html_path.relative_to(root))
        try:
            text = read_text(html_path)
        except UnicodeDecodeError:
            add_finding(findings, "html_read_error", relative_html, "site HTML is not valid UTF-8")
            continue
        parser = HtmlReferenceParser()
        parser.feed(text)
        if parser.script_seen:
            add_finding(
                findings,
                "site_script_present",
                relative_html,
                "public landing pages must stay static; script tags require a separate review",
            )
        for tag, attr, target in parser.references:
            lowered = target.lower()
            if tag in {"img", "link", "script"} and lowered.startswith(("http://", "https://")):
                add_finding(
                    findings,
                    "site_external_asset",
                    relative_html,
                    f"external {tag} {attr} is not allowed in the public landing page: {target}",
                )
                continue
            if not html_reference_is_local(target):
                continue
            target_path, fragment = split_html_reference(target)
            if not target_path and fragment:
                if fragment not in parser.ids:
                    add_finding(
                        findings,
                        "site_anchor_missing",
                        relative_html,
                        f"{tag} {attr} anchor target is missing: {target}",
                    )
                continue
            if not target_path:
                continue
            candidate = (html_path.parent / target_path).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                add_finding(
                    findings,
                    "site_asset_escapes_root",
                    relative_html,
                    f"{tag} {attr} escapes release root: {target}",
                )
                continue
            if not candidate.exists():
                add_finding(
                    findings,
                    "site_asset_missing",
                    relative_html,
                    f"{tag} {attr} target is missing: {target}",
                )
                continue
            if fragment and candidate.suffix.lower() in {".html", ".htm"}:
                try:
                    target_ids = html_document_ids(candidate)
                except UnicodeDecodeError:
                    add_finding(
                        findings,
                        "html_read_error",
                        str(candidate.relative_to(root)),
                        "site HTML is not valid UTF-8",
                    )
                    continue
                if fragment not in target_ids:
                    add_finding(
                        findings,
                        "site_anchor_missing",
                        relative_html,
                        f"{tag} {attr} anchor target is missing: {target}",
                    )


CSS_BLOCK_RE = re.compile(r"(?P<selectors>[^{}]+)\{(?P<body>[^{}]+)\}", re.DOTALL)
CSS_DECLARATION_RE = re.compile(r"(?P<property>[A-Za-z-]+)\s*:\s*(?P<value>[^;{}]+)")


def css_value_is_zero(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"0", "0px", "0rem", "0em"}


def check_static_site_css(root: Path, findings: list[dict[str, str]]) -> None:
    for css_path in sorted((root / "site").glob("*.css")):
        relative_css = str(css_path.relative_to(root))
        try:
            text = read_text(css_path)
        except UnicodeDecodeError:
            add_finding(findings, "css_read_error", relative_css, "site CSS is not valid UTF-8")
            continue
        for block in CSS_BLOCK_RE.finditer(text):
            selectors = " ".join(block.group("selectors").split())
            body = block.group("body")
            if "font-family: var(--font-sans)" in body and selectors != ".hero h1":
                add_finding(
                    findings,
                    "site_css_sans_outside_hero_title",
                    relative_css,
                    f"only the landing page hero H1 should use the sans font, found selector: {selectors}",
                )
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in CSS_DECLARATION_RE.finditer(line):
                prop = match.group("property").strip().lower()
                value = match.group("value").strip().lower()
                if prop == "font-size" and re.search(r"\b\d*\.?\d+(?:vw|vh|vmin|vmax)\b", value):
                    add_finding(
                        findings,
                        "site_css_viewport_font_size",
                        relative_css,
                        f"line {line_number}: font-size must not use viewport units",
                    )
                if prop == "letter-spacing" and not css_value_is_zero(value):
                    add_finding(
                        findings,
                        "site_css_nonzero_letter_spacing",
                        relative_css,
                        f"line {line_number}: letter-spacing must be 0",
                    )


def check_no_public_artifacts(root: Path, findings: list[dict[str, str]]) -> None:
    for path in sorted(root.rglob("*")):
        relative_path = str(path.relative_to(root))
        if path.is_dir() and path.name in FORBIDDEN_ARTIFACT_DIR_NAMES:
            if path.name == "__pycache__":
                kind = "pycache_present"
            elif path.name in FORBIDDEN_CACHE_DIR_NAMES:
                kind = "python_cache_dir_present"
            else:
                kind = "release_artifact_dir_present"
            add_finding(
                findings,
                kind,
                relative_path,
                "release tree should not contain cache, dependency, build, or release-output directories",
            )
        if path.is_file() and path.name in FORBIDDEN_ARTIFACT_FILE_NAMES:
            add_finding(
                findings,
                "release_artifact_file_present",
                relative_path,
                "release tree should not contain local coverage or OS metadata files",
            )
        if path.is_file() and path.suffix.lower() in FORBIDDEN_BYTECODE_SUFFIXES:
            add_finding(
                findings,
                "python_bytecode_present",
                relative_path,
                "release tree should not contain Python bytecode files",
            )
        elif path.is_file() and path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES:
            add_finding(
                findings,
                "release_artifact_file_present",
                relative_path,
                "release tree should not contain log or temporary files",
            )


def run_scanner(root: Path, private_denylist: Path | None) -> dict[str, Any]:
    scanner = root / "tools" / "clutch_distribution_scan.py"
    if not scanner.exists():
        return {
            "ok": False,
            "finding_count": 1,
            "findings": [
                {
                    "kind": "missing_scanner",
                    "path": "tools/clutch_distribution_scan.py",
                    "message": "scanner is missing",
                }
            ],
        }
    command = [sys.executable, str(scanner), str(root), "--json"]
    if private_denylist is not None:
        command.extend(["--private-denylist", str(private_denylist)])
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {
                "ok": False,
                "finding_count": 1,
                "findings": [
                    {
                        "kind": "scanner_error",
                        "path": "tools/clutch_distribution_scan.py",
                        "message": result.stderr.strip() or "scanner failed",
                    }
                ],
            }
        return payload
    return json.loads(result.stdout)


def build_gate_payload(root: Path, private_denylist: Path | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    findings: list[dict[str, str]] = []
    if not root.exists():
        add_finding(findings, "missing_root", str(root), "release root does not exist")
        return {
            "schema": "clutch.public_release_gate.v1",
            "ok": False,
            "status": "failed",
            "root": str(root),
            "finding_count": len(findings),
            "findings": findings,
        }

    check_required_files(root, findings)
    check_required_text(root, findings)
    check_readme_first_screen(root, findings)
    check_install_guidance_sequence(root, findings)
    check_markdown_links(root, findings)
    check_static_site_hero_titles(root, findings)
    check_static_site_public_links(root, findings)
    check_static_site_assets(root, findings)
    check_static_site_css(root, findings)
    check_no_public_artifacts(root, findings)
    scanner_payload = run_scanner(root, private_denylist)
    for item in scanner_payload.get("findings", []):
        findings.append(
            {
                "kind": f"scanner:{item.get('kind', 'finding')}",
                "path": str(item.get("path", "")),
                "message": str(item.get("message", "")),
            }
        )

    ok = len(findings) == 0
    return {
        "schema": "clutch.public_release_gate.v1",
        "ok": ok,
        "status": "ready_for_operator_review" if ok else "failed",
        "root": str(root),
        "scanner_ok": bool(scanner_payload.get("ok")),
        "scanner_finding_count": int(scanner_payload.get("finding_count") or 0),
        "finding_count": len(findings),
        "findings": findings,
        "next_actions": [
            "run clean install smoke",
            "run first project smoke",
            "run Web console smoke",
            "run multi-PC collab smoke",
            "record release zip SHA256",
            "keep repository private until explicit operator approval",
        ]
        if ok
        else ["fix findings before staging or publishing the release"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Exported CLUTCH release root.")
    parser.add_argument("--private-denylist", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_gate_payload(args.root, args.private_denylist)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"public_release_gate status={payload['status']} finding_count={payload['finding_count']}")
        for finding in payload["findings"]:
            print(f"{finding['path']}: {finding['kind']}: {finding['message']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
