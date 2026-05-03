#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mimetypes
import re
import subprocess
import sys
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from clutch_ctl import (
    DEFAULT_COLLAB_STALE_SEC,
    PROJECT_BACKUPS_ROOT,
    build_collab_monitor_status_payload,
    build_overview_payload,
    build_worker_status_payload,
    command_line,
    default_ops_root,
    is_binding_active,
    load_active_bindings,
    load_registry,
    normalize_machine_id,
    project_entries,
    project_machine_role_summary,
    session_collab_monitor_context,
)


ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = ROOT_DIR / "modules" / "web" / "static"
CLUTCH_CTL = ROOT_DIR / "scripts" / "clutch_ctl.py"
DEFAULT_WEB_PORT = 8765
READ_TIMEOUT_SEC = 90
MACHINE_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,96}$")
WEB_VERSION_SURFACE = (
    "scripts/clutch_web.py",
    "scripts/clutch_ctl.py",
    "modules/web/static/index.html",
    "modules/web/static/app.js",
    "modules/web/static/styles.css",
)


def git_head_version() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return re.sub(r"[^A-Za-z0-9_.-]", "", result.stdout.strip())
    except OSError:
        pass
    return "nogit"


def static_asset_version() -> str:
    head = git_head_version()
    digest = hashlib.sha256()
    seen = False
    for relative in WEB_VERSION_SURFACE:
        path = ROOT_DIR / relative
        try:
            data = path.read_bytes()
        except OSError:
            continue
        seen = True
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    if not seen:
        return head
    return f"{head}-{digest.hexdigest()[:8]}"


WEB_PROCESS_VERSION = static_asset_version()


def command_policy_badges(
    *,
    project_scoped: bool,
    state_changing: bool,
    confirmation_required: bool,
    preview_only: bool,
    advanced_apply: bool,
) -> list[dict[str, Any]]:
    badges: list[dict[str, Any]] = []
    if preview_only:
        badges.append({"label": {"en": "Preview only", "ko": "미리보기"}, "tone": "preview"})
    elif state_changing:
        badges.append({"label": {"en": "Changes state", "ko": "상태 변경"}, "tone": "write"})
    else:
        badges.append({"label": {"en": "Read-only", "ko": "읽기 전용"}, "tone": "read"})
    if confirmation_required:
        badges.append({"label": {"en": "Confirm", "ko": "확인 필요"}, "tone": "confirm"})
    if project_scoped:
        badges.append({"label": {"en": "Project", "ko": "프로젝트"}, "tone": "project"})
    if advanced_apply:
        badges.append({"label": {"en": "Advanced apply", "ko": "고급 실행"}, "tone": "advanced"})
    return badges


def command_meta(
    key: str,
    *,
    group: str,
    title_en: str,
    title_ko: str,
    detail_en: str,
    detail_ko: str,
    scope_en: str,
    scope_ko: str,
    project_scoped: bool = False,
    state_changing: bool = False,
    confirmation_required: bool | None = None,
    preview_only: bool = False,
    advanced_apply: bool = False,
    attention_kinds: list[str] | None = None,
) -> dict[str, Any]:
    requires_confirmation = state_changing if confirmation_required is None else bool(confirmation_required)
    return {
        "key": key,
        "group": group,
        "title": {"en": title_en, "ko": title_ko},
        "detail": {"en": detail_en, "ko": detail_ko},
        "scope": {"en": scope_en, "ko": scope_ko},
        "project_scoped": project_scoped,
        "state_changing": state_changing,
        "read_only": not state_changing,
        "confirmation_required": requires_confirmation,
        "preview_only": preview_only,
        "advanced_apply": advanced_apply,
        "attention_kinds": attention_kinds or [],
        "policy_badges": command_policy_badges(
            project_scoped=project_scoped,
            state_changing=state_changing,
            confirmation_required=requires_confirmation,
            preview_only=preview_only,
            advanced_apply=advanced_apply,
        ),
    }


WEB_COMMANDS: list[dict[str, Any]] = [
    command_meta(
        "overview",
        group="default",
        title_en="Status Check",
        title_ko="상태 확인",
        detail_en="Machine, projects, workers, and attention summary.",
        detail_ko="머신, 프로젝트, 워커, 주의 항목 요약입니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "project-attention-resolution-plan",
        group="default",
        title_en="Troubleshoot",
        title_ko="문제 해결",
        detail_en="Resolution plan for selected project Review items.",
        detail_ko="선택 프로젝트의 주의 항목 해결 계획입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
        attention_kinds=["*"],
    ),
    command_meta(
        "project-refresh-preview",
        group="default",
        title_en="Refresh Check",
        title_ko="전체 새로고침 점검",
        detail_en="Checks code sync, metadata fetch, versioning, and restore readiness together.",
        detail_ko="코드 동기화, 메타데이터 fetch, 버전 관리, 복구 준비도를 함께 점검합니다.",
        scope_en="Project Preview",
        scope_ko="프로젝트 미리보기",
        project_scoped=True,
        preview_only=True,
        attention_kinds=["repo_sync", "project_sync", "sync", "versioning_readiness", "project_snapshot", "restore"],
    ),
    command_meta(
        "project-checkpoint-write",
        group="default",
        title_en="Checkpoint",
        title_ko="체크포인트",
        detail_en="Creates a local backup and reproducibility manifest.",
        detail_ko="로컬 backup과 재현 manifest를 함께 생성합니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
        attention_kinds=["project_backup", "project_snapshot"],
    ),
    command_meta(
        "project-away-prepare-intent",
        group="default",
        title_en="Prepare Away",
        title_ko="자리비움 준비",
        detail_en="Records an away-work intent for the next Codex prompt.",
        detail_ko="다음 Codex 지시가 참고할 자리비움 intent를 기록합니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
        attention_kinds=["away_plan"],
    ),
    command_meta(
        "project-away-continue-intent",
        group="default",
        title_en="Continue Away",
        title_ko="자리비움 이어가기",
        detail_en="Records intent to continue within the active away plan.",
        detail_ko="활성 away plan 범위에서 이어갈 intent를 기록합니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
        attention_kinds=["away_plan"],
    ),
    command_meta(
        "collab-binding-align-preview",
        group="default",
        title_en="Collab Check",
        title_ko="Collab 상태 점검",
        detail_en="Preview-only live collab and binding alignment check.",
        detail_ko="실시간 collab 연결과 binding 정렬 필요 여부만 확인합니다.",
        scope_en="Project Preview",
        scope_ko="프로젝트 미리보기",
        project_scoped=True,
        preview_only=True,
        attention_kinds=["collab", "collab_readiness", "collab_binding", "binding_alignment", "worker_link"],
    ),
    command_meta(
        "collab-monitor-status",
        group="default",
        title_en="Monitor Check",
        title_ko="Monitor 점검",
        detail_en="Checks whether collab monitors are running and operator-visible.",
        detail_ko="collab monitor가 실행 중이고 사용자가 볼 수 있는 상태인지 확인합니다.",
        scope_en="Project Collab",
        scope_ko="프로젝트 Collab",
        project_scoped=True,
        attention_kinds=["collab", "collab_readiness", "collab_monitor", "monitor_visibility", "worker_link", "runtime"],
    ),
    command_meta(
        "project-restore-readiness",
        group="default",
        title_en="Recovery Review",
        title_ko="복구 검토",
        detail_en="Non-destructive restore audit and blockers.",
        detail_ko="비파괴 restore 검토와 blocker 상태입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
        attention_kinds=["project_backup", "project_snapshot", "restore"],
    ),
    command_meta(
        "attention-resolution-plan",
        group="advanced-system",
        title_en="Attention Plan",
        title_ko="주의 해결 계획",
        detail_en="Maps Review items to checks and gated fixes.",
        detail_ko="주의 항목을 확인 명령과 승인 수정으로 정리합니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "attention-resolution-fix-preview",
        group="advanced-system",
        title_en="Attention Fix Preview",
        title_ko="주의 해결 미리보기",
        detail_en="Previews resolver steps and terminal apply command.",
        detail_ko="해결 단계와 터미널 적용 명령을 확인합니다.",
        scope_en="System Preview",
        scope_ko="시스템 미리보기",
    ),
    command_meta(
        "bindings",
        group="advanced-system",
        title_en="Binding List",
        title_ko="Binding 목록",
        detail_en="Active and archived project/session bindings.",
        detail_ko="활성 및 보관된 프로젝트/세션 binding입니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "binding-check",
        group="advanced-system",
        title_en="Binding Check",
        title_ko="Binding 점검",
        detail_en="Selected project attach conflicts and recommendations.",
        detail_ko="선택 프로젝트 기준 attach 충돌과 권장 조치입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
    ),
    command_meta(
        "runtime-check",
        group="advanced-system",
        title_en="Runtime Check",
        title_ko="Runtime 점검",
        detail_en="Local services, daemon, notify, and collab runtime health.",
        detail_ko="로컬 service, daemon, notify, collab runtime 상태입니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "worker-status",
        group="advanced-system",
        title_en="Worker Status",
        title_ko="워커 상태",
        detail_en="Worker link state, queue state, and availability.",
        detail_ko="워커 연결 상태, queue, 사용 가능 여부입니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "reboot-readiness",
        group="advanced-system",
        title_en="Reboot Readiness",
        title_ko="재부팅 준비도",
        detail_en="Manual reboot recovery readiness without rebooting.",
        detail_ko="실제 재부팅 없이 수동 재부팅 복구 준비도를 확인합니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "web-console-status",
        group="advanced-system",
        title_en="Web Console Status",
        title_ko="Web 콘솔 상태",
        detail_en="Checks whether the local Web UI process is ready and version-aligned.",
        detail_ko="로컬 Web UI 프로세스가 실행 중이고 버전이 정렬됐는지 확인합니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "web-console-browser-smoke",
        group="advanced-system",
        title_en="Browser Smoke",
        title_ko="브라우저 Smoke",
        detail_en="Runs a headless screenshot smoke against the local Web UI when a browser is available.",
        detail_ko="사용 가능한 브라우저가 있으면 로컬 Web UI headless screenshot smoke를 실행합니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "machine-version-state",
        group="advanced-system",
        title_en="Machine Version State",
        title_ko="머신 버전 상태",
        detail_en="Foundation, ops, and collab checkout parity for this PC.",
        detail_ko="이 PC의 foundation, ops, collab checkout 버전 상태입니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "machine-lifecycle-readiness",
        group="advanced-system",
        title_en="Machine Lifecycle",
        title_ko="머신 Lifecycle",
        detail_en="Install, session entry, reconnect, runtime, and online sync readiness.",
        detail_ko="설치, session entry, reconnect, runtime, online sync 준비도입니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "online-identity",
        group="advanced-system",
        title_en="Online Identity",
        title_ko="온라인 Identity",
        detail_en="GitHub authentication, SSH identity, and expected repository access.",
        detail_ko="GitHub 인증, SSH identity, 예상 repo 접근 상태입니다.",
        scope_en="System",
        scope_ko="시스템",
    ),
    command_meta(
        "project-status",
        group="advanced-project",
        title_en="Project Status",
        title_ko="프로젝트 상태",
        detail_en="Selected project repo sync, backup, binding, and away state.",
        detail_ko="선택 프로젝트의 repo 동기화, backup, binding, away 상태입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
    ),
    command_meta(
        "project-sync-preview",
        group="advanced-project",
        title_en="Repo Sync Check",
        title_ko="Repo 동기화 점검",
        detail_en="Lower-level clone/pull readiness preview without changing the workspace.",
        detail_ko="workspace를 변경하지 않는 저수준 clone/pull 준비도 미리보기입니다.",
        scope_en="Project Preview",
        scope_ko="프로젝트 미리보기",
        project_scoped=True,
        preview_only=True,
        attention_kinds=["repo_sync", "project_sync", "sync"],
    ),
    command_meta(
        "project-history",
        group="advanced-project",
        title_en="Project History",
        title_ko="프로젝트 이력",
        detail_en="Durable docs, git commits, backups, snapshots, metadata, and away evidence.",
        detail_ko="지속 문서, git commit, backup, snapshot, metadata, away 근거입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
    ),
    command_meta(
        "project-attention-resolution-fix-preview",
        group="advanced-project",
        title_en="Project Fix Preview",
        title_ko="프로젝트 해결 미리보기",
        detail_en="Previews fixes for selected project attention items.",
        detail_ko="선택 프로젝트의 주의 항목 해결을 미리봅니다.",
        scope_en="Project Preview",
        scope_ko="프로젝트 미리보기",
        project_scoped=True,
    ),
    command_meta(
        "project-versioning-readiness",
        group="advanced-project",
        title_en="Versioning Readiness",
        title_ko="버전 관리 준비도",
        detail_en="Dirty tree, remote, snapshot metadata, and publication checks.",
        detail_ko="dirty tree, remote, snapshot metadata, publication 상태를 점검합니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
        attention_kinds=["versioning_readiness"],
    ),
    command_meta(
        "project-online-publish-preview",
        group="advanced-project",
        title_en="Publish Preview",
        title_ko="Publish 미리보기",
        detail_en="Online publication authority and push plan dry run.",
        detail_ko="온라인 publish 권한과 push 계획을 dry run으로 확인합니다.",
        scope_en="Project Preview",
        scope_ko="프로젝트 미리보기",
        project_scoped=True,
    ),
    command_meta(
        "project-backups",
        group="advanced-project",
        title_en="Local Backups",
        title_ko="로컬 백업",
        detail_en="Local backup bundles available on this PC.",
        detail_ko="이 PC에서 사용할 수 있는 로컬 backup bundle입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
    ),
    command_meta(
        "project-snapshots",
        group="advanced-project",
        title_en="Local Manifests",
        title_ko="로컬 manifest",
        detail_en="Machine-local snapshot manifests for this PC.",
        detail_ko="이 PC에 저장된 machine-local snapshot manifest입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
    ),
    command_meta(
        "project-artifact-pointers",
        group="advanced-project",
        title_en="Artifact Pointers",
        title_ko="Artifact Pointer",
        detail_en="Snapshot artifact records and verification hints.",
        detail_ko="Snapshot artifact 기록과 검증 힌트입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
    ),
    command_meta(
        "project-away-report",
        group="advanced-project",
        title_en="Away Report",
        title_ko="자리비움 보고",
        detail_en="Current away-plan report and lifecycle state.",
        detail_ko="현재 away plan 보고와 lifecycle 상태입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
    ),
    command_meta(
        "project-away-cycles",
        group="advanced-project",
        title_en="Away Cycles",
        title_ko="자리비움 Cycle",
        detail_en="Queued away-development cycle history.",
        detail_ko="Queued away-development cycle 기록입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
    ),
    command_meta(
        "project-operator-intents",
        group="advanced-project",
        title_en="Operator Intents",
        title_ko="운영자 intent",
        detail_en="Pending durable intents recorded from the web console.",
        detail_ko="웹 콘솔에서 기록한 대기 intent입니다.",
        scope_en="Project",
        scope_ko="프로젝트",
        project_scoped=True,
    ),
    command_meta(
        "machine-collab-guide",
        group="advanced-collab",
        title_en="Connect New PC",
        title_ko="새 PC 연결",
        detail_en="Builds onboarding guidance for a new machine and connection mode.",
        detail_ko="새 머신과 연결 모드에 맞는 합류 안내를 생성합니다.",
        scope_en="Project Collab",
        scope_ko="프로젝트 Collab",
        project_scoped=True,
        attention_kinds=["machine_onboarding", "new_machine"],
    ),
    command_meta(
        "collab-transport-readiness",
        group="advanced-collab",
        title_en="Transport Readiness",
        title_ko="전송 준비도",
        detail_en="Checks collab repo tags, protocol, release surface, and namespaces.",
        detail_ko="collab repo tag, protocol, release surface, namespace를 점검합니다.",
        scope_en="Project Collab",
        scope_ko="프로젝트 Collab",
        project_scoped=True,
    ),
    command_meta(
        "project-collab-delegate-intent",
        group="advanced-collab",
        title_en="Delegate Intent",
        title_ko="서브에게 맡기기",
        detail_en="Records a safe worker handoff intent for the next Codex prompt.",
        detail_ko="다음 Codex 지시가 참고할 안전한 worker 위임 intent를 기록합니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
    ),
    command_meta(
        "project-sync-apply",
        group="advanced-project-actions",
        title_en="Repo Sync Apply",
        title_ko="Repo 동기화 실행",
        detail_en="Runs the project clone/pull sync plan.",
        detail_ko="프로젝트 clone/pull 동기화 계획을 실행합니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
        advanced_apply=True,
    ),
    command_meta(
        "project-refresh-apply",
        group="advanced-project-actions",
        title_en="Refresh Apply",
        title_ko="전체 새로고침 실행",
        detail_en="Applies code sync and snapshot metadata fetch, then rechecks readiness.",
        detail_ko="코드 동기화와 snapshot metadata fetch를 실행한 뒤 준비도를 다시 확인합니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
        advanced_apply=True,
    ),
    command_meta(
        "project-backup-write",
        group="advanced-project-actions",
        title_en="Write Backup",
        title_ko="백업 기록",
        detail_en="Creates a local project backup bundle.",
        detail_ko="로컬 프로젝트 백업 bundle을 생성합니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
    ),
    command_meta(
        "project-local-snapshot-write",
        group="advanced-project-actions",
        title_en="Write Manifest",
        title_ko="manifest 기록",
        detail_en="Creates a local CLUTCH snapshot manifest.",
        detail_ko="로컬 CLUTCH snapshot manifest를 생성합니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
    ),
    command_meta(
        "project-metadata-fetch-write",
        group="advanced-project-actions",
        title_en="Fetch Metadata",
        title_ko="메타데이터 가져오기",
        detail_en="Fetches snapshot metadata refs from approved remotes.",
        detail_ko="승인된 remote에서 snapshot metadata refs를 가져옵니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
    ),
    command_meta(
        "collab-binding-align-apply",
        group="advanced-project-actions",
        title_en="Collab Align Apply",
        title_ko="Collab 정렬 적용",
        detail_en="Writes binding alignment for fresh live collab links.",
        detail_ko="최신 collab 연결을 프로젝트 binding에 반영합니다.",
        scope_en="Project Action",
        scope_ko="프로젝트 작업",
        project_scoped=True,
        state_changing=True,
        advanced_apply=True,
    ),
]
WEB_COMMAND_REGISTRY: dict[str, dict[str, Any]] = {item["key"]: item for item in WEB_COMMANDS}


def command_group_meta(
    group_id: str,
    *,
    label_en: str,
    label_ko: str,
    title_en: str,
    title_ko: str,
) -> dict[str, Any]:
    return {
        "group_id": group_id,
        "label": {"en": label_en, "ko": label_ko},
        "title": {"en": title_en, "ko": title_ko},
        "command_keys": [item["key"] for item in WEB_COMMANDS if item["group"] == group_id],
    }


WEB_COMMAND_GROUPS: list[dict[str, Any]] = [
    command_group_meta(
        "default",
        label_en="Console",
        label_ko="콘솔",
        title_en="Core Workflows",
        title_ko="핵심 workflow",
    ),
    command_group_meta(
        "advanced-system",
        label_en="System",
        label_ko="시스템",
        title_en="Advanced Diagnostics",
        title_ko="고급 진단",
    ),
    command_group_meta(
        "advanced-project",
        label_en="Project",
        label_ko="프로젝트",
        title_en="Selected Project",
        title_ko="선택된 프로젝트",
    ),
    command_group_meta(
        "advanced-collab",
        label_en="Collab",
        label_ko="Collab",
        title_en="Collab / Onboarding",
        title_ko="Collab / 새 PC 합류",
    ),
    command_group_meta(
        "advanced-project-actions",
        label_en="Project",
        label_ko="프로젝트",
        title_en="Project Actions",
        title_ko="프로젝트 작업",
    ),
]
STATE_CHANGING_COMMANDS = {item["key"] for item in WEB_COMMANDS if item["state_changing"]}
CONFIRMATION_REQUIRED_COMMANDS = {item["key"] for item in WEB_COMMANDS if item["confirmation_required"]}
WORKFLOW_COMMAND_KEYS = {"project-checkpoint-write"}
ATTENTION_SHORTCUT_COMMAND_PRIORITY: dict[str, int] = {
    "project-refresh-preview": 10,
    "collab-binding-align-preview": 20,
    "collab-monitor-status": 30,
    "project-versioning-readiness": 40,
    "project-restore-readiness": 50,
    "project-sync-preview": 90,
}


def web_command_keys(*, group: str | None = None, predicate: str | None = None) -> list[str]:
    keys: list[str] = []
    for item in WEB_COMMANDS:
        if group is not None and item["group"] != group:
            continue
        if predicate is not None and not item[predicate]:
            continue
        keys.append(str(item["key"]))
    return keys


def build_attention_shortcuts_payload() -> dict[str, Any]:
    fallback_command_key = "project-attention-resolution-plan"
    kind_commands: dict[str, list[str]] = {}
    excluded_state_changing: list[str] = []
    for item in WEB_COMMANDS:
        kinds = [str(kind) for kind in item.get("attention_kinds") or [] if str(kind) and str(kind) != "*"]
        if not kinds:
            continue
        key = str(item["key"])
        if item["state_changing"] and key != fallback_command_key:
            excluded_state_changing.append(key)
            continue
        if not item["read_only"] and not item["preview_only"] and key != fallback_command_key:
            continue
        for kind in kinds:
            commands = kind_commands.setdefault(kind, [])
            if key not in commands:
                commands.append(key)
    group_rank = {str(group["group_id"]): index for index, group in enumerate(WEB_COMMAND_GROUPS)}
    registry_order = {key: index for index, key in enumerate(WEB_COMMAND_REGISTRY)}
    for commands in kind_commands.values():
        commands.sort(
            key=lambda command_key: (
                ATTENTION_SHORTCUT_COMMAND_PRIORITY.get(command_key, 1000),
                group_rank.get(str(WEB_COMMAND_REGISTRY.get(command_key, {}).get("group") or ""), 1000),
                registry_order.get(command_key, 1000),
            )
        )
    return {
        "schema": "clutch.web.attention_shortcuts.v1",
        "fallback_command_key": fallback_command_key,
        "kind_commands": kind_commands,
        "max_per_item": 3,
        "excluded_state_changing_command_keys": sorted(excluded_state_changing),
    }


def build_command_registry_integrity_payload() -> dict[str, Any]:
    command_keys = [str(item["key"]) for item in WEB_COMMANDS]
    registry_keys = list(WEB_COMMAND_REGISTRY.keys())
    group_ids = [str(group["group_id"]) for group in WEB_COMMAND_GROUPS]
    grouped_keys = [str(key) for group in WEB_COMMAND_GROUPS for key in group["command_keys"]]
    default_command_keys = web_command_keys(group="default")
    advanced_command_keys = [key for key in registry_keys if key not in default_command_keys]
    attention_shortcuts = build_attention_shortcuts_payload()
    shortcut_keys = sorted({key for commands in attention_shortcuts["kind_commands"].values() for key in commands})
    fallback_command_key = str(attention_shortcuts["fallback_command_key"])
    default_min = 8
    default_max = 10

    def duplicate_values(values: list[str]) -> list[str]:
        return sorted(value for value, count in Counter(values).items() if count > 1)

    duplicate_command_keys = duplicate_values(command_keys)
    duplicate_group_ids = duplicate_values(group_ids)
    duplicate_grouped_keys = duplicate_values(grouped_keys)
    missing_from_groups = sorted(set(registry_keys) - set(grouped_keys))
    unknown_grouped_keys = sorted(set(grouped_keys) - set(registry_keys))
    unknown_command_groups = sorted({str(item["group"]) for item in WEB_COMMANDS} - set(group_ids))
    empty_group_ids = sorted(str(group["group_id"]) for group in WEB_COMMAND_GROUPS if not group["command_keys"])
    state_changing_shortcuts = sorted(
        key for key in shortcut_keys if key in STATE_CHANGING_COMMANDS and key != fallback_command_key
    )
    shortcut_missing_commands = sorted(set(shortcut_keys) - set(registry_keys))
    state_changing_without_confirmation = sorted(STATE_CHANGING_COMMANDS - CONFIRMATION_REQUIRED_COMMANDS)
    preview_state_changing_commands = sorted(
        str(item["key"]) for item in WEB_COMMANDS if item["preview_only"] and item["state_changing"]
    )
    advanced_apply_without_state_change = sorted(
        str(item["key"]) for item in WEB_COMMANDS if item["advanced_apply"] and not item["state_changing"]
    )
    fallback_missing = fallback_command_key not in WEB_COMMAND_REGISTRY
    default_count_ok = default_min <= len(default_command_keys) <= default_max
    registry_order_matches_groups = grouped_keys == registry_keys
    workflow_commands_missing = sorted(WORKFLOW_COMMAND_KEYS - set(registry_keys))
    execution_unmapped_commands: list[str] = []
    preview_without_dry_run: list[str] = []
    project_scoped_without_project_allowed: list[str] = []
    confirmation_not_enforced: list[str] = []
    argv_mapped_count = 0
    workflow_mapped_count = 0
    for item in WEB_COMMANDS:
        key = str(item["key"])
        if key in WORKFLOW_COMMAND_KEYS:
            workflow_mapped_count += 1
            continue
        probe_project = "clutch" if item["project_scoped"] else ""
        try:
            argv = safe_command_argv(
                key,
                probe_project,
                confirmed=bool(item["confirmation_required"]),
                new_machine_id="future-pc-01",
                connection_mode="auto",
            )
        except ValueError:
            execution_unmapped_commands.append(key)
            argv = []
        else:
            argv_mapped_count += 1
        if item["preview_only"] and argv and "--dry-run" not in argv:
            preview_without_dry_run.append(key)
        if item["project_scoped"]:
            try:
                safe_command_argv(
                    key,
                    "",
                    confirmed=bool(item["confirmation_required"]),
                    new_machine_id="future-pc-01",
                    connection_mode="auto",
                )
            except ValueError:
                pass
            else:
                project_scoped_without_project_allowed.append(key)
        if item["state_changing"] and key not in WORKFLOW_COMMAND_KEYS:
            try:
                safe_command_argv(
                    key,
                    probe_project,
                    confirmed=False,
                    new_machine_id="future-pc-01",
                    connection_mode="auto",
                )
            except ValueError as exc:
                if "confirmation_required" not in str(exc):
                    confirmation_not_enforced.append(key)
            else:
                confirmation_not_enforced.append(key)

    findings: list[dict[str, Any]] = []

    def add_finding(code: str, message: str, *, severity: str = "error", keys: list[str] | None = None) -> None:
        finding: dict[str, Any] = {"code": code, "severity": severity, "message": message}
        if keys:
            finding["keys"] = keys
        findings.append(finding)

    if duplicate_command_keys:
        add_finding("duplicate_command_keys", "command keys must be unique", keys=duplicate_command_keys)
    if duplicate_group_ids:
        add_finding("duplicate_group_ids", "command group ids must be unique", keys=duplicate_group_ids)
    if duplicate_grouped_keys:
        add_finding("duplicate_grouped_keys", "command keys must appear in exactly one group", keys=duplicate_grouped_keys)
    if missing_from_groups:
        add_finding("commands_missing_from_groups", "registered commands must be exposed by a command group", keys=missing_from_groups)
    if unknown_grouped_keys:
        add_finding("unknown_grouped_commands", "command groups must not reference unknown commands", keys=unknown_grouped_keys)
    if unknown_command_groups:
        add_finding("unknown_command_groups", "commands must reference a declared group", keys=unknown_command_groups)
    if empty_group_ids:
        add_finding("empty_command_groups", "declared command groups should not be empty", keys=empty_group_ids)
    if not default_count_ok:
        add_finding(
            "default_command_count_out_of_range",
            f"default command count should stay between {default_min} and {default_max}",
            keys=default_command_keys,
        )
    if not registry_order_matches_groups:
        add_finding("registry_group_order_mismatch", "grouped command order must match registry order")
    if fallback_missing:
        add_finding("attention_fallback_missing", "attention shortcut fallback command is not registered", keys=[fallback_command_key])
    if shortcut_missing_commands:
        add_finding("attention_shortcut_missing_command", "attention shortcuts must reference registered commands", keys=shortcut_missing_commands)
    if state_changing_shortcuts:
        add_finding(
            "state_changing_attention_shortcuts",
            "attention shortcuts must not suggest state-changing commands",
            keys=state_changing_shortcuts,
        )
    if state_changing_without_confirmation:
        add_finding(
            "state_changing_without_confirmation",
            "state-changing commands must require confirmation",
            keys=state_changing_without_confirmation,
        )
    if preview_state_changing_commands:
        add_finding(
            "preview_state_changing_commands",
            "preview-only commands must not also be state-changing",
            keys=preview_state_changing_commands,
        )
    if advanced_apply_without_state_change:
        add_finding(
            "advanced_apply_without_state_change",
            "advanced apply commands should be state-changing",
            keys=advanced_apply_without_state_change,
        )
    if workflow_commands_missing:
        add_finding("workflow_command_missing", "workflow commands must be registered", keys=workflow_commands_missing)
    if execution_unmapped_commands:
        add_finding(
            "command_without_execution_path",
            "registered commands must have a backend execution path",
            keys=execution_unmapped_commands,
        )
    if preview_without_dry_run:
        add_finding(
            "preview_command_without_dry_run",
            "preview-only commands must invoke dry-run backend actions",
            keys=preview_without_dry_run,
        )
    if project_scoped_without_project_allowed:
        add_finding(
            "project_command_without_project_guard",
            "project-scoped commands must reject missing project context",
            keys=project_scoped_without_project_allowed,
        )
    if confirmation_not_enforced:
        add_finding(
            "confirmation_not_enforced",
            "state-changing command execution paths must reject unconfirmed calls",
            keys=confirmation_not_enforced,
        )

    return {
        "schema": "clutch.web.command_registry_integrity.v1",
        "ok": not findings,
        "summary": {
            "command_count": len(command_keys),
            "registry_count": len(registry_keys),
            "group_count": len(WEB_COMMAND_GROUPS),
            "default_command_count": len(default_command_keys),
            "default_command_min": default_min,
            "default_command_max": default_max,
            "advanced_command_count": len(advanced_command_keys),
            "shortcut_command_count": len(shortcut_keys),
            "argv_mapped_command_count": argv_mapped_count,
            "workflow_mapped_command_count": workflow_mapped_count,
            "execution_mapped_command_count": argv_mapped_count + workflow_mapped_count,
            "finding_count": len(findings),
        },
        "checks": {
            "unique_command_keys": not duplicate_command_keys,
            "unique_group_ids": not duplicate_group_ids,
            "commands_grouped_once": not missing_from_groups and not duplicate_grouped_keys,
            "groups_reference_known_commands": not unknown_grouped_keys,
            "commands_reference_declared_groups": not unknown_command_groups,
            "groups_non_empty": not empty_group_ids,
            "default_count_ok": default_count_ok,
            "registry_order_matches_groups": registry_order_matches_groups,
            "attention_fallback_registered": not fallback_missing,
            "attention_shortcuts_reference_registered_commands": not shortcut_missing_commands,
            "attention_shortcuts_non_mutating": not state_changing_shortcuts,
            "state_changing_commands_require_confirmation": not state_changing_without_confirmation,
            "preview_only_commands_non_mutating": not preview_state_changing_commands,
            "advanced_apply_commands_change_state": not advanced_apply_without_state_change,
            "workflow_commands_registered": not workflow_commands_missing,
            "registered_commands_have_execution_path": not execution_unmapped_commands,
            "preview_only_commands_use_dry_run": not preview_without_dry_run,
            "project_scoped_commands_require_project": not project_scoped_without_project_allowed,
            "confirmation_required_commands_reject_unconfirmed": not confirmation_not_enforced,
        },
        "findings": findings,
    }


def build_command_surface_integrity_payload() -> dict[str, Any]:
    expected_group_ids = [str(group["group_id"]) for group in WEB_COMMAND_GROUPS]
    index_path = STATIC_ROOT / "index.html"
    app_path = STATIC_ROOT / "app.js"
    try:
        index_html = index_path.read_text(encoding="utf-8")
        index_readable = True
    except OSError as exc:
        index_html = ""
        index_readable = False
        index_error = str(exc)
    else:
        index_error = ""
    try:
        app_js = app_path.read_text(encoding="utf-8")
        app_readable = True
    except OSError as exc:
        app_js = ""
        app_readable = False
        app_error = str(exc)
    else:
        app_error = ""

    placeholder_group_ids = re.findall(r'data-command-group="([^"]+)"', index_html)
    expected_set = set(expected_group_ids)
    placeholder_set = set(placeholder_group_ids)
    missing_placeholders = sorted(expected_set - placeholder_set)
    unknown_placeholders = sorted(placeholder_set - expected_set)
    duplicate_placeholders = sorted(value for value, count in Counter(placeholder_group_ids).items() if count > 1)
    advanced_shell_present = '<details class="command-advanced">' in index_html
    default_shell_present = 'id="defaultCommandGroup"' in index_html
    required_js_entrypoints = [
        "function commandRegistryAvailable(",
        "function commandGroupKeys(",
        "function commandGroupEntry(",
        "function createCommandButton(",
        "function renderCommandSurface(",
        "function commandResultJudgement(",
        "renderCommandSurface();",
    ]
    missing_js_entrypoints = [entry for entry in required_js_entrypoints if entry not in app_js]
    render_gate_entrypoints = [
        "function commandRegistrySurfaceOk(",
        "function commandSurfaceRenderReady(",
        "function defaultCommandGroupReady(",
        "function commandRegistryMetaText(",
    ]
    missing_render_gate_entrypoints = [entry for entry in render_gate_entrypoints if entry not in app_js]
    deprecated_render_fallback_patterns = [
        "return commandRegistryAvailable() && commandRegistrySurfaceOk();",
    ]
    deprecated_render_fallbacks = [pattern for pattern in deprecated_render_fallback_patterns if pattern in app_js]

    findings: list[dict[str, Any]] = []

    def add_finding(code: str, message: str, *, severity: str = "error", keys: list[str] | None = None) -> None:
        finding: dict[str, Any] = {"code": code, "severity": severity, "message": message}
        if keys:
            finding["keys"] = keys
        findings.append(finding)

    if not index_readable:
        add_finding("index_html_unreadable", f"static index.html is not readable: {index_error}")
    if not app_readable:
        add_finding("app_js_unreadable", f"static app.js is not readable: {app_error}")
    if duplicate_placeholders:
        add_finding("duplicate_command_group_placeholders", "command group placeholders must be unique", keys=duplicate_placeholders)
    if missing_placeholders:
        add_finding("missing_command_group_placeholders", "static HTML must include every command group placeholder", keys=missing_placeholders)
    if unknown_placeholders:
        add_finding("unknown_command_group_placeholders", "static HTML must not include unknown command group placeholders", keys=unknown_placeholders)
    if not default_shell_present:
        add_finding("default_command_shell_missing", "static HTML must include the default command group shell")
    if not advanced_shell_present:
        add_finding("advanced_command_shell_missing", "static HTML must include the collapsed advanced command shell")
    if missing_js_entrypoints:
        add_finding("missing_command_render_entrypoints", "frontend must keep command registry render entrypoints", keys=missing_js_entrypoints)
    if missing_render_gate_entrypoints:
        add_finding(
            "missing_command_render_gate_entrypoints",
            "frontend must keep explicit command render-readiness gate entrypoints",
            keys=missing_render_gate_entrypoints,
        )
    if deprecated_render_fallbacks:
        add_finding(
            "deprecated_command_render_fallback",
            "frontend must not infer render readiness from registry/surface availability alone",
            keys=deprecated_render_fallbacks,
        )

    return {
        "schema": "clutch.web.command_surface_integrity.v1",
        "ok": not findings,
        "summary": {
            "expected_group_count": len(expected_group_ids),
            "placeholder_group_count": len(placeholder_group_ids),
            "missing_group_count": len(missing_placeholders),
            "unknown_group_count": len(unknown_placeholders),
            "duplicate_group_count": len(duplicate_placeholders),
            "required_js_entrypoint_count": len(required_js_entrypoints),
            "missing_js_entrypoint_count": len(missing_js_entrypoints),
            "render_gate_entrypoint_count": len(render_gate_entrypoints),
            "missing_render_gate_entrypoint_count": len(missing_render_gate_entrypoints),
            "deprecated_render_fallback_count": len(deprecated_render_fallbacks),
            "finding_count": len(findings),
        },
        "checks": {
            "index_html_readable": index_readable,
            "app_js_readable": app_readable,
            "command_group_placeholders_complete": not missing_placeholders,
            "command_group_placeholders_known": not unknown_placeholders,
            "command_group_placeholders_unique": not duplicate_placeholders,
            "default_command_shell_present": default_shell_present,
            "advanced_command_shell_present": advanced_shell_present,
            "frontend_render_entrypoints_present": not missing_js_entrypoints,
            "frontend_render_gate_entrypoints_present": not missing_render_gate_entrypoints,
            "frontend_render_readiness_requires_explicit_signal": not deprecated_render_fallbacks,
        },
        "expected_group_ids": expected_group_ids,
        "expected_js_entrypoints": required_js_entrypoints,
        "placeholder_group_ids": placeholder_group_ids,
        "missing_group_ids": missing_placeholders,
        "unknown_group_ids": unknown_placeholders,
        "missing_js_entrypoints": missing_js_entrypoints,
        "missing_render_gate_entrypoints": missing_render_gate_entrypoints,
        "deprecated_render_fallbacks": deprecated_render_fallbacks,
        "findings": findings,
    }


def json_response(payload: Any, status: int = 200) -> tuple[int, bytes, str]:
    return status, (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"), "application/json"


def error_payload(status: int, message: str) -> tuple[int, bytes, str]:
    return json_response({"schema": "clutch.web.error.v1", "ok": False, "error": message}, status)


def static_response(path: Path) -> tuple[int, bytes, str]:
    if not path.exists() or not path.is_file():
        return error_payload(404, "not found")
    content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    if path.suffix == ".js":
        content_type = "text/javascript"
    body = path.read_bytes()
    if path.name == "index.html":
        body = body.replace(b"__CLUTCH_ASSET_VERSION__", WEB_PROCESS_VERSION.encode("utf-8"))
    return 200, body, content_type


def parse_bool(value: str, default: bool) -> bool:
    if value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def command_changes_state(command_key: str) -> bool:
    return command_key in STATE_CHANGING_COMMANDS


def command_requires_confirmation(command_key: str) -> bool:
    return command_key in CONFIRMATION_REQUIRED_COMMANDS


def safe_machine_id(value: str, *, default: str = "future-pc-01") -> str:
    candidate = (value or default).strip()
    if not MACHINE_ID_RE.fullmatch(candidate):
        raise ValueError("invalid new_machine_id: use letters, numbers, dot, underscore, or dash")
    return candidate


def safe_connection_mode(value: str, *, default: str = "auto") -> str:
    candidate = (value or default).strip() or default
    if candidate not in {"auto", "lan", "online"}:
        raise ValueError("invalid connection_mode: expected auto, lan, or online")
    return candidate


def safe_command_argv(
    command_key: str,
    project: str = "",
    *,
    confirmed: bool = False,
    new_machine_id: str = "",
    connection_mode: str = "auto",
) -> list[str]:
    base = [sys.executable, str(CLUTCH_CTL)]
    project_text = project.strip()
    commands: dict[str, list[str]] = {
        "overview": [*base, "overview", "--json"],
        "attention-resolution-plan": [*base, "attention-resolution-plan", "--skip-runtime", "--json"],
        "attention-resolution-fix-preview": [
            *base,
            "attention-resolution-apply",
            "--dry-run",
            "--skip-runtime",
            "--json",
        ],
        "bindings": [*base, "bindings", "--all", "--json"],
        "runtime-check": [*base, "runtime-check", "--json"],
        "worker-status": [*base, "worker-status", "--json"],
        "reboot-readiness": [*base, "reboot-readiness", "--json"],
        "web-console-status": [*base, "web-console-status", "--json"],
        "web-console-browser-smoke": [*base, "web-console-browser-smoke", "--json"],
        "machine-version-state": [*base, "machine-version-state", "--json"],
        "machine-lifecycle-readiness": [*base, "machine-lifecycle-readiness", "--skip-runtime", "--json"],
        "online-identity": [*base, "online-identity", "--json"],
    }
    project_commands: dict[str, list[str]] = {
        "binding-check": [*base, "binding-check", "--project", project_text, "--json"],
        "project-status": [*base, "project-status", "--project", project_text, "--skip-runtime", "--json"],
        "project-attention-resolution-plan": [
            *base,
            "attention-resolution-plan",
            "--project",
            project_text,
            "--skip-runtime",
            "--json",
        ],
        "project-attention-resolution-fix-preview": [
            *base,
            "attention-resolution-apply",
            "--project",
            project_text,
            "--dry-run",
            "--skip-runtime",
            "--json",
        ],
        "project-versioning-readiness": [*base, "project-versioning-readiness", "--project", project_text, "--json"],
        "project-sync-preview": [*base, "project-sync", "--project", project_text, "--dry-run", "--json"],
        "project-history": [*base, "project-history", "--project", project_text, "--limit", "10", "--json"],
        "project-refresh-preview": [
            *base,
            "project-refresh",
            "--project",
            project_text,
            "--dry-run",
            "--skip-runtime",
            "--json",
        ],
        "project-online-publish-preview": [*base, "project-online-publish", "--project", project_text, "--dry-run", "--json"],
        "collab-binding-align-preview": [
            *base,
            "collab-binding-align",
            "--project",
            project_text,
            "--dry-run",
            "--json",
        ],
        "collab-transport-readiness": [
            *base,
            "collab-transport-readiness",
            "--project",
            project_text,
            "--json",
        ],
        "collab-monitor-status": [
            *base,
            "collab-monitor-status",
            "--project",
            project_text,
            "--json",
        ],
        "project-backups": [*base, "project-backups", "--project", project_text, "--limit", "10", "--json"],
        "project-snapshots": [*base, "project-snapshots", "--project", project_text, "--limit", "10", "--json"],
        "project-restore-readiness": [*base, "project-restore-readiness", "--project", project_text, "--json"],
        "project-artifact-pointers": [*base, "project-artifact-pointers", "--project", project_text, "--json"],
        "project-away-report": [*base, "project-away-report", "--project", project_text, "--skip-runtime", "--json"],
        "project-away-cycles": [*base, "project-away-cycles", "--project", project_text, "--limit", "10", "--json"],
        "project-operator-intents": [
            *base,
            "project-operator-intents",
            "--project",
            project_text,
            "--all",
            "--limit",
            "20",
            "--json",
        ],
    }
    state_changing_project_commands: dict[str, list[str]] = {
        "project-sync-apply": [*base, "project-sync", "--project", project_text, "--json"],
        "project-refresh-apply": [
            *base,
            "project-refresh",
            "--project",
            project_text,
            "--skip-runtime",
            "--write",
            "--yes",
            "--json",
        ],
        "project-backup-write": [*base, "project-backup", "--project", project_text, "--json"],
        "project-local-snapshot-write": [
            *base,
            "project-snapshot",
            "--project",
            project_text,
            "--skip-runtime",
            "--write",
            "--json",
        ],
        "project-metadata-fetch-write": [
            *base,
            "project-snapshot-metadata-sync",
            "--project",
            project_text,
            "--direction",
            "fetch",
            "--write",
            "--yes",
            "--json",
        ],
        "collab-binding-align-apply": [
            *base,
            "collab-binding-align",
            "--project",
            project_text,
            "--json",
        ],
        "project-away-prepare-intent": [
            *base,
            "project-operator-intent",
            "--project",
            project_text,
            "--intent-type",
            "away_prepare",
            "--objective",
            "Prepare queued away development. Wait for the operator's next natural-language task before editing.",
            "--allowed-scope",
            "No code edits are authorized by this web action alone.",
            "--verification",
            f"python3 {CLUTCH_CTL} project-away-report --project {project_text} --skip-runtime --json",
            "--stop-condition",
            "The next Codex prompt does not give a concrete objective.",
            "--source-command",
            "project-away-prepare-intent",
            "--write",
            "--json",
        ],
        "project-away-continue-intent": [
            *base,
            "project-operator-intent",
            "--project",
            project_text,
            "--intent-type",
            "away_continue",
            "--objective",
            "Continue queued away development within the active away plan after the operator confirms the objective.",
            "--allowed-scope",
            "Stay inside the active away plan, stop conditions, and approval boundaries.",
            "--verification",
            f"python3 {CLUTCH_CTL} project-away-work --project {project_text} --json",
            "--stop-condition",
            "Away plan is missing, expired, ambiguous, or requires fresh active approval.",
            "--source-command",
            "project-away-continue-intent",
            "--write",
            "--json",
        ],
        "project-collab-delegate-intent": [
            *base,
            "project-operator-intent",
            "--project",
            project_text,
            "--intent-type",
            "collab_delegate",
            "--objective",
            "Prepare a safe worker delegation. Wait for the operator's next natural-language task before sending work to a peer.",
            "--allowed-scope",
            "This web action records intent only; it does not send a collab request by itself.",
            "--allowed-scope",
            "Delegated work must stay inside the selected project and must be safe for text/code/docs inspection or edits.",
            "--verification",
            f"python3 {CLUTCH_CTL} collab-binding-align --project {project_text} --dry-run --json",
            "--verification",
            f"python3 {CLUTCH_CTL} worker-status --json",
            "--stop-condition",
            "No active worker is available or the next Codex prompt does not provide a concrete delegated task.",
            "--stop-condition",
            "The requested work could affect live hardware, credentials, network settings, system services, or requires unclear approval.",
            "--source-command",
            "project-collab-delegate-intent",
            "--write",
            "--json",
        ],
    }
    if command_key in commands:
        return commands[command_key]
    if command_key == "machine-collab-guide" and project_text:
        return [
            *base,
            "machine-collab-guide",
            "--project",
            project_text,
            "--new-machine-id",
            safe_machine_id(new_machine_id),
            "--connection-mode",
            safe_connection_mode(connection_mode),
            "--json",
        ]
    if command_key in project_commands and project_text:
        return project_commands[command_key]
    if command_key in state_changing_project_commands and project_text:
        if command_requires_confirmation(command_key) and not confirmed:
            raise ValueError(f"confirmation_required: {command_key}")
        return state_changing_project_commands[command_key]
    raise ValueError(f"unsupported or incomplete command: {command_key}")


def ui_text(en: str, ko: str = "") -> dict[str, str]:
    return {"en": en, "ko": ko or en}


def ui_metric(label_en: str, value: Any, *, label_ko: str = "", tone: str = "neutral") -> dict[str, Any]:
    return {
        "label": ui_text(label_en, label_ko),
        "value": value,
        "tone": tone,
    }


def ui_row(
    title_en: str,
    detail_en: str = "",
    *,
    title_ko: str = "",
    detail_ko: str = "",
    tone: str = "neutral",
    meta: list[str] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "title": ui_text(title_en, title_ko),
        "detail": ui_text(detail_en, detail_ko),
        "tone": tone,
    }
    if meta:
        row["meta"] = meta
    return row


def ui_block(
    kind: str,
    title_en: str,
    summary_en: str,
    *,
    title_ko: str = "",
    summary_ko: str = "",
    tone: str = "neutral",
    metrics: list[dict[str, Any]] | None = None,
    rows: list[dict[str, Any]] | None = None,
    actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    block: dict[str, Any] = {
        "kind": kind,
        "tone": tone,
        "title": ui_text(title_en, title_ko),
        "summary": ui_text(summary_en, summary_ko),
    }
    if metrics:
        block["metrics"] = metrics
    if rows:
        block["rows"] = rows
    if actions:
        block["actions"] = actions
    return block


def normalize_summary_tone(tone: Any) -> str:
    value = str(tone or "neutral")
    return value if value in {"ok", "warn", "error", "info", "neutral"} else "neutral"


def command_operator_judgement(summary_blocks: list[dict[str, Any]], *, ok: bool) -> dict[str, Any]:
    primary_tone = "neutral"
    if summary_blocks and isinstance(summary_blocks[0], dict):
        primary_tone = normalize_summary_tone(summary_blocks[0].get("tone"))
    source = "summary_blocks" if summary_blocks else "returncode"
    if primary_tone == "error":
        status, tone, label = "blocked", "error", ui_text("Blocked", "차단됨")
    elif primary_tone == "warn":
        status, tone, label = "review", "warn", ui_text("Review", "확인 필요")
    elif primary_tone == "info" and ok:
        status, tone, label = "observe", "info", ui_text("Observe", "관찰")
    elif ok:
        status, tone, label = "complete", "ok", ui_text("Complete", "완료")
    else:
        status, tone, label = "review", "warn", ui_text("Review", "확인 필요")
    return {
        "schema": "clutch.web.command_operator_judgement.v1",
        "status": status,
        "tone": tone,
        "label": label,
        "primary_summary_tone": primary_tone,
        "source": source,
    }


def bool_word(value: Any) -> str:
    return "yes" if bool(value) else "no"


def attention_tone(counts: dict[str, Any], *, ok: bool = True) -> str:
    if Number(counts.get("error_count", 0)) > 0 or Number(counts.get("needs_approval_count", 0)) > 0:
        return "error"
    if not ok or Number(counts.get("warning_count", 0)) > 0:
        return "warn"
    if Number(counts.get("info_count", 0)) > 0:
        return "info"
    return "ok"


def Number(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def status_label_for_tone(tone: str) -> tuple[str, str]:
    if tone == "ok":
        return "Ready", "준비됨"
    if tone == "error":
        return "Blocked", "차단됨"
    if tone == "info":
        return "Observe", "관찰"
    if tone == "warn":
        return "Review", "확인 필요"
    return "Unknown", "알 수 없음"


def localized_status_value(status: str) -> dict[str, str]:
    value = str(status or "").strip()
    labels = {
        "attention_required": ("Attention required", "확인 필요"),
        "confirmation_required": ("Confirmation required", "확인 필요"),
        "ready": ("Ready", "준비됨"),
        "refreshed": ("Refreshed", "새로고침 완료"),
        "review_recommended": ("Review recommended", "검토 권장"),
        "target_machine_required": ("Target machine required", "대상 PC 필요"),
    }
    label = labels.get(value)
    if label:
        return ui_text(label[0], label[1])
    return ui_text(value or "-", value or "-")


def rows_from_findings(items: Any, *, limit: int = 12) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity") or item.get("status") or "info")
        tone = "error" if severity in {"error", "blocking", "blocked"} else "warn" if severity == "warning" else "info"
        title = str(item.get("title") or item.get("kind") or item.get("code") or item.get("name") or "Finding")
        detail = str(item.get("operator_summary") or item.get("message") or item.get("details") or item.get("detail") or "")
        meta = [value for value in [severity, str(item.get("repo_id") or ""), str(item.get("project_id") or "")] if value]
        rows.append(ui_row(title, detail, tone=tone, meta=meta))
    return rows


COMMAND_LIKE_PREFIXES = (
    "mkdir ",
    "python ",
    "python3 ",
    "/usr/bin/python",
    "clutch_ctl.py ",
    "scripts/clutch_ctl.py ",
    "git ",
    "bash ",
    "sh ",
    "systemctl ",
    "service ",
    "./",
)
COMMAND_LIKE_MARKERS = (" scripts/clutch_ctl.py ", " --json", " --dry-run", " --project ")
APPROVAL_SENSITIVE_MARKERS = (
    "--write",
    "--yes",
    " publish",
    " promote",
    " apply",
    " approval",
    " sudo",
    " systemctl",
    " service ",
    " restart",
    " sync-online",
    " uninstall ",
    "uninstall_clutch_machine.sh",
)
SETUP_COMMAND_MARKERS = (
    "mkdir ",
    "git clone ",
    "bootstrap_clutch_machine.sh",
    " set-machine-defaults ",
)


def action_text_is_command(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    return text.startswith(COMMAND_LIKE_PREFIXES) or any(marker in f" {text} " for marker in COMMAND_LIKE_MARKERS)


def action_text_is_approval_sensitive(value: str) -> bool:
    lowered = f" {value.strip().lower()} "
    return any(marker in lowered for marker in APPROVAL_SENSITIVE_MARKERS)


def action_text_is_setup_command(value: str) -> bool:
    lowered = f" {value.strip().lower()} "
    return any(marker in lowered for marker in SETUP_COMMAND_MARKERS)


def row_from_next_action(action: Any) -> dict[str, Any] | None:
    if isinstance(action, str):
        text = action.strip()
        if not text:
            return None
        if action_text_is_command(text):
            approval_sensitive = action_text_is_approval_sensitive(text)
            setup_command = action_text_is_setup_command(text)
            return ui_row(
                text,
                (
                    "Approval or publisher policy may be required before running this command."
                    if approval_sensitive
                    else "Local setup command. Run only on the intended machine and workspace."
                    if setup_command
                    else "Terminal check command. Run from the relevant CLUTCH workspace."
                ),
                detail_ko=(
                    "이 명령은 실행 전 승인 또는 publisher 정책 확인이 필요할 수 있습니다."
                    if approval_sensitive
                    else "로컬 setup 명령입니다. 의도한 머신과 workspace에서만 실행하세요."
                    if setup_command
                    else "터미널 점검 명령입니다. 관련 CLUTCH workspace에서 실행하세요."
                ),
                tone="warn" if approval_sensitive else "info",
                meta=[
                    "terminal command",
                    "policy/approval check" if approval_sensitive else "local setup" if setup_command else "read-only/check",
                ],
            )
        return ui_row(
            text,
            "Operator request or decision. Complete it outside the web command runner when needed.",
            detail_ko="사용자 요청 또는 결정 사항입니다. 필요한 경우 웹 명령 실행기 밖에서 직접 처리하세요.",
            tone="info",
            meta=["operator step"],
        )
    if isinstance(action, dict):
        command = str(action.get("command") or "")
        title = str(action.get("title") or command or action.get("name") or "Next action")
        detail = str(action.get("detail") or action.get("message") or action.get("reason") or "")
        approval_sensitive = bool(action.get("requires_approval") or action.get("approval_required")) or action_text_is_approval_sensitive(command or title)
        is_command = bool(command) or action_text_is_command(title)
        setup_command = action_text_is_setup_command(command or title)
        if not detail:
            if is_command:
                detail = (
                    "Approval or publisher policy may be required before running this command."
                    if approval_sensitive
                    else "Local setup command. Run only on the intended machine and workspace."
                    if setup_command
                    else "Terminal check command. Run from the relevant CLUTCH workspace."
                )
            else:
                detail = "Operator request or decision. Complete it outside the web command runner when needed."
        meta = [str(value) for value in [action.get("kind"), action.get("scope"), "terminal command" if is_command else "operator step"] if value]
        if approval_sensitive:
            meta.append("policy/approval check")
        elif setup_command:
            meta.append("local setup")
        elif is_command:
            meta.append("read-only/check")
        return ui_row(title, detail, tone="warn" if approval_sensitive else "info", meta=meta)
    return None


def rows_from_next_actions(actions: Any, *, limit: int = 8) -> list[dict[str, Any]]:
    if not isinstance(actions, list):
        return []
    rows: list[dict[str, Any]] = []
    for action in actions[:limit]:
        row = row_from_next_action(action)
        if row:
            rows.append(row)
    return rows


def rows_from_approval_boundaries(items: Any, *, limit: int = 8) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in items[:limit]:
        text = str(item or "").strip()
        if not text:
            continue
        rows.append(
            ui_row(
                text,
                "Requires fresh active operator approval before CLUTCH should execute or rely on this action.",
                detail_ko="CLUTCH가 이 작업을 실행하거나 근거로 삼기 전에 사용자의 fresh active approval이 필요합니다.",
                tone="warn",
                meta=["approval boundary", "fresh approval required"],
            )
        )
    return rows


OPERATOR_REQUEST_SAFETY_MARKERS = (
    "do not",
    "sudo",
    "token",
    "credential",
    "password",
    "secret",
    "hardware",
    "approval",
)
OPERATOR_REQUEST_SETUP_MARKERS = (
    "connect",
    "wired lan",
    "switch",
    "same lan",
    "bootstrap",
    "session-entry",
    "machine profile",
)


def row_from_operator_request(request: Any) -> dict[str, Any] | None:
    text = str(request or "").strip()
    if not text:
        return None
    lowered = text.lower()
    safety_boundary = any(marker in lowered for marker in OPERATOR_REQUEST_SAFETY_MARKERS)
    setup_step = any(marker in lowered for marker in OPERATOR_REQUEST_SETUP_MARKERS)
    if safety_boundary:
        detail_en = "Safety or approval boundary. Complete deliberately outside the web command runner."
        detail_ko = "안전 또는 승인 경계입니다. 웹 명령 실행기 밖에서 명확히 처리하세요."
        tone = "warn"
        meta = ["operator step", "approval/safety boundary"]
    elif setup_step:
        detail_en = "Physical or setup step for the operator before CLUTCH automation can rely on this machine."
        detail_ko = "CLUTCH 자동화가 이 머신을 근거로 삼기 전에 사용자가 처리해야 하는 물리/설정 단계입니다."
        tone = "info"
        meta = ["operator step", "physical/setup"]
    else:
        detail_en = "Operator step. Complete outside the web command runner when needed."
        detail_ko = "사용자 단계입니다. 필요한 경우 웹 명령 실행기 밖에서 직접 처리하세요."
        tone = "info"
        meta = ["operator step"]
    return ui_row(text, detail_en, detail_ko=detail_ko, tone=tone, meta=meta)


def rows_from_operator_requests(items: Any, *, limit: int = 8) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in items[:limit]:
        row = row_from_operator_request(item)
        if row:
            rows.append(row)
    return rows


AWAY_BLOCKING_DECISIONS = {"stop", "stop_for_approval", "blocked", "expired"}
AWAY_CONTINUE_DECISIONS = {"", "continue"}
AWAY_REVIEW_STATUSES = {"latest_cycle_not_continue", "scope_review_required", "operator_review_required"}


def away_cycle_needs_review(decision: str, soak_status: str = "") -> bool:
    return decision not in AWAY_CONTINUE_DECISIONS or soak_status in AWAY_REVIEW_STATUSES


def away_cycle_tone(*, ok: bool, decision: str, soak_status: str = "") -> str:
    if decision in AWAY_BLOCKING_DECISIONS:
        return "error"
    if not ok or away_cycle_needs_review(decision, soak_status):
        return "warn"
    return "ok"


def away_cycle_row_tone(decision: str) -> str:
    if decision in AWAY_BLOCKING_DECISIONS:
        return "error"
    if decision not in AWAY_CONTINUE_DECISIONS:
        return "warn"
    return "info"


def build_overview_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    projects = payload.get("projects") if isinstance(payload.get("projects"), dict) else {}
    workers = payload.get("workers") if isinstance(payload.get("workers"), dict) else {}
    counts = payload.get("attention_severity_counts") if isinstance(payload.get("attention_severity_counts"), dict) else {}
    tone = attention_tone(counts, ok=bool(payload.get("ok", False)))
    status_en, status_ko = status_label_for_tone(tone)
    project_count = Number(projects.get("project_count"))
    ok_count = Number(projects.get("ok_count"))
    worker_count = Number(workers.get("worker_count"))
    available_count = Number(workers.get("available_count"))
    attention_count = Number(counts.get("total_count", payload.get("attention_count", 0)))
    blocks = [
        ui_block(
            "judgement",
            "Operator judgement",
            f"{status_en}: {attention_count} attention items across {project_count} projects; {available_count}/{worker_count} workers available.",
            title_ko="운영 판단",
            summary_ko=f"{status_ko}: 프로젝트 {project_count}개 중 주의 항목 {attention_count}개, 워커 {available_count}/{worker_count}개 사용 가능.",
            tone=tone,
            metrics=[
                ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
                ui_metric("Projects", f"{ok_count}/{project_count}", label_ko="프로젝트"),
                ui_metric("Workers", f"{available_count}/{worker_count}", label_ko="워커"),
                ui_metric("Attention", attention_count, label_ko="주의 항목", tone=tone),
            ],
        )
    ]
    finding_rows = rows_from_findings(payload.get("attention_items"))
    if finding_rows:
        blocks.append(
            ui_block(
                "findings",
                "What needs attention",
                "Review these items before trusting the current CLUTCH state.",
                title_ko="확인이 필요한 항목",
                summary_ko="현재 CLUTCH 상태를 신뢰하기 전에 아래 항목을 확인하세요.",
                tone=tone,
                rows=finding_rows,
            )
        )
    return blocks


def build_bindings_summary_blocks(payload: Any) -> list[dict[str, Any]]:
    bindings = payload if isinstance(payload, list) else []
    active = [item for item in bindings if isinstance(item, dict) and str(item.get("status") or "active") == "active"]
    projects = sorted({str(item.get("project_id") or "") for item in active if isinstance(item, dict) and item.get("project_id")})
    machines = sorted({str(item.get("machine_id") or "") for item in active if isinstance(item, dict) and item.get("machine_id")})
    rows = [
        ui_row(
            f"{item.get('project_id', '-')} / {item.get('role', '-')} / {item.get('machine_id', '-')}",
            str(item.get("workspace_path") or item.get("binding_id") or ""),
            tone="info" if str(item.get("role") or "") != "main" else "ok",
            meta=[
                f"status {item.get('status', '-')}",
                f"thread {item.get('thread_id', '-')}",
            ],
        )
        for item in active[:30]
        if isinstance(item, dict)
    ]
    return [
        ui_block(
            "judgement",
            "Binding interpretation",
            f"{len(active)} active bindings are visible across {len(projects)} projects and {len(machines)} machines.",
            title_ko="Binding 해석",
            summary_ko=f"활성 binding {len(active)}개가 프로젝트 {len(projects)}개, 머신 {len(machines)}개에서 보입니다.",
            tone="ok" if active else "info",
            metrics=[
                ui_metric("Active bindings", len(active), label_ko="활성 binding"),
                ui_metric("Projects", len(projects), label_ko="프로젝트"),
                ui_metric("Machines", len(machines), label_ko="머신"),
                ui_metric("Returned records", len(bindings), label_ko="반환 기록"),
            ],
        ),
        ui_block(
            "records",
            "Active records",
            "These records currently count toward project/session role display.",
            title_ko="활성 기록",
            summary_ko="아래 기록은 현재 프로젝트/세션 역할 표시에 반영됩니다.",
            tone="info",
            rows=rows,
        ),
    ]


def build_binding_check_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    action = str(payload.get("action_recommended") or "unknown")
    project_id = str(payload.get("project_id") or "")
    project_bindings = payload.get("project_active_bindings") if isinstance(payload.get("project_active_bindings"), list) else []
    machine_bindings = payload.get("machine_active_bindings") if isinstance(payload.get("machine_active_bindings"), list) else []
    ok_actions = {"already_bound", "available", "ok"}
    tone = "ok" if action in ok_actions else "warn"
    action_summaries = {
        "already_bound": (
            "Current thread is already bound to this project.",
            "현재 thread가 이미 이 프로젝트에 붙어 있습니다.",
        ),
        "available": (
            "No active binding conflict is visible.",
            "보이는 활성 binding 충돌이 없습니다.",
        ),
        "ok": (
            "Binding check is clear.",
            "Binding 점검이 정상입니다.",
        ),
        "takeover_required": (
            "Another active main binding exists; takeover requires an explicit operator decision.",
            "다른 활성 main binding이 있어 takeover는 명시적 판단이 필요합니다.",
        ),
        "confirm_required": (
            "This machine is already bound elsewhere; confirm before changing project binding.",
            "이 머신이 다른 곳에 이미 붙어 있으므로 binding 변경 전 확인이 필요합니다.",
        ),
        "attach_or_worker": (
            "Worker-only bindings exist; choose the intended attach role deliberately.",
            "worker 전용 binding이 있으므로 의도한 attach 역할을 명확히 선택해야 합니다.",
        ),
    }
    summary_en, summary_ko = action_summaries.get(
        action,
        (
            "Review the binding state before attaching.",
            "attach 전에 binding 상태를 확인해야 합니다.",
        ),
    )
    rows = rows_from_findings([
        {
            "severity": "info" if tone == "ok" else "warning",
            "kind": action,
            "message": str(payload.get("reason") or "No conflict reason reported."),
            "project_id": project_id,
        }
    ])
    return [
        ui_block(
            "judgement",
            "Attach judgement",
            f"{summary_en} {len(project_bindings)} active project bindings and {len(machine_bindings)} active bindings on this machine.",
            title_ko="Attach 판단",
            summary_ko=f"{summary_ko} 활성 project binding {len(project_bindings)}개, 이 머신의 활성 binding {len(machine_bindings)}개.",
            tone=tone,
            metrics=[
                ui_metric("Action", action, label_ko="Action", tone=tone),
                ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
                ui_metric("Thread", payload.get("thread_id", "-"), label_ko="Thread"),
                ui_metric("Project bindings", len(project_bindings), label_ko="프로젝트 binding"),
                ui_metric("Machine bindings", len(machine_bindings), label_ko="머신 binding"),
            ],
            rows=rows,
        )
    ]


def build_project_status_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    counts = payload.get("attention_severity_counts") if isinstance(payload.get("attention_severity_counts"), dict) else {}
    tone = attention_tone(counts, ok=bool(payload.get("ok", False)))
    status_en, status_ko = status_label_for_tone(tone)
    sync = payload.get("sync_summary") if isinstance(payload.get("sync_summary"), dict) else {}
    backup = payload.get("online_backup") if isinstance(payload.get("online_backup"), dict) else {}
    bindings = payload.get("bindings") if isinstance(payload.get("bindings"), dict) else {}
    collab = payload.get("collab_readiness") if isinstance(payload.get("collab_readiness"), dict) else {}
    integration = payload.get("integration_profile") if isinstance(payload.get("integration_profile"), dict) else {}
    readiness_profile = str(payload.get("readiness_profile") or "collaborative")
    versioning = payload.get("versioning_readiness") if isinstance(payload.get("versioning_readiness"), dict) else {}
    data_handling = payload.get("data_handling") if isinstance(payload.get("data_handling"), dict) else {}
    authority = versioning.get("version_authority") if isinstance(versioning.get("version_authority"), dict) else {}
    publisher = versioning.get("publisher_context") if isinstance(versioning.get("publisher_context"), dict) else {}
    snapshots = payload.get("snapshots") if isinstance(payload.get("snapshots"), dict) else {}
    snapshot_freshness = snapshots.get("freshness") if isinstance(snapshots.get("freshness"), dict) else {}
    snapshot_metadata = payload.get("snapshot_metadata") if isinstance(payload.get("snapshot_metadata"), dict) else {}
    data_status = str(data_handling.get("status") or "-")
    data_tone = (
        "warn"
        if bool(data_handling.get("requires_artifact_pointer_before_handoff")) or data_status == "needs_artifact_pointers"
        else "ok"
        if data_status in {"artifact_pointers_recorded", "code_metadata_only"}
        else "info"
        if data_status and data_status != "-"
        else "neutral"
    )
    blocks = [
        ui_block(
            "judgement",
            "Project judgement",
            (
                f"{status_en}: {payload.get('operator_summary')}"
                if str(payload.get("operator_summary") or "").strip()
                else f"{status_en}: repo sync {sync.get('required_sync_ready_count', 0)}/{sync.get('required_repo_count', 0)}, online backup {backup.get('enabled_count', 0)}/{backup.get('repo_count', 0)}."
            ),
            title_ko="프로젝트 판단",
            summary_ko=f"{status_ko}: repo 동기화 {sync.get('required_sync_ready_count', 0)}/{sync.get('required_repo_count', 0)}, 온라인 백업 {backup.get('enabled_count', 0)}/{backup.get('repo_count', 0)}.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Integration", f"{integration.get('mode', '-')}/{integration.get('status', '-')}", label_ko="통합"),
                ui_metric("Readiness", readiness_profile, label_ko="Readiness"),
                ui_metric("Publisher", bool_word(publisher.get("is_online_publisher")), label_ko="Publisher"),
                ui_metric("Code source", authority.get("code_source_of_truth", "-"), label_ko="코드 기준"),
                ui_metric("Repro source", authority.get("reproducibility_boundary", versioning.get("reproducibility_source", "-")), label_ko="재현 기준"),
                ui_metric("Repo sync", f"{sync.get('required_sync_ready_count', 0)}/{sync.get('required_repo_count', 0)}", label_ko="Repo 동기화"),
                ui_metric("Current repos", f"{sync.get('up_to_date_required_count', 0)}/{sync.get('required_repo_count', 0)}", label_ko="최신 repo"),
                ui_metric("Blocked repos", sync.get("required_blocked_count", 0), label_ko="차단 repo"),
                ui_metric("Online backup", f"{backup.get('enabled_count', 0)}/{backup.get('repo_count', 0)}", label_ko="온라인 백업"),
                ui_metric("This PC manifests", f"{snapshots.get('snapshot_count', 0)} / {snapshot_freshness.get('status', '-')}", label_ko="이 PC manifest"),
                ui_metric("Promoted metadata", f"{snapshot_metadata.get('valid_metadata_ref_count', 0)}/{snapshot_metadata.get('metadata_ref_count', 0)}", label_ko="승격 metadata"),
                ui_metric("Data handling", data_status, label_ko="데이터 처리", tone=data_tone),
                ui_metric("Artifact pointers", data_handling.get("artifact_pointer_count", 0), label_ko="Artifact pointer", tone=data_tone),
                ui_metric("Main/Sub", f"{bindings.get('project_main_count', bindings.get('main_count', 0))}/{bindings.get('project_worker_count', bindings.get('worker_count', 0))}", label_ko="Main/Sub"),
                ui_metric("Collab", str(collab.get("status") or "-"), label_ko="Collab"),
                ui_metric("Attention", payload.get("attention_count", counts.get("total_count", 0)), label_ko="주의 항목", tone=tone),
                ui_metric("Maintainer advisories", payload.get("maintainer_attention_count", 0), label_ko="Maintainer advisory", tone="info"),
            ],
        )
    ]
    if data_handling:
        data_rows = [
            ui_row(
                "Project data boundary",
                str(data_handling.get("summary") or "Project data policy has no summary."),
                title_ko="프로젝트 데이터 경계",
                detail_ko=str(data_handling.get("summary") or "프로젝트 데이터 정책 요약이 없습니다."),
                tone=data_tone,
                meta=[
                    f"policy {data_handling.get('artifact_pointer_policy_mode', '-')}",
                    f"backup {data_handling.get('backup_boundary', '-')}",
                    f"repro {data_handling.get('reproducibility_boundary', '-')}",
                ],
            ),
            ui_row(
                "Recommended project note",
                str(data_handling.get("recommended_note_path") or data_handling.get("recommended_note_name") or "-"),
                title_ko="권장 프로젝트 노트",
                detail_ko=str(data_handling.get("recommended_note_path") or data_handling.get("recommended_note_name") or "-"),
                tone="ok" if data_handling.get("recommended_note_exists") else "warn",
                meta=[
                    "project-local guidance",
                    f"file {'exists' if data_handling.get('recommended_note_exists') else 'missing'}",
                    str(data_handling.get("path_check_scope") or "current_machine_filesystem"),
                ],
            ),
            ui_row(
                "Artifact manifest",
                str(data_handling.get("recommended_artifact_manifest_path") or "-"),
                title_ko="Artifact manifest",
                detail_ko=str(data_handling.get("recommended_artifact_manifest_path") or "-"),
                tone="ok" if data_handling.get("recommended_artifact_manifest_exists") else "info",
                meta=[
                    f"file {'exists' if data_handling.get('recommended_artifact_manifest_exists') else 'missing'}",
                    "optional until artifact pointers are required",
                    str(data_handling.get("path_check_scope") or "current_machine_filesystem"),
                ],
            ),
            ui_row(
                "Large artifact boundary",
                str(data_handling.get("large_artifact_boundary") or "-"),
                title_ko="대형 artifact 경계",
                detail_ko=str(data_handling.get("large_artifact_boundary") or "-"),
                tone="info",
                meta=["out of git", "record pointer when required"],
            ),
        ]
        data_notes = data_handling.get("notes", []) if isinstance(data_handling.get("notes"), list) else []
        for note in data_notes:
            text = str(note or "").strip()
            if not text:
                continue
            data_rows.append(
                ui_row(
                    "Policy note",
                    text,
                    title_ko="정책 메모",
                    detail_ko=text,
                    tone="info",
                    meta=["artifact policy"],
                )
            )
            if len(data_rows) >= 6:
                break
        blocks.append(
            ui_block(
                "records",
                "Data handling",
                "Project-specific storage and artifact-pointer boundaries.",
                title_ko="데이터 처리",
                summary_ko="프로젝트별 저장 방식과 artifact pointer 경계입니다.",
                tone=data_tone,
                rows=data_rows,
            )
        )
    finding_rows = rows_from_findings(payload.get("attention_items"))
    if finding_rows:
        blocks.append(ui_block("findings", "Findings", "Project-specific issues reported by CLUTCH.", title_ko="점검 항목", summary_ko="CLUTCH가 보고한 프로젝트별 이슈입니다.", tone=tone, rows=finding_rows))
    maintainer_rows = rows_from_findings(payload.get("maintainer_attention_items"))
    if maintainer_rows:
        blocks.append(
            ui_block(
                "records",
                "Maintainer advisories",
                "Advanced CLUTCH maintenance items hidden from normal researcher-facing attention.",
                title_ko="Maintainer advisory",
                summary_ko="일반 연구자 주의항목에서는 숨긴 CLUTCH 유지보수용 고급 항목입니다.",
                tone="info",
                rows=maintainer_rows,
            )
        )
    action_rows = rows_from_next_actions(payload.get("next_actions"))
    action_rows.extend(rows_from_next_actions(data_handling.get("next_actions"), limit=4))
    if action_rows:
        blocks.append(ui_block("next_actions", "Suggested next checks", "Run these follow-up checks before proceeding.", title_ko="권장 다음 확인", summary_ko="계속 진행하기 전에 아래 후속 확인을 실행하세요.", tone="info", actions=action_rows))
    return blocks


def build_versioning_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    blocking = Number(payload.get("blocking_finding_count", summary.get("blocking_finding_count")))
    warnings = Number(payload.get("warning_finding_count", summary.get("warning_finding_count")))
    integration = payload.get("integration_profile") if isinstance(payload.get("integration_profile"), dict) else {}
    publisher = payload.get("publisher_context") if isinstance(payload.get("publisher_context"), dict) else {}
    authority = payload.get("version_authority") if isinstance(payload.get("version_authority"), dict) else {}
    tone = "error" if blocking else "warn" if warnings or not payload.get("ok") else "ok"
    status_en, status_ko = status_label_for_tone(tone)
    repro_source = str(
        authority.get("reproducibility_boundary")
        or summary.get("version_authority_reproducibility_boundary")
        or payload.get("reproducibility_source")
        or summary.get("reproducibility_source")
        or "-"
    )
    code_source = str(authority.get("code_source_of_truth") or summary.get("version_authority_code_source") or "-")
    authority_status = str(authority.get("operator_status") or summary.get("version_authority_status") or "-")
    publication_boundary = (
        authority.get("publication_boundary")
        if isinstance(authority.get("publication_boundary"), dict)
        else {}
    )
    local_manifest_role = str(authority.get("local_snapshot_role") or "-")
    metadata_covered = Number(summary.get("metadata_covered_required_repo_count"))
    metadata_required = Number(summary.get("metadata_required_repo_count"))
    metadata_coverage = f"{metadata_covered}/{metadata_required}" if metadata_required else "-"
    dirty_repos = Number(summary.get("dirty_repo_count", payload.get("dirty_repo_count")))
    needs_publish_repos = Number(summary.get("needs_publish_repo_count", payload.get("needs_publish_repo_count")))
    routine_publish_ready = bool(payload.get("routine_publish_ready"))
    repro_ready = bool(payload.get("reproducibility_ready"))
    local_snapshot_ready = bool(payload.get("local_snapshot_reproducibility_ready", summary.get("local_snapshot_reproducibility_ready")))
    metadata_ready = bool(payload.get("metadata_reproducibility_ready", summary.get("metadata_reproducibility_ready")))
    publication_boundary_status = str(publication_boundary.get("status") or "")
    publication_gate_ready = (
        bool(publication_boundary.get("clean_publication_ready"))
        or publication_boundary_status == "canonical_online_ready"
        if publication_boundary
        else routine_publish_ready and dirty_repos == 0
    )
    publication_gate_status = "ready" if publication_gate_ready else "review"
    authority_status_display = (
        ui_text("Recovery ready, publish review", "복구 준비, publish 확인")
        if authority_status == "recovery_ready_publication_review"
        else ui_text("Canonical online ready", "온라인 기준 준비됨")
        if authority_status == "canonical_online_ready"
        else ui_text("Attention required", "확인 필요")
        if authority_status == "attention_required"
        else authority_status
    )
    publication_gate_display = (
        ui_text("Clean publication ready", "깨끗한 publish 준비됨")
        if bool(publication_boundary.get("clean_publication_ready")) or (publication_gate_ready and not publication_boundary_status)
        else ui_text("Canonical online ready", "온라인 기준 준비됨")
        if publication_boundary_status == "canonical_online_ready"
        else ui_text("Publication review required", "publish 확인 필요")
    )
    publication_gate_tone = "ok" if publication_gate_ready else "warn"
    recovery_tone = "ok" if repro_ready else "warn"
    publication_detail_en = (
        str(publication_boundary.get("operator_summary") or "Clean routine publication can proceed.")
        if publication_gate_ready
        else str(
            publication_boundary.get("operator_summary")
            or "Dirty or unpublished WIP must be preserved or committed before treating online HEAD publication as canonical."
        )
    )
    publication_detail_ko = (
        "깨끗한 일상 publish를 진행할 수 있습니다."
        if bool(publication_boundary.get("clean_publication_ready"))
        else "온라인 기준 repo head와 metadata가 현재 상태를 덮고 있습니다. publish 실행은 설정된 publisher PC가 담당합니다."
        if publication_boundary_status == "canonical_online_ready"
        else "dirty WIP를 보존하거나 커밋해야 clean online publication으로 볼 수 있습니다."
        if dirty_repos
        else "승인된 clean commit publish가 필요합니다."
        if needs_publish_repos
        else "dirty 또는 미공개 WIP는 온라인 HEAD publish를 canonical로 보기 전에 보존하거나 커밋해야 합니다."
    )
    recovery_detail_en = (
        f"Recovery is covered by {repro_source}; this is separate from clean release readiness."
        if repro_ready
        else f"Recovery is not fully covered yet; current source is {repro_source}."
    )
    recovery_detail_ko = (
        f"복구성은 {repro_source} 기준으로 덮여 있으며, clean release 준비와는 별도입니다."
        if repro_ready
        else f"복구성이 아직 완전히 덮이지 않았습니다. 현재 기준은 {repro_source}입니다."
    )
    blocks = [
        ui_block(
            "judgement",
            "Versioning judgement",
            f"{status_en}: source of truth is {code_source}; reproducibility boundary is {repro_source}.",
            title_ko="버전 관리 판단",
            summary_ko=f"{status_ko}: 코드 기준은 {code_source}, 재현 기준은 {repro_source}.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Integration", f"{integration.get('mode', '-')}/{integration.get('status', '-')}", label_ko="통합"),
                ui_metric("Publisher", bool_word(publisher.get("is_online_publisher")), label_ko="Publisher"),
                ui_metric("Authority", authority_status_display, label_ko="Authority", tone="warn" if authority_status == "recovery_ready_publication_review" else "neutral"),
                ui_metric("Code source", code_source, label_ko="코드 기준"),
                ui_metric("Repro source", repro_source, label_ko="재현 기준"),
                ui_metric("Local manifest role", local_manifest_role, label_ko="로컬 manifest 역할"),
                ui_metric("Publication gate", publication_gate_display, label_ko="Publish gate", tone=publication_gate_tone),
                ui_metric("Routine publish", bool_word(payload.get("routine_publish_ready")), label_ko="일상 publish"),
                ui_metric("Reproducibility", bool_word(payload.get("reproducibility_ready")), label_ko="재현성"),
                ui_metric("Snapshot freshness", summary.get("snapshot_freshness", "-"), label_ko="Snapshot freshness"),
                ui_metric("Metadata coverage", metadata_coverage, label_ko="Metadata coverage"),
                ui_metric("Dirty repos", dirty_repos, label_ko="Dirty repo", tone="warn" if dirty_repos else "neutral"),
                ui_metric("Artifact pointers", Number(summary.get("latest_artifact_pointer_count")), label_ko="Artifact pointer"),
                ui_metric("Warnings", warnings, label_ko="경고", tone="warn" if warnings else "neutral"),
                ui_metric("Blockers", blocking, label_ko="차단 항목", tone="error" if blocking else "neutral"),
            ],
        )
    ]
    blocks.append(
        ui_block(
            "records",
            "Release and recovery boundary",
            "Publication readiness and recovery coverage are intentionally shown separately.",
            title_ko="릴리즈와 복구 경계",
            summary_ko="Publish 준비도와 복구 coverage는 의도적으로 분리해 표시합니다.",
            tone="warn" if not publication_gate_ready or not repro_ready else "ok",
            rows=[
                ui_row(
                    "Publication gate",
                    publication_detail_en,
                    title_ko="Publish gate",
                    detail_ko=publication_detail_ko,
                    tone=publication_gate_tone,
                    meta=[
                        f"authority {authority_status}",
                        f"routine publish {bool_word(routine_publish_ready)}",
                        f"dirty repos {dirty_repos}",
                    ],
                ),
                ui_row(
                    "Recovery coverage",
                    recovery_detail_en,
                    title_ko="복구 coverage",
                    detail_ko=recovery_detail_ko,
                    tone=recovery_tone,
                    meta=[
                        f"source {repro_source}",
                        f"local snapshot {bool_word(local_snapshot_ready)}",
                        f"metadata {bool_word(metadata_ready)}",
                    ],
                ),
            ],
        )
    )
    finding_rows = rows_from_findings(payload.get("findings"))
    if finding_rows:
        finding_summary_en = (
            "These findings explain why versioning is not fully ready."
            if tone != "ok"
            else "Informational evidence about supporting local manifests and artifacts."
        )
        finding_summary_ko = (
            "버전 관리가 완전히 준비되지 않은 이유입니다."
            if tone != "ok"
            else "보조 로컬 manifest와 artifact에 대한 정보성 근거입니다."
        )
        blocks.append(ui_block("findings", "Versioning findings", finding_summary_en, title_ko="버전 관리 점검 항목", summary_ko=finding_summary_ko, tone=tone, rows=finding_rows))
    action_rows = rows_from_next_actions(payload.get("next_actions"))
    if action_rows:
        blocks.append(ui_block("next_actions", "Suggested next checks", "Use these actions to close the versioning gap.", title_ko="권장 다음 확인", summary_ko="아래 항목으로 버전 관리 갭을 닫으세요.", tone="info", actions=action_rows))
    return blocks


def build_worker_status_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    workers = payload.get("workers") if isinstance(payload.get("workers"), list) else []
    available = Number(payload.get("available_count"))
    worker_count = Number(payload.get("worker_count", len(workers)))
    stale = Number(payload.get("stale_count"))
    busy = Number(payload.get("busy_count"))
    tone = "warn" if stale or busy or available < worker_count else "ok"
    rows: list[dict[str, Any]] = []
    activity_rows: list[dict[str, Any]] = []
    for worker in workers:
        if not isinstance(worker, dict):
            continue
        health = worker.get("health") if isinstance(worker.get("health"), dict) else {}
        peer = worker.get("peer") if isinstance(worker.get("peer"), dict) else {}
        activity = str(worker.get("activity") or "")
        worker_label = str(worker.get("display_name") or worker.get("host") or "Worker")
        worker_tone = "ok" if activity == "available" and str(health.get("peer_status") or "") == "fresh" else "warn"
        rows.append(
            ui_row(
                worker_label,
                f"{worker.get('host', '-')} -> {peer.get('host', health.get('peer_host', '-'))}",
                tone=worker_tone,
                meta=[
                    f"role {worker.get('role', '-')}",
                    f"activity {activity or '-'}",
                    f"state {health.get('state_status', '-')}",
                    f"link {health.get('peer_status', '-')}",
                ],
            )
        )

        outgoing = worker.get("last_outgoing_request") if isinstance(worker.get("last_outgoing_request"), dict) else {}
        if outgoing and (
            outgoing.get("request_id") or outgoing.get("task_text_preview") or outgoing.get("project_id")
        ):
            approval_required = bool(outgoing.get("approval_required"))
            activity_rows.append(
                ui_row(
                    f"{worker_label}: outgoing request",
                    str(outgoing.get("task_text_preview") or outgoing.get("request_id") or ""),
                    title_ko=f"{worker_label}: 보낸 요청",
                    detail_ko=str(outgoing.get("task_text_preview") or outgoing.get("request_id") or ""),
                    tone="warn" if approval_required else "info",
                    meta=[
                        f"id {outgoing.get('request_id', '-')}",
                        f"kind {outgoing.get('request_kind', '-')}",
                        f"project {outgoing.get('project_id', '-')}",
                        f"approval {bool_word(approval_required)}",
                    ],
                )
            )

        ack = worker.get("last_peer_ack") if isinstance(worker.get("last_peer_ack"), dict) else {}
        if ack and (ack.get("request_id") or ack.get("message") or ack.get("result")):
            result = str(ack.get("result") or "")
            ack_tone = "ok" if result in {"accepted", "queued", "ok"} else "warn" if result else "info"
            activity_rows.append(
                ui_row(
                    f"{worker_label}: peer ACK",
                    str(ack.get("message") or ack.get("result") or ""),
                    title_ko=f"{worker_label}: peer ACK",
                    detail_ko=str(ack.get("message") or ack.get("result") or ""),
                    tone=ack_tone,
                    meta=[
                        f"id {ack.get('request_id', '-')}",
                        f"kind {ack.get('request_kind', '-')}",
                        f"host {ack.get('host', '-')}",
                        f"result {result or '-'}",
                    ],
                )
            )

        for event_key, title_en, title_ko in (
            ("last_peer_result", "peer result", "peer 결과"),
            ("last_task_result", "local task result", "로컬 task 결과"),
        ):
            result_event = worker.get(event_key) if isinstance(worker.get(event_key), dict) else {}
            if not result_event or not (
                result_event.get("request_id")
                or result_event.get("summary")
                or result_event.get("result_status")
                or result_event.get("returncode") is not None
            ):
                continue
            result_status = str(result_event.get("result_status") or "")
            returncode = result_event.get("returncode")
            result_tone = "ok" if result_status == "completed" and returncode in (0, "0") else "warn" if result_status else "info"
            activity_rows.append(
                ui_row(
                    f"{worker_label}: {title_en}",
                    str(result_event.get("summary") or result_status or result_event.get("response_path") or ""),
                    title_ko=f"{worker_label}: {title_ko}",
                    detail_ko=str(result_event.get("summary") or result_status or result_event.get("response_path") or ""),
                    tone=result_tone,
                    meta=[
                        f"id {result_event.get('request_id', '-')}",
                        f"kind {result_event.get('request_kind', '-')}",
                        f"status {result_status or '-'}",
                        f"return {returncode if returncode is not None else '-'}",
                    ],
                )
            )

        peer_status = worker.get("last_peer_status") if isinstance(worker.get("last_peer_status"), dict) else {}
        if peer_status and (peer_status.get("host") or peer_status.get("state") or peer_status.get("active_task")):
            blocked = bool(peer_status.get("blocked") or peer_status.get("awaiting_user_approval"))
            dirty = bool(peer_status.get("git_dirty"))
            peer_status_tone = "warn" if blocked or dirty else "ok" if str(peer_status.get("state") or "") in {"ready", "idle"} else "info"
            activity_rows.append(
                ui_row(
                    f"{worker_label}: peer status",
                    str(peer_status.get("active_task") or peer_status.get("state") or ""),
                    title_ko=f"{worker_label}: peer 상태",
                    detail_ko=str(peer_status.get("active_task") or peer_status.get("state") or ""),
                    tone=peer_status_tone,
                    meta=[
                        f"host {peer_status.get('host', '-')}",
                        f"role {peer_status.get('role', '-')}",
                        f"state {peer_status.get('state', '-')}",
                        f"dirty {bool_word(dirty)}",
                    ],
                )
            )

    blocks = [
        ui_block(
            "judgement",
            "Worker judgement",
            f"{available}/{worker_count} workers are available; stale {stale}, busy {busy}.",
            title_ko="워커 판단",
            summary_ko=f"워커 {available}/{worker_count}개 사용 가능, 오래됨 {stale}, 작업 중 {busy}.",
            tone=tone,
            metrics=[
                ui_metric("Available", available, label_ko="사용 가능"),
                ui_metric("Workers", worker_count, label_ko="워커"),
                ui_metric("Stale", stale, label_ko="오래됨", tone="warn" if stale else "neutral"),
                ui_metric("Busy", busy, label_ko="작업 중", tone="warn" if busy else "neutral"),
            ],
        ),
        ui_block("records", "Worker records", "Per-worker role, activity, and link state.", title_ko="워커 기록", summary_ko="워커별 역할, 활동, 연결 상태입니다.", tone="info", rows=rows),
    ]
    if activity_rows:
        blocks.append(
            ui_block(
                "records",
                "Recent collab activity",
                "Recent outgoing requests, peer ACKs, results, and peer status from the worker state files.",
                title_ko="최근 Collab 활동",
                summary_ko="worker 상태 파일의 최근 보낸 요청, peer ACK, 결과, peer 상태입니다.",
                tone="info",
                rows=activity_rows[:24],
            )
        )
    return blocks


def collab_monitor_actionable_next_actions(actions: Any) -> list[Any]:
    if not isinstance(actions, list):
        return []
    status_only_messages = {
        "collab monitors are running and operator-visible",
    }
    actionable: list[Any] = []
    for action in actions:
        if isinstance(action, str) and action.strip().lower() in status_only_messages:
            continue
        actionable.append(action)
    return actionable


def collab_monitor_visibility_action_row(item: dict[str, Any]) -> dict[str, Any] | None:
    host = str(item.get("host") or "monitor")
    running = bool(item.get("running")) or str(item.get("tmux_status") or "") == "running"
    if running and item.get("attach_command"):
        command = str(item.get("attach_command") or "")
        action_title = f"Attach {host} monitor"
        action_title_ko = f"{host} monitor 붙기"
        action_kind = "attach visible terminal"
    elif item.get("start_visible_command"):
        command = str(item.get("start_visible_command") or "")
        action_title = f"Open {host} monitor"
        action_title_ko = f"{host} monitor 열기"
        action_kind = "start visible monitor"
    else:
        return None
    meta = [
        "operator step",
        "visibility repair",
        action_kind,
        f"host {host}",
        f"scope {item.get('monitor_scope', '-') or '-'}",
        f"session {item.get('session_name', '-') or '-'}",
        f"tmux {item.get('tmux_status', '-') or '-'}",
        f"clients {item.get('attached_client_count', 0)}",
    ]
    ssh_target = str(item.get("ssh_target") or "").strip()
    if ssh_target:
        meta.append(f"ssh {ssh_target}")
    return ui_row(
        action_title,
        command,
        title_ko=action_title_ko,
        detail_ko=command,
        tone="warn",
        meta=meta,
    )


def build_collab_monitor_status_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    monitors = payload.get("monitors") if isinstance(payload.get("monitors"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    monitor_count = Number(payload.get("monitor_count", summary.get("monitor_count", len(monitors))))
    running_count = Number(payload.get("running_count", summary.get("running_count")))
    visible_count = Number(payload.get("operator_visible_count", summary.get("operator_visible_count")))
    missing_count = Number(payload.get("missing_count", summary.get("missing_count")))
    hidden_count = Number(payload.get("hidden_count", summary.get("hidden_count")))
    task_context_count = Number(payload.get("task_context_count", summary.get("task_context_count")))
    active_task_count = Number(payload.get("active_task_count", summary.get("active_task_count")))
    task_history_count = Number(payload.get("task_history_count", summary.get("task_history_count")))
    stale_task_history_count = Number(payload.get("stale_task_history_count", summary.get("stale_task_history_count")))
    selected_project_task_count = Number(payload.get("selected_project_task_count", summary.get("selected_project_task_count")))
    other_project_history_count = Number(payload.get("other_project_history_count", summary.get("other_project_history_count")))
    role_context_status = str(payload.get("role_context_status") or summary.get("role_context_status") or "-")
    binding_role_only_count = Number(payload.get("binding_role_only_count", summary.get("binding_role_only_count")))
    transport_role_differs_count = Number(
        payload.get("transport_role_differs_count", summary.get("transport_role_differs_count"))
    )
    role_mismatch_count = transport_role_differs_count
    tone = "error" if missing_count else "warn" if hidden_count or role_mismatch_count else "ok"
    if missing_count:
        judgement = "One or more collab monitor sessions are missing; restart the visible monitor before relying on collab context."
        judgement_ko = "collab monitor 세션 일부가 없습니다. collab context에 의존하기 전에 보이는 monitor를 다시 시작하세요."
    elif hidden_count:
        judgement = "Collab monitors are running, but at least one is only in the background; attach a visible terminal."
        judgement_ko = "collab monitor는 실행 중이지만 일부가 background 상태입니다. 사용자가 볼 수 있게 terminal을 붙이세요."
    elif role_mismatch_count:
        judgement = "Collab monitors are visible, but a collab transport role differs from the CLUTCH project binding; treat CLUTCH binding as the role source before delegating work."
        judgement_ko = "collab monitor는 보이지만 collab transport role이 CLUTCH project binding과 다릅니다. 작업을 위임하기 전 CLUTCH binding을 역할 기준으로 보세요."
    else:
        judgement = "Main/sub collab monitors are running and operator-visible; continue normal work by instructing the Codex session in natural language."
        judgement_ko = "main/sub collab monitor가 실행 중이고 사용자에게 보입니다. 일반 작업은 Codex 세션에 자연어로 지시하면 됩니다."
    project_role_labels: list[str] = []
    transport_role_labels: list[str] = []
    rows: list[dict[str, Any]] = []
    for item in monitors:
        if not isinstance(item, dict):
            continue
        visible = bool(item.get("operator_visible"))
        running = bool(item.get("running")) or str(item.get("tmux_status") or "") == "running"
        row_tone = "ok" if visible else "warn" if running else "error"
        role = str(item.get("role") or "-")
        binding_role = str(item.get("binding_role") or "")
        transport_role = str(item.get("transport_role") or item.get("role") or "")
        peer_host = str(item.get("peer_host") or "-")
        peer_role = str(item.get("peer_role") or "-")
        peer_binding_role = str(item.get("peer_binding_role") or "")
        peer_role_detail = (
            f"binding {peer_binding_role}, transport {peer_role}"
            if peer_binding_role
            else peer_role
        )
        host = str(item.get("host") or item.get("display_name") or "collab monitor")
        project_role = binding_role
        if project_role and project_role != "-":
            role_label = f"{host}:{project_role}"
            if role_label not in project_role_labels:
                project_role_labels.append(role_label)
        if transport_role and transport_role != "-":
            transport_role_label = f"{host}:{transport_role}"
            if transport_role_label not in transport_role_labels:
                transport_role_labels.append(transport_role_label)
        task = str(item.get("last_request_id") or "-")
        result = str(item.get("last_result_status") or "-")
        recent_task_project_id = str(item.get("recent_task_project_id") or "")
        recent_task_project_scope = str(item.get("recent_task_project_scope") or "none")
        recent_task_status = str(item.get("recent_task_status") or "none")
        recent_task_age_sec = item.get("recent_task_age_sec")
        task_age_meta = f"task age {Number(recent_task_age_sec)}s" if recent_task_age_sec is not None else "task age unknown"
        host_sources = item.get("host_sources") if isinstance(item.get("host_sources"), list) else []
        host_source_summary = ", ".join(str(source) for source in host_sources if str(source).strip()) or "-"
        project_role_for_detail = binding_role or "-"
        runtime_role_for_detail = transport_role or role or "-"
        detail = (
            f"project role {project_role_for_detail}; "
            f"runtime {runtime_role_for_detail} -> {peer_host} ({peer_role_detail}); "
            f"task {task}; result {result}; "
            f"recent project {recent_task_project_id or '-'}"
        )
        rows.append(
            ui_row(
                str(item.get("display_name") or item.get("host") or "collab monitor"),
                detail,
                tone=row_tone,
                meta=[
                    f"session {item.get('session_name', '-')}",
                    f"tmux {item.get('tmux_status', '-')}",
                    f"clients {item.get('attached_client_count', 0)}",
                    f"visible {bool_word(visible)}",
                    f"activity {item.get('activity', '-')}",
                    f"heartbeat {item.get('heartbeat_status', '-')}",
                    f"peer {item.get('peer_status', '-')}",
                    f"peer binding {peer_binding_role or '-'}",
                    f"scope {item.get('monitor_scope', '-')}",
                    f"task scope {recent_task_project_scope}",
                    f"task status {recent_task_status}",
                    task_age_meta,
                    f"source {host_source_summary}",
                ],
            )
        )
    actions = rows_from_next_actions(collab_monitor_actionable_next_actions(payload.get("next_actions")), limit=6)
    for item in monitors:
        if not isinstance(item, dict):
            continue
        if item.get("operator_visible"):
            continue
        action_row = collab_monitor_visibility_action_row(item)
        if action_row:
            actions.append(action_row)
    if role_mismatch_count:
        actions.append(
            ui_row(
                "Review role mismatch in Codex session",
                "Ask the active Codex session to inspect CLUTCH binding versus collab transport role before delegating work.",
                title_ko="Codex 세션에서 역할 mismatch 확인",
                detail_ko="작업을 위임하기 전 활성 Codex 세션에 CLUTCH binding과 collab transport role 차이를 확인하라고 지시하세요.",
                tone="warn",
                meta=["operator protocol", "role context"],
            )
        )
    elif binding_role_only_count:
        actions.append(
            ui_row(
                "Role source is CLUTCH binding",
                "Transport role may be unassigned; use the project binding role shown by CLUTCH before delegating work.",
                title_ko="역할 기준은 CLUTCH binding",
                detail_ko="transport role은 unassigned일 수 있습니다. 작업을 위임하기 전 CLUTCH가 표시한 project binding 역할을 기준으로 보세요.",
                tone="info",
                meta=["operator protocol", "diagnostic transport"],
            )
        )
    if not missing_count and not hidden_count and not role_mismatch_count:
        actions.append(
            ui_row(
                "Use the Codex session for work",
                "Do not add routine Web commands here; give natural-language instructions in the active Codex session.",
                title_ko="작업은 Codex 세션에 지시",
                detail_ko="일상 작업 버튼을 Web에 늘리지 말고, 활성 Codex 세션에 자연어로 지시하세요.",
                tone="ok",
                meta=["operator protocol", "no extra web action"],
            )
        )
    project_role_summary = ", ".join(project_role_labels[:4]) if project_role_labels else "unavailable"
    transport_role_summary = ", ".join(transport_role_labels[:4]) if transport_role_labels else ""
    role_summary = f"Project binding roles: {project_role_summary}"
    role_summary_ko = f"프로젝트 binding 역할: {project_role_summary}"
    if transport_role_summary and transport_role_summary != project_role_summary:
        role_summary = f"{role_summary}; transport roles (diagnostic): {transport_role_summary}"
        role_summary_ko = f"{role_summary_ko}; transport 역할(진단): {transport_role_summary}"
    role_source_note = ""
    role_source_note_ko = ""
    if binding_role_only_count and not transport_role_differs_count:
        role_source_note = " Transport role may be unassigned; CLUTCH binding remains authoritative."
        role_source_note_ko = " transport role은 unassigned일 수 있으며 CLUTCH binding이 기준입니다."
    task_history_note = ""
    task_history_note_ko = ""
    if (
        active_task_count == 0
        and selected_project_task_count == 0
        and other_project_history_count > 0
    ):
        task_history_note = " Task history belongs to another project; do not treat it as active selected-project work."
        task_history_note_ko = " 작업 이력은 다른 프로젝트의 기록이므로 선택한 프로젝트의 활성 작업으로 보지 마세요."
    role_context_rows: list[dict[str, Any]] = []
    for item in monitors:
        if not isinstance(item, dict):
            continue
        binding_role = str(item.get("binding_role") or "-")
        transport_role = str(item.get("transport_role") or item.get("role") or "-")
        role_alignment = str(item.get("role_alignment") or "-")
        host_sources = item.get("host_sources") if isinstance(item.get("host_sources"), list) else []
        host_source_summary = ", ".join(str(source) for source in host_sources if str(source).strip()) or "-"
        if role_alignment == "aligned":
            row_tone = "ok"
        elif role_alignment == "transport_role_differs":
            row_tone = "warn"
        elif role_alignment == "binding_role_only":
            row_tone = "info"
        else:
            row_tone = "neutral"
        role_context_rows.append(
            ui_row(
                str(item.get("display_name") or item.get("host") or "collab monitor"),
                f"binding {binding_role}; transport {transport_role}; alignment {role_alignment}",
                tone=row_tone,
                meta=[
                    f"machine {item.get('machine_id', '-')}",
                    f"binding status {item.get('binding_status', '-') or '-'}",
                    f"thread {item.get('binding_thread_id', '-') or '-'}",
                    f"source {host_source_summary}",
                ],
            )
        )
    blocks = [
        ui_block(
            "judgement",
            "Collab monitor judgement",
            f"{judgement} {role_summary}.{role_source_note}{task_history_note}",
            title_ko="Collab monitor 판단",
            summary_ko=f"{judgement_ko} {role_summary_ko}.{role_source_note_ko}{task_history_note_ko}",
            tone=tone,
            metrics=[
                ui_metric("Visible", visible_count, label_ko="보임", tone="ok" if visible_count == monitor_count else "warn"),
                ui_metric("Running", running_count, label_ko="실행 중"),
                ui_metric("Monitors", monitor_count, label_ko="Monitor"),
                ui_metric("Missing", missing_count, label_ko="없음", tone="error" if missing_count else "neutral"),
                ui_metric("Hidden", hidden_count, label_ko="숨김", tone="warn" if hidden_count else "neutral"),
                ui_metric("Active tasks", active_task_count, label_ko="활성 작업", tone="info" if active_task_count else "neutral"),
                ui_metric("Task history", task_history_count, label_ko="작업 이력", tone="info" if task_history_count else "neutral"),
                ui_metric("Selected tasks", selected_project_task_count, label_ko="선택 작업", tone="info" if selected_project_task_count else "neutral"),
                ui_metric("Other history", other_project_history_count, label_ko="다른 이력", tone="info" if other_project_history_count else "neutral"),
                ui_metric("Stale history", stale_task_history_count, label_ko="오래된 이력", tone="info" if stale_task_history_count else "neutral"),
                ui_metric("Role source", role_context_status, label_ko="역할 기준", tone="warn" if transport_role_differs_count else "info" if binding_role_only_count else "ok"),
            ],
        )
    ]
    if rows:
        blocks.append(
            ui_block(
                "records",
                "Monitor records",
                "Per-host collab monitor visibility, role, heartbeat, and recent task context.",
                title_ko="Monitor 기록",
                summary_ko="Host별 collab monitor 표시 상태, 역할, heartbeat, 최근 task context입니다.",
                tone="info",
                rows=rows,
            )
        )
    if role_context_rows:
        blocks.append(
            ui_block(
                "records",
                "Role source context",
                "CLUTCH project bindings are the project role source; collab transport role is diagnostic runtime state.",
                title_ko="역할 기준 context",
                summary_ko="CLUTCH project binding이 프로젝트 역할 기준이며, collab transport role은 runtime 진단 상태입니다.",
                tone="warn" if transport_role_differs_count else "info",
                rows=role_context_rows,
            )
        )
    if actions:
        actions_summary = (
            "Run these commands on the intended machine when a monitor is missing or only running in the background."
            if missing_count or hidden_count
            else "Monitor visibility is ready, but role context should be reviewed in the active Codex session before delegation."
            if role_mismatch_count
            else "No monitor repair action is needed; CLUTCH binding is the role source, and routine work should continue through the active Codex session."
            if binding_role_only_count
            else "No monitor repair action is needed; routine work should continue through the active Codex session."
        )
        actions_summary_ko = (
            "monitor가 없거나 background로만 실행 중이면 해당 머신에서 아래 명령을 실행하세요."
            if missing_count or hidden_count
            else "monitor 가시성은 준비됐지만 위임 전 활성 Codex 세션에서 역할 context를 확인하세요."
            if role_mismatch_count
            else "monitor 복구 조치는 필요 없습니다. CLUTCH binding이 역할 기준이며 일상 작업은 활성 Codex 세션으로 이어가세요."
            if binding_role_only_count
            else "monitor 복구 조치는 필요 없습니다. 일상 작업은 활성 Codex 세션으로 이어가세요."
        )
        blocks.append(
            ui_block(
                "next_actions",
                "Monitor actions",
                actions_summary,
                title_ko="Monitor 조치",
                summary_ko=actions_summary_ko,
                tone="warn" if missing_count or hidden_count or role_mismatch_count else "ok",
                actions=actions[:10],
            )
        )
    return blocks


def build_records_from_repo_results(repos: Any) -> list[dict[str, Any]]:
    if isinstance(repos, dict):
        iterable = [{"repo_id": key, **value} if isinstance(value, dict) else {"repo_id": key, "status": value} for key, value in repos.items()]
    elif isinstance(repos, list):
        iterable = repos
    else:
        iterable = []
    rows: list[dict[str, Any]] = []
    for repo in iterable[:20]:
        if not isinstance(repo, dict):
            continue
        status = str(repo.get("operator_status") or repo.get("status") or repo.get("sync_status") or repo.get("online_backup_status") or "-")
        legacy_status = str(repo.get("status") or repo.get("sync_status") or repo.get("online_backup_status") or "-")
        operator_tone = str(repo.get("operator_tone") or "")
        tone = (
            "ok"
            if status in {"ok", "ready", "bundled", "would_pull", "would_clone", "enabled", "up_to_date"}
            else "info"
            if status in {
                "sync_preview_ready",
                "fast_forward_available",
                "local_commits_unpublished",
                "remote_machine_execution_required",
                "clone_available",
            }
            else "warn"
            if status != "-"
            else "neutral"
        )
        if operator_tone in {"ok", "info", "warn", "error"}:
            tone = "warn" if operator_tone == "error" else operator_tone
        meta = [f"status {status}", f"ready {repo.get('sync_ready', repo.get('required_sync_ready', '-'))}"]
        if legacy_status and legacy_status != status:
            meta.append(f"raw {legacy_status}")
        rows.append(
            ui_row(
                str(repo.get("repo_id") or repo.get("display_name") or repo.get("path") or "Repo"),
                str(repo.get("path") or repo.get("workspace_path") or repo.get("message") or ""),
                tone=tone,
                meta=meta,
            )
        )
    return rows


def build_project_sync_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    repos = payload.get("repos", payload.get("repo_results", []))
    rows = build_records_from_repo_results(repos)
    required = Number(payload.get("required_repo_count", len(rows)))
    ready = Number(payload.get("sync_ready_required_count", payload.get("required_sync_ready_count")))
    blocked = Number(payload.get("sync_blocked_required_count", payload.get("required_blocked_count")))
    current = Number(payload.get("up_to_date_required_count"))
    fast_forward = Number(payload.get("fast_forward_required_count"))
    attention = Number(payload.get("operator_attention_required_count"))
    dry_run = bool(payload.get("dry_run", True))
    mode_en = "preview" if dry_run else "result"
    mode_ko = "미리보기" if dry_run else "결과"
    change_note_en = "No workspace changes were made." if dry_run else "Workspace sync was executed."
    change_note_ko = "workspace는 변경하지 않았습니다." if dry_run else "workspace 동기화를 실행했습니다."
    tone = "error" if blocked or attention else "warn" if ready < required else "ok"
    return [
        ui_block(
            "judgement",
            f"Sync {mode_en} judgement",
            f"{ready}/{required} required repos are sync-ready; current {current}, fast-forward {fast_forward}, blocked {blocked}. {change_note_en}",
            title_ko=f"Repo 동기화 {mode_ko} 판단",
            summary_ko=f"필수 repo {ready}/{required}개 sync 준비, 최신 {current}, fast-forward {fast_forward}, 차단 {blocked}. {change_note_ko}",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Required repos", required, label_ko="필수 repo"),
                ui_metric("Ready repos", ready, label_ko="준비 repo"),
                ui_metric("Current repos", current, label_ko="최신 repo"),
                ui_metric("Fast-forward", fast_forward, label_ko="Fast-forward"),
                ui_metric("Blocked", blocked, label_ko="차단", tone="error" if blocked else "neutral"),
                ui_metric("Attention", attention, label_ko="주의", tone="warn" if attention else "neutral"),
                ui_metric("Dry run", bool_word(dry_run), label_ko="Dry run"),
            ],
        ),
        ui_block("records", "Repo plan", "Clone/pull readiness by repo.", title_ko="Repo 계획", summary_ko="Repo별 clone/pull 준비도입니다.", tone="info", rows=rows),
    ]


def build_project_refresh_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    steps = payload.get("steps") if isinstance(payload.get("steps"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    metadata = payload.get("metadata_fetch") if isinstance(payload.get("metadata_fetch"), dict) else {}
    sync = payload.get("sync") if isinstance(payload.get("sync"), dict) else {}
    project_status = payload.get("project_status") if isinstance(payload.get("project_status"), dict) else {}
    versioning = payload.get("versioning_readiness") if isinstance(payload.get("versioning_readiness"), dict) else {}
    restore = payload.get("restore_readiness") if isinstance(payload.get("restore_readiness"), dict) else {}
    blocking = Number(payload.get("blocking_step_count", summary.get("blocking_step_count")))
    warnings = Number(payload.get("warning_step_count", summary.get("warning_step_count")))
    refresh_status = str(payload.get("status") or ("review_recommended" if warnings else "ready"))
    confirmation_required = bool(payload.get("confirmation_required"))
    write = bool(payload.get("write"))
    write_requested = bool(payload.get("write_requested", summary.get("write_requested", write)))
    local_write_executed = bool(payload.get("local_write_executed", summary.get("local_write_executed", write and not confirmation_required)))
    target_machine_required = (
        str(payload.get("status") or "") == "target_machine_required"
        or Number(summary.get("target_machine_required_count")) > 0
    )
    tone = "error" if blocking or confirmation_required else "warn" if warnings else "ok"
    status_en, status_ko = status_label_for_tone(tone)
    if refresh_status == "review_recommended":
        status_en, status_ko = "Review recommended", "검토 권장"
    if target_machine_required:
        mode_en = "target machine"
        mode_ko = "대상 PC"
    elif local_write_executed:
        mode_en = "write"
        mode_ko = "쓰기"
    elif confirmation_required or write_requested:
        mode_en = "confirmation"
        mode_ko = "확인 필요"
    else:
        mode_en = "preview"
        mode_ko = "미리보기"
    operator_summary = str(payload.get("operator_summary") or "").strip()
    if confirmation_required:
        operator_summary_ko = "쓰기 확인이 필요합니다."
    elif blocking:
        operator_summary_ko = "차단 항목이 있어 운영자 검토가 필요합니다."
    elif target_machine_required:
        operator_summary_ko = "대상 PC의 로컬 workspace에서 실행해야 합니다."
    elif warnings:
        operator_summary_ko = "차단은 없지만 별도 검토 항목이 남아 있습니다."
    else:
        operator_summary_ko = "차단 항목 없이 완료되었습니다."
    rows: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        step_tone = "error" if step.get("blocking") else "warn" if not step.get("ok") else "ok"
        rows.append(
            ui_row(
                str(step.get("title") or step.get("id") or "Step"),
                str(step.get("summary") or ""),
                tone=step_tone,
                meta=[
                    f"id {step.get('id', '-')}",
                    f"status {step.get('status', '-')}",
                    f"blocking {bool_word(step.get('blocking'))}",
                ],
            )
        )
    blocks = [
        ui_block(
            "judgement",
            "Project refresh judgement",
            (
                f"{status_en}: {operator_summary}"
                if operator_summary
                else f"{status_en}: {mode_en} refresh checked code sync, metadata, versioning, and restore readiness."
            ),
            title_ko="프로젝트 새로고침 판단",
            summary_ko=f"{status_ko}: {operator_summary_ko}",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Status", localized_status_value(refresh_status), label_ko="상태", tone=tone),
                ui_metric("Mode", mode_en, label_ko="모드", tone="warn" if write_requested or target_machine_required else "info"),
                ui_metric(
                    "Write requested",
                    bool_word(write_requested),
                    label_ko="쓰기 요청",
                    tone="warn" if target_machine_required and write_requested else "neutral",
                ),
                ui_metric("Ready", bool_word(payload.get("ready")), label_ko="준비"),
                ui_metric("Blocking", blocking, label_ko="차단", tone="error" if blocking else "neutral"),
                ui_metric("Warnings", warnings, label_ko="경고", tone="warn" if warnings else "neutral"),
                ui_metric(
                    "Target steps",
                    Number(summary.get("target_machine_required_count")),
                    label_ko="대상 PC 단계",
                    tone="warn" if target_machine_required else "neutral",
                ),
                ui_metric(
                    "Repo sync",
                    f"{sync.get('sync_ready_required_count', summary.get('sync_ready_required_count', 0))}/"
                    f"{sync.get('required_repo_count', summary.get('required_repo_count', 0))}",
                    label_ko="Repo 동기화",
                ),
                ui_metric(
                    "Metadata gaps",
                    metadata.get("missing_remote_ref_count", summary.get("metadata_missing_remote_ref_count", 0)),
                    label_ko="Metadata gap",
                    tone="warn"
                    if metadata.get("missing_remote_ref_count", summary.get("metadata_missing_remote_ref_count", 0))
                    else "neutral",
                ),
                ui_metric(
                    "Attention",
                    project_status.get("attention_count", summary.get("project_attention_count", 0)),
                    label_ko="주의 항목",
                    tone="warn" if project_status.get("attention_count", summary.get("project_attention_count", 0)) else "neutral",
                ),
                ui_metric(
                    "Reproducibility",
                    bool_word(versioning.get("reproducibility_ready", summary.get("reproducibility_ready"))),
                    label_ko="재현성",
                ),
                ui_metric("Restore", bool_word(restore.get("ok", summary.get("restore_ready", True))), label_ko="복구"),
            ],
        ),
        ui_block(
            "records",
            "Refresh steps",
            "One operator workflow covering code sync, metadata fetch, versioning, and restore readiness.",
            title_ko="새로고침 단계",
            summary_ko="코드 동기화, metadata fetch, 버전 관리, 복구 준비도를 하나의 운영 workflow로 확인합니다.",
            tone="info",
            rows=rows,
        ),
    ]
    action_rows = rows_from_next_actions(payload.get("next_actions"))
    if action_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Suggested next checks",
                "Use these actions only when they match the current approval boundary.",
                title_ko="권장 다음 확인",
                summary_ko="현재 승인 경계에 맞는 경우에만 아래 항목을 실행하세요.",
                tone="info",
                actions=action_rows,
            )
        )
    return blocks


def build_publish_preview_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    authority = payload.get("publish_authority") if isinstance(payload.get("publish_authority"), dict) else {}
    repos = payload.get("repo_results", payload.get("repos", []))
    rows = build_records_from_repo_results(repos)
    authority_ok = bool(authority.get("ok", payload.get("publish_authority_ok", payload.get("ok", False))))
    blocked_count = Number(payload.get("blocked_repo_count", payload.get("blocking_finding_count", 0)))
    tone = "error" if blocked_count else "ok" if authority_ok else "warn"
    return [
        ui_block(
            "judgement",
            "Publish preview judgement",
            f"Authority {'passes' if authority_ok else 'needs review'}; blocked repos {blocked_count}. This is still a dry run.",
            title_ko="Publish 미리보기 판단",
            summary_ko=f"권한 {'통과' if authority_ok else '확인 필요'}, 차단 repo {blocked_count}. 이 명령은 dry run입니다.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Authority", bool_word(authority_ok), label_ko="권한"),
                ui_metric("Blocked repos", blocked_count, label_ko="차단 repo", tone="error" if blocked_count else "neutral"),
                ui_metric("Dry run", bool_word(payload.get("dry_run", True)), label_ko="Dry run"),
            ],
        ),
        ui_block("records", "Repo publication plan", "What would be published by repo.", title_ko="Repo publish 계획", summary_ko="Repo별 publish 예정 내용입니다.", tone="info", rows=rows),
    ]


def build_collab_align_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    warnings = Number(payload.get("warning_count"))
    tone = "warn" if warnings else "ok"
    rows = [
        ui_row(
            f"{item.get('peer_machine_id') or item.get('peer_host') or '-'} / {item.get('peer_role') or '-'}",
            str(item.get("message") or ""),
            tone="warn" if str(item.get("status") or "") == "unbound" else "ok",
            meta=[f"project {item.get('project_id', '-')}", f"status {item.get('status', '-')}", f"link {item.get('peer_status', '-')}"],
        )
        for item in items[:20]
        if isinstance(item, dict)
    ]
    blocks = [
        ui_block(
            "judgement",
            "Collab alignment judgement",
            f"{payload.get('aligned_count', 0)} links aligned, {payload.get('created_count', 0)} would be created, warnings {warnings}.",
            title_ko="Collab 정렬 판단",
            summary_ko=f"연결 {payload.get('aligned_count', 0)}개 정렬, {payload.get('created_count', 0)}개 생성 예정, 경고 {warnings}.",
            tone=tone,
            metrics=[
                ui_metric("Aligned", payload.get("aligned_count", 0), label_ko="정렬됨"),
                ui_metric("Would create", payload.get("created_count", 0), label_ko="생성 예정"),
                ui_metric("Warnings", warnings, label_ko="경고", tone="warn" if warnings else "neutral"),
                ui_metric("Dry run", bool_word(payload.get("dry_run", True)), label_ko="Dry run"),
            ],
        ),
        ui_block("records", "Link records", "Live collab links compared against project bindings.", title_ko="연결 기록", summary_ko="실시간 collab 연결과 프로젝트 binding 비교 결과입니다.", tone="info", rows=rows),
    ]
    action_rows = rows_from_next_actions(payload.get("next_actions"), limit=6)
    if action_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Monitor and worker follow-up",
                "Use these read-only checks before applying any collab binding change.",
                title_ko="Monitor 및 워커 후속 확인",
                summary_ko="collab binding 변경을 적용하기 전에 아래 읽기 전용 확인을 먼저 사용하세요.",
                tone="warn" if warnings else "info",
                actions=action_rows,
            )
        )
    return blocks


def build_collab_transport_readiness_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    repo = payload.get("repo") if isinstance(payload.get("repo"), dict) else {}
    manifest = payload.get("manifest") if isinstance(payload.get("manifest"), dict) else {}
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    blocking = Number(summary.get("blocking_count"))
    warnings = Number(summary.get("warning_count"))
    tone = "error" if blocking else "warn" if warnings or not payload.get("transport_ready") else "ok"
    status_en, status_ko = status_label_for_tone(tone)
    tags = summary.get("exact_tags") if isinstance(summary.get("exact_tags"), list) else []
    tag_labels = [str(tag) for tag in tags if str(tag).strip()]
    if len(tag_labels) > 3:
        exact_tag_summary = f"{', '.join(tag_labels[:3])} (+{len(tag_labels) - 3} more)"
    elif tag_labels:
        exact_tag_summary = ", ".join(tag_labels)
    else:
        exact_tag_summary = "-"
    release_surface = payload.get("release_surface") if isinstance(payload.get("release_surface"), list) else []
    namespaces = payload.get("namespace_previews") if isinstance(payload.get("namespace_previews"), list) else []
    surface_rows = [
        ui_row(
            str(item.get("path") or "release surface"),
            str(item.get("kind") or ""),
            tone="ok" if item.get("exists") else "warn",
            meta=[f"exists {bool_word(item.get('exists'))}"],
        )
        for item in release_surface[:16]
        if isinstance(item, dict)
    ]
    namespace_rows = [
        ui_row(
            str(item.get("namespace") or "namespace"),
            f"{item.get('from_machine_id', '-')} -> {item.get('to_machine_id', '-')}",
            tone="info",
        )
        for item in namespaces[:12]
        if isinstance(item, dict)
    ]
    policy_rows: list[dict[str, Any]] = []
    for note in policy.get("notes", []) if isinstance(policy.get("notes"), list) else []:
        if not str(note).strip():
            continue
        policy_rows.append(
            ui_row(
                "Policy note",
                str(note),
                title_ko="정책 메모",
                detail_ko=str(note),
                tone="info",
            )
        )
    for title, title_ko, value in [
        ("Release tag policy", "Release tag 정책", policy.get("release_tag_policy") or manifest.get("release_tag_policy")),
        ("Runtime namespace", "Runtime namespace", policy.get("runtime_namespace_template") or manifest.get("runtime_namespace_template")),
        ("Legacy runtime", "Legacy runtime", policy.get("legacy_runtime_compatibility") or manifest.get("legacy_runtime_compatibility")),
    ]:
        if not value:
            continue
        policy_rows.append(
            ui_row(
                title,
                str(value),
                title_ko=title_ko,
                detail_ko=str(value),
                tone="info",
                meta=["operator boundary"],
            )
        )
    blocks = [
        ui_block(
            "judgement",
            "Collab transport readiness",
            f"{status_en}: {repo.get('repo_name', 'collab transport')} at {repo.get('head_short', '-')}; protocol {summary.get('protocol_version', manifest.get('protocol_version', '-'))}.",
            title_ko="Collab 전송 준비도",
            summary_ko=f"{status_ko}: {repo.get('repo_name', 'collab transport')} HEAD {repo.get('head_short', '-')}, protocol {summary.get('protocol_version', manifest.get('protocol_version', '-'))}.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Ready", bool_word(payload.get("transport_ready")), label_ko="준비"),
                ui_metric("Policy source", payload.get("policy_source", "-"), label_ko="정책 출처"),
                ui_metric("Protocol", summary.get("protocol_version", manifest.get("protocol_version", "-")), label_ko="Protocol"),
                ui_metric("Latest tag", summary.get("latest_tag", "-"), label_ko="최신 tag"),
                ui_metric("Exact tags", exact_tag_summary, label_ko="정확 tag"),
                ui_metric("Release surface", f"{summary.get('release_surface_required_count', 0) - summary.get('release_surface_missing_count', 0)}/{summary.get('release_surface_required_count', 0)}", label_ko="Release surface"),
                ui_metric("Runtime state", f"{summary.get('runtime_state_present_count', 0)}/{summary.get('runtime_state_known_count', 0)}", label_ko="Runtime 상태"),
                ui_metric("Namespaces", summary.get("namespace_preview_count", len(namespaces)), label_ko="Namespace"),
                ui_metric("Warnings", warnings, label_ko="경고", tone="warn" if warnings else "neutral"),
                ui_metric("Blockers", blocking, label_ko="차단", tone="error" if blocking else "neutral"),
            ],
        )
    ]
    finding_rows = rows_from_findings(payload.get("findings"))
    if finding_rows:
        blocks.append(
            ui_block(
                "findings",
                "Readiness findings",
                "Transport notes and warnings returned by CLUTCH.",
                title_ko="준비도 점검 항목",
                summary_ko="CLUTCH가 반환한 transport 참고 사항과 경고입니다.",
                tone=tone,
                rows=finding_rows,
            )
        )
    if namespace_rows:
        blocks.append(
            ui_block(
                "records",
                "Machine-id namespaces",
                "Previewed runtime namespaces for non-hardcoded collab channels.",
                title_ko="Machine-id namespace",
                summary_ko="하드코딩되지 않은 collab channel에 사용할 runtime namespace 미리보기입니다.",
                tone="info",
                rows=namespace_rows,
            )
        )
    if policy_rows:
        blocks.append(
            ui_block(
                "records",
                "Policy boundaries",
                "CLUTCH keeps role, binding, and release authority policy separate from the transport implementation repo.",
                title_ko="정책 경계",
                summary_ko="CLUTCH는 역할, binding, release 권한 정책을 transport 구현 repo와 분리해서 관리합니다.",
                tone="info",
                rows=policy_rows[:12],
            )
        )
    if surface_rows:
        blocks.append(
            ui_block(
                "records",
                "Release surface",
                "Files that define the releasable collab transport surface.",
                title_ko="Release surface",
                summary_ko="릴리즈 가능한 collab transport 표면을 구성하는 파일입니다.",
                tone="info",
                rows=surface_rows,
            )
        )
    action_rows = rows_from_next_actions(payload.get("next_actions"))
    if action_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Suggested next checks",
                "Follow these before changing collab runtime topology.",
                title_ko="권장 다음 확인",
                summary_ko="collab runtime topology를 바꾸기 전에 아래 확인을 사용하세요.",
                tone="info",
                actions=action_rows,
            )
        )
    return blocks


def build_project_history_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    durable = payload.get("durable_docs") if isinstance(payload.get("durable_docs"), dict) else {}
    docs = payload.get("docs") if isinstance(payload.get("docs"), list) else []
    repos = payload.get("repos") if isinstance(payload.get("repos"), list) else []
    status = str(payload.get("status") or "")
    target_machine_required = status == "target_machine_required" or Number(summary.get("target_machine_required_count")) > 0
    history_ready = bool(payload.get("history_ready"))
    tone = "warn" if target_machine_required or not history_ready else "ok" if payload.get("ok") else "error"
    status_en, status_ko = status_label_for_tone(tone)
    operator_summary = str(payload.get("operator_summary") or "").strip()
    if target_machine_required:
        summary_ko = "대상 PC의 로컬 workspace에서 실행해야 프로젝트 이력을 정확히 볼 수 있습니다."
    elif history_ready:
        summary_ko = "프로젝트 이력을 문서와 복구 근거로 검토할 수 있습니다."
    else:
        summary_ko = "프로젝트 이력 근거를 더 확인해야 합니다."

    doc_rows: list[dict[str, Any]] = []
    for item in docs[:10]:
        if not isinstance(item, dict):
            continue
        exists = bool(item.get("exists"))
        recommended = bool(item.get("recommended"))
        doc_rows.append(
            ui_row(
                str(item.get("kind") or "doc"),
                str(item.get("path") or ""),
                tone="ok" if exists else "warn" if recommended else "neutral",
                meta=[
                    "present" if exists else "missing",
                    "recommended" if recommended else "",
                    str(item.get("source") or ""),
                    f"bytes {item.get('byte_count')}" if item.get("byte_count") is not None else "",
                ],
            )
        )

    repo_rows: list[dict[str, Any]] = []
    for repo in repos[:6]:
        if not isinstance(repo, dict):
            continue
        dirty_count = Number(repo.get("dirty_file_count"))
        target_required = bool(repo.get("target_machine_required"))
        commits = repo.get("recent_commits") if isinstance(repo.get("recent_commits"), list) else []
        latest_commit = commits[0] if commits and isinstance(commits[0], dict) else {}
        repo_rows.append(
            ui_row(
                str(repo.get("repo_id") or repo.get("display_name") or "repo"),
                str(latest_commit.get("subject") or repo.get("path") or ""),
                tone="warn" if dirty_count or target_required else "ok",
                meta=[
                    f"head {repo.get('head', '')}" if repo.get("head") else "",
                    f"branch {repo.get('branch', '')}" if repo.get("branch") else "",
                    f"dirty files {dirty_count}" if dirty_count else "",
                    "target machine required" if target_required else "",
                ],
            )
        )

    blocks = [
        ui_block(
            "judgement",
            "Project history judgement",
            f"{status_en}: {operator_summary}" if operator_summary else f"{status_en}: project history evidence was indexed.",
            title_ko="프로젝트 이력 판단",
            summary_ko=f"{status_ko}: {summary_ko}",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Status", status or "-", label_ko="상태", tone=tone),
                ui_metric("History ready", bool_word(history_ready), label_ko="이력 준비"),
                ui_metric("Durable docs", summary.get("durable_context_doc_count", durable.get("present_count", 0)), label_ko="지속 문서"),
                ui_metric(
                    "Project history docs",
                    f"{summary.get('present_project_history_doc_count', payload.get('present_project_history_doc_count', 0))}/"
                    f"{summary.get('project_history_doc_count', payload.get('project_history_doc_count', 0))}",
                    label_ko="History 문서",
                ),
                ui_metric("Repos", summary.get("repo_count", payload.get("repo_count", 0)), label_ko="Repo"),
                ui_metric("Backups", summary.get("backup_snapshot_count", 0), label_ko="Backup"),
                ui_metric("Snapshots", summary.get("local_snapshot_count", 0), label_ko="Snapshot"),
                ui_metric("Metadata refs", summary.get("valid_metadata_ref_count", 0), label_ko="Metadata ref"),
                ui_metric("Away checkpoints", summary.get("away_checkpoint_count", payload.get("away_checkpoint_count", 0)), label_ko="Away checkpoint"),
                ui_metric("Intents", summary.get("operator_intent_count", payload.get("operator_intent_count", 0)), label_ko="Intent"),
            ],
        )
    ]
    if doc_rows:
        blocks.append(
            ui_block(
                "records",
                "Durable documents",
                "Project memory documents and recommended ledgers.",
                title_ko="지속 문서",
                summary_ko="프로젝트 memory 문서와 권장 ledger입니다.",
                tone="info",
                rows=doc_rows,
            )
        )
    if repo_rows:
        blocks.append(
            ui_block(
                "records",
                "Git evidence",
                "Configured repos and recent commit evidence.",
                title_ko="Git 근거",
                summary_ko="설정된 repo와 최근 commit 근거입니다.",
                tone="info",
                rows=repo_rows,
            )
        )
    action_rows = rows_from_next_actions(payload.get("next_actions"), limit=6)
    if action_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Suggested next checks",
                "Use these follow-up checks when history evidence is incomplete.",
                title_ko="권장 다음 확인",
                summary_ko="이력 근거가 부족할 때 아래 후속 확인을 사용하세요.",
                tone="info",
                actions=action_rows,
            )
        )
    return blocks


def build_machine_collab_guide_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    peer_endpoints = payload.get("peer_endpoints") if isinstance(payload.get("peer_endpoints"), list) else []
    namespaces = payload.get("namespace_previews") if isinstance(payload.get("namespace_previews"), list) else []
    network_targets = payload.get("network_targets") if isinstance(payload.get("network_targets"), list) else []
    requests = payload.get("operator_requests") if isinstance(payload.get("operator_requests"), list) else []
    release_onboarding = payload.get("release_onboarding") if isinstance(payload.get("release_onboarding"), dict) else {}
    bootstrap = payload.get("bootstrap_commands") if isinstance(payload.get("bootstrap_commands"), list) else []
    transport_setup = payload.get("transport_setup_commands") if isinstance(payload.get("transport_setup_commands"), list) else []
    post_bootstrap = payload.get("post_bootstrap_commands") if isinstance(payload.get("post_bootstrap_commands"), list) else []
    collab_setup = payload.get("collab_setup_commands") if isinstance(payload.get("collab_setup_commands"), list) else []
    verification = payload.get("verification_commands") if isinstance(payload.get("verification_commands"), list) else []
    release_required = bool(release_onboarding.get("release_required_before_unattended_new_pc"))
    release_publication_allowed = release_onboarding.get("publication_allowed_now")
    guide_status = str(release_onboarding.get("status") or "guide_only")
    tone = "warn" if release_required and release_publication_allowed is False else "info" if not payload.get("new_machine_known") else "ok"
    peer_rows = [
        ui_row(
            str(item.get("machine_id") or item.get("display_name") or "peer"),
            str(item.get("coord_endpoint") or item.get("lan_ip") or ""),
            tone="ok" if item.get("known") else "info",
            meta=[value for value in [str(item.get("display_name") or ""), f"port {item.get('coord_port', '-')}", str(item.get("collab_host") or "")] if value],
        )
        for item in peer_endpoints[:12]
        if isinstance(item, dict)
    ]
    namespace_rows = [
        ui_row(
            str(item.get("namespace") or "namespace"),
            f"{item.get('from_machine_id', '-')} -> {item.get('to_machine_id', '-')}",
            tone="info",
        )
        for item in namespaces[:12]
        if isinstance(item, dict)
    ]
    command_rows = rows_from_next_actions([*bootstrap, *transport_setup, *verification], limit=18)
    post_bootstrap_rows = rows_from_next_actions(post_bootstrap, limit=8)
    collab_setup_rows = rows_from_next_actions(collab_setup, limit=8)
    request_rows = rows_from_operator_requests(requests, limit=8)
    release_rows: list[dict[str, Any]] = []
    for item in release_onboarding.get("required_items", []) if isinstance(release_onboarding.get("required_items"), list) else []:
        if isinstance(item, dict):
            name = str(item.get("name") or "Release item")
            detail = str(item.get("detail") or "")
            status = str(item.get("status") or "-")
        else:
            name = str(item)
            detail = ""
            status = "required_for_release"
        release_rows.append(
            ui_row(
                name,
                detail,
                tone="warn" if status == "required_for_release" else "info",
                meta=[f"status {status}", "release checklist"],
            )
        )
    boundary_rows: list[dict[str, Any]] = []
    if release_onboarding:
        boundary_rows.append(
            ui_row(
                "Guide only",
                "This command prepares onboarding guidance; it does not publish release tags, create GitHub releases, or register the new PC.",
                title_ko="가이드 전용",
                detail_ko="이 명령은 onboarding 가이드를 준비할 뿐 release tag publish, GitHub Release 생성, 새 PC 등록을 수행하지 않습니다.",
                tone="warn" if release_publication_allowed is False else "info",
                meta=[f"status {guide_status}", "no state change"],
            )
        )
    if release_required:
        boundary_rows.append(
            ui_row(
                "Release required before unattended onboarding",
                "A release tag and manifest should exist before a new PC joins unattended or repeatably.",
                title_ko="무인 onboarding 전 release 필요",
                detail_ko="새 PC가 무인 또는 반복 가능한 방식으로 합류하려면 release tag와 manifest가 먼저 있어야 합니다.",
                tone="warn",
                meta=["release gate", f"publish now {bool_word(release_publication_allowed)}"],
            )
        )
    registry_preview = payload.get("registry_update_preview") if isinstance(payload.get("registry_update_preview"), dict) else {}
    registry_machine = registry_preview.get("machine") if isinstance(registry_preview.get("machine"), dict) else {}
    if registry_machine:
        boundary_rows.append(
            ui_row(
                "Registry update preview",
                f"Prepared preview for {registry_machine.get('machine_id', payload.get('new_machine_id', '-'))}; operator review is required before registry changes.",
                title_ko="Registry 변경 미리보기",
                detail_ko=f"{registry_machine.get('machine_id', payload.get('new_machine_id', '-'))} 등록 미리보기만 준비됐습니다. registry 변경 전 사용자 검토가 필요합니다.",
                tone="info",
                meta=[str(registry_machine.get("status") or "pending_profile_review"), "preview only"],
            )
        )
    blocks = [
        ui_block(
            "judgement",
            "New PC collab guide",
            f"Guide for {payload.get('new_machine_id', '-')}: requested mode {payload.get('connection_mode', '-')}, effective mode {payload.get('effective_connection_mode', '-')}. "
            + ("Guide only; unattended onboarding still needs the release checklist." if release_required and release_publication_allowed is False else ""),
            title_ko="새 PC collab 가이드",
            summary_ko=f"{payload.get('new_machine_id', '-')} 가이드: 요청 mode {payload.get('connection_mode', '-')}, 실제 mode {payload.get('effective_connection_mode', '-')}. "
            + ("가이드 전용이며 무인 onboarding에는 release checklist가 더 필요합니다." if release_required and release_publication_allowed is False else ""),
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("New machine", payload.get("new_machine_id", "-"), label_ko="새 머신"),
                ui_metric("Known", bool_word(payload.get("new_machine_known")), label_ko="등록됨"),
                ui_metric("Mode", payload.get("effective_connection_mode", payload.get("connection_mode", "-")), label_ko="Mode"),
                ui_metric("Guide status", guide_status, label_ko="가이드 상태"),
                ui_metric("Release required", bool_word(release_required), label_ko="Release 필요", tone="warn" if release_required else "ok"),
                ui_metric("Publish now", bool_word(release_publication_allowed), label_ko="지금 publish", tone="warn" if release_publication_allowed is False else "ok"),
                ui_metric("Peers", len(peer_endpoints), label_ko="Peer"),
                ui_metric("Network targets", len(network_targets), label_ko="Network target"),
                ui_metric("Namespaces", len(namespaces), label_ko="Namespace"),
                ui_metric("Policy source", payload.get("collab_transport_policy_source", "-"), label_ko="정책 출처"),
            ],
        )
    ]
    if boundary_rows:
        blocks.append(
            ui_block(
                "findings",
                "Onboarding boundary",
                "What this guide can prepare now, and what still needs operator or release approval.",
                title_ko="Onboarding 경계",
                summary_ko="이 가이드가 지금 준비할 수 있는 것과 사용자 또는 release 승인이 더 필요한 항목입니다.",
                tone="warn" if any(row.get("tone") == "warn" for row in boundary_rows) else "info",
                rows=boundary_rows,
            )
        )
    if release_rows:
        blocks.append(
            ui_block(
                "records",
                "Release onboarding checklist",
                "GitHub Release or release-note items that should exist before unattended new-PC onboarding. This guide does not publish them.",
                title_ko="Release onboarding 체크리스트",
                summary_ko="새 PC 자동 합류 전에 GitHub Release 또는 release note에 있어야 할 항목입니다. 이 가이드는 이를 publish하지 않습니다.",
                tone="warn" if release_onboarding.get("publication_allowed_now") is False else "info",
                rows=release_rows,
            )
        )
    if request_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Operator requests",
                "Physical and approval-sensitive steps the operator should perform.",
                title_ko="사용자 요청 사항",
                summary_ko="사용자가 직접 처리해야 하는 물리 연결 및 승인 민감 단계입니다.",
                tone="info",
                actions=request_rows,
            )
        )
    if command_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Bootstrap and verification commands",
                "Commands for installing, configuring, and verifying the new PC.",
                title_ko="Bootstrap 및 검증 명령",
                summary_ko="새 PC 설치, 설정, 검증에 사용할 명령입니다.",
                tone="info",
                actions=command_rows,
            )
        )
    if post_bootstrap_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Post-bootstrap checks",
                "Run these on the new PC after the bootstrap command completes.",
                title_ko="Bootstrap 이후 확인",
                summary_ko="Bootstrap 명령이 끝난 뒤 새 PC에서 실행할 확인입니다.",
                tone="info",
                actions=post_bootstrap_rows,
            )
        )
    if collab_setup_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Collab setup dry-runs",
                "Read-only topology and role-transition previews before enabling real collaboration.",
                title_ko="Collab 설정 dry-run",
                summary_ko="실제 협업을 켜기 전에 topology와 role transition을 읽기 전용으로 확인합니다.",
                tone="info",
                actions=collab_setup_rows,
            )
        )
    if peer_rows:
        blocks.append(
            ui_block(
                "records",
                "Known peer endpoints",
                "Existing CLUTCH machines the new PC can use as peers.",
                title_ko="기존 peer endpoint",
                summary_ko="새 PC가 peer로 사용할 수 있는 기존 CLUTCH 머신입니다.",
                tone="info",
                rows=peer_rows,
            )
        )
    if namespace_rows:
        blocks.append(
            ui_block(
                "records",
                "Machine-id namespaces",
                "Namespaces CLUTCH expects for future non-hardcoded collab channels.",
                title_ko="Machine-id namespace",
                summary_ko="향후 하드코딩 없는 collab channel에 사용할 namespace입니다.",
                tone="info",
                rows=namespace_rows,
            )
        )
    return blocks


def build_runtime_check_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    required_count = Number(payload.get("required_check_count"))
    failed_required = Number(payload.get("failed_required_count"))
    optional_failed = sum(
        1
        for item in checks
        if isinstance(item, dict) and not item.get("required") and not item.get("ok")
    )
    total_failed = sum(1 for item in checks if isinstance(item, dict) and not item.get("ok"))
    tone = "warn" if failed_required or not bool(payload.get("ok", False)) else "info" if optional_failed else "ok"
    rows = []
    for item in checks[:18]:
        if not isinstance(item, dict):
            continue
        ok = bool(item.get("ok"))
        required = bool(item.get("required"))
        row_tone = "ok" if ok else "warn" if required else "info"
        details = str(item.get("details") or "").strip()
        status = str(item.get("status") or "-")
        recovery = str(item.get("recovery_command") or "").strip()
        meta = ["required" if required else "optional", f"status {status}"]
        if recovery and not ok:
            meta.append(f"recovery {recovery}")
        rows.append(
            ui_row(
                str(item.get("name") or "runtime check"),
                f"{status}. {details}".strip(),
                title_ko=str(item.get("name") or "runtime check"),
                detail_ko=f"{status}. {details}".strip(),
                tone=row_tone,
                meta=meta,
            )
        )
    summary_en = (
        "Required runtime checks need recovery."
        if tone == "warn"
        else "Optional runtime checks need attention."
        if tone == "info"
        else "Required runtime checks are healthy."
    )
    summary_ko = (
        "필수 runtime 점검에 복구가 필요합니다."
        if tone == "warn"
        else "선택 runtime 점검에 확인이 필요합니다."
        if tone == "info"
        else "필수 runtime 점검이 정상입니다."
    )
    blocks = [
        ui_block(
            "judgement",
            "Runtime judgement",
            summary_en,
            title_ko="Runtime 판단",
            summary_ko=summary_ko,
            tone=tone,
            metrics=[
                ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
                ui_metric("Host", payload.get("host", "-"), label_ko="Host"),
                ui_metric("Required checks", required_count, label_ko="필수 점검"),
                ui_metric("Failed required", failed_required, label_ko="필수 실패", tone="warn" if failed_required else "neutral"),
                ui_metric("Optional failed", optional_failed, label_ko="선택 실패", tone="info" if optional_failed else "neutral"),
                ui_metric("Failed total", total_failed, label_ko="전체 실패", tone="warn" if total_failed else "neutral"),
            ],
        ),
        ui_block(
            "records",
            "Runtime check records",
            "Local user services, tmux monitors, and collab freshness checks.",
            title_ko="Runtime 점검 기록",
            summary_ko="로컬 user service, tmux monitor, collab freshness 점검입니다.",
            tone="info",
            rows=rows,
        ),
    ]
    recovery_commands = payload.get("recovery_commands") if isinstance(payload.get("recovery_commands"), list) else []
    recovery_rows = rows_from_next_actions(recovery_commands, limit=8)
    if recovery_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Recovery commands",
                "These commands may restart local runtime services; run them deliberately on the intended machine.",
                title_ko="복구 명령",
                summary_ko="아래 명령은 로컬 runtime service를 재시작할 수 있으므로 의도한 머신에서 명확히 실행하세요.",
                tone="warn",
                actions=recovery_rows,
            )
        )
    return blocks


def build_reboot_readiness_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    required = Number(payload.get("required_check_count"))
    failed = Number(payload.get("failed_required_count"))
    runtime_ok = bool(payload.get("runtime_ok", payload.get("ok", failed == 0)))
    after_login_ready = bool(payload.get("after_login_recovery_ready"))
    pre_login_guarantee = bool(payload.get("pre_login_boot_guarantee"))
    tone = "error" if failed else "ok" if after_login_ready and runtime_ok else "warn"
    readiness_items = payload.get("readiness_items") if isinstance(payload.get("readiness_items"), list) else []
    rows = [
        ui_row(
            str(item.get("name") or item.get("kind") or "Readiness item"),
            str(item.get("details") or item.get("recovery_command") or ""),
            tone="ok" if bool(item.get("ok_now")) else "warn" if bool(item.get("required", True)) else "info",
            meta=[
                f"kind {item.get('kind', '-')}",
                f"status {item.get('status_now', '-')}",
                f"enabled {item.get('enabled_state', '-')}",
                f"required {bool_word(item.get('required', False))}",
            ],
        )
        for item in readiness_items[:20]
        if isinstance(item, dict)
    ]
    actions = rows_from_next_actions(payload.get("recovery_commands"), limit=6)
    actions.extend(rows_from_next_actions(payload.get("post_reboot_validation_commands"), limit=6))
    approval_rows = rows_from_approval_boundaries(payload.get("explicit_user_approval_required_for"))
    blocks = [
        ui_block(
            "judgement",
            "Reboot recovery judgement",
            f"After-login recovery ready: {bool_word(after_login_ready)}; required failures {failed}/{required}; pre-login guarantee {bool_word(pre_login_guarantee)}.",
            title_ko="재부팅 복구 판단",
            summary_ko=f"로그인 후 복구 준비 {bool_word(after_login_ready)}, 필수 실패 {failed}/{required}, 로그인 전 보장 {bool_word(pre_login_guarantee)}.",
            tone=tone,
            metrics=[
                ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
                ui_metric("Runtime OK", bool_word(runtime_ok), label_ko="Runtime 정상", tone="ok" if runtime_ok else "warn"),
                ui_metric("After-login recovery", bool_word(after_login_ready), label_ko="로그인 후 복구"),
                ui_metric("Pre-login guarantee", bool_word(pre_login_guarantee), label_ko="로그인 전 보장"),
                ui_metric("Required failures", failed, label_ko="필수 실패", tone="error" if failed else "ok"),
            ],
        ),
        ui_block(
            "records",
            "Readiness items",
            "Login-scoped service and collab recovery checks for this PC.",
            title_ko="준비 항목",
            summary_ko="이 PC의 로그인 scope service와 collab 복구 점검입니다.",
            tone="info",
            rows=rows,
        ),
    ]
    if approval_rows:
        blocks.append(
            ui_block(
                "findings",
                "Approval boundaries",
                "These actions remain outside read-only reboot readiness and require fresh operator approval.",
                title_ko="승인 경계",
                summary_ko="아래 항목은 읽기 전용 재부팅 준비도 점검 범위를 벗어나며 fresh operator approval이 필요합니다.",
                tone="warn",
                rows=approval_rows,
            )
        )
    blocks.append(
        ui_block(
            "next_actions",
            "Recovery and validation commands",
            "Use after an operator-approved manual reboot or service restart.",
            title_ko="복구 및 검증 명령",
            summary_ko="운영자가 승인한 수동 재부팅 또는 service 재시작 후 사용합니다.",
            tone="info",
            actions=actions,
        )
    )
    return blocks


def build_machine_lifecycle_readiness_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    error_count = Number(payload.get("error_count"))
    warning_count = Number(payload.get("warning_count"))
    tone = "error" if error_count else "warn" if warning_count or not bool(payload.get("ok", True)) else "ok"
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    repos = payload.get("repos") if isinstance(payload.get("repos"), dict) else {}
    runtime_check = payload.get("runtime_check") if isinstance(payload.get("runtime_check"), dict) else {}
    runtime_checks = runtime_check.get("checks") if isinstance(runtime_check.get("checks"), list) else []
    selected = [
        item
        for item in checks
        if isinstance(item, dict) and (not bool(item.get("ok", False)) or str(item.get("severity") or "") != "ok")
    ]
    if not selected:
        selected = [item for item in checks if isinstance(item, dict)][:12]
    rows: list[dict[str, Any]] = []
    interpretation_rows: list[dict[str, Any]] = []
    for item in selected[:20]:
        name = str(item.get("name") or "Lifecycle check")
        details = str(item.get("details") or item.get("recovery_command") or "")
        detail_entries = [entry.strip() for entry in details.split(";") if entry.strip()]
        compact_details = details
        if str(item.get("status") or "") == "dirty" and len(detail_entries) > 4:
            compact_details = f"{len(detail_entries)} dirty entries: {', '.join(detail_entries[:3])} (+{len(detail_entries) - 3} more)"
        meta = [
            f"category {item.get('category', '-')}",
            f"status {item.get('status', '-')}",
            f"severity {item.get('severity', '-')}",
        ]
        if str(item.get("status") or "") == "dirty" and detail_entries:
            meta.append(f"dirty entries {len(detail_entries)}")
        rows.append(
            ui_row(
                name,
                compact_details,
                tone="ok" if bool(item.get("ok")) else "warn",
                meta=meta,
            )
        )
        if str(item.get("status") or "") == "dirty":
            interpretation_rows.append(
                ui_row(
                    name,
                    "Dirty worktree means this machine has local development WIP; it blocks sync/release readiness but does not by itself mean runtime services are broken.",
                    title_ko=name,
                    detail_ko="dirty worktree는 이 머신에 로컬 개발 WIP가 있다는 뜻입니다. sync/release 준비도는 막지만 그 자체가 runtime service 고장은 아닙니다.",
                    tone="info",
                    meta=["development WIP", "sync/release gate"],
                )
            )
    next_commands = payload.get("next_commands") if isinstance(payload.get("next_commands"), dict) else {}
    lifecycle_actions: list[dict[str, Any]] = []
    for name, command in list(next_commands.items())[:8]:
        command_text = str(command)
        command_key = str(name)
        key_lower = command_key.lower()
        approval_required = action_text_is_approval_sensitive(command_text) or (
            ("execute" in key_lower or "apply" in key_lower or "uninstall" in key_lower)
            and "dry_run" not in key_lower
            and "readiness" not in key_lower
        )
        row = row_from_next_action(
            {
                "title": command_text,
                "command": command_text,
                "kind": f"machine lifecycle: {command_key}",
                "requires_approval": approval_required,
            }
        )
        if row:
            lifecycle_actions.append(row)
    approval_rows = rows_from_approval_boundaries(payload.get("explicit_user_approval_required_for"))
    repo_rows: list[dict[str, Any]] = []
    for repo_name in sorted(repos):
        repo = repos.get(repo_name)
        if not isinstance(repo, dict):
            continue
        dirty = bool(repo.get("dirty"))
        remote_matches = bool(repo.get("remote_head_matches_local"))
        fallback_active = bool(repo.get("worker_lan_mirror_fallback_active"))
        row_tone = "warn" if dirty or not remote_matches or fallback_active else "ok"
        meta = [
            f"sync {repo.get('sync_source', '-')}",
            f"remote {bool_word(remote_matches)}",
            f"lan mirror {bool_word(repo.get('lan_mirror_matches_local'))}",
        ]
        if fallback_active:
            meta.append("LAN fallback active")
        repo_rows.append(
            ui_row(
                str(repo_name),
                f"head {repo.get('head_short', '-')}; dirty {bool_word(dirty)}",
                title_ko=str(repo_name),
                detail_ko=f"HEAD {repo.get('head_short', '-')}; dirty {bool_word(dirty)}",
                tone=row_tone,
                meta=meta,
            )
        )
    runtime_rows: list[dict[str, Any]] = []
    for item in runtime_checks[:14]:
        if not isinstance(item, dict):
            continue
        recovery_command = str(item.get("recovery_command") or "")
        meta = [
            f"required {bool_word(item.get('required'))}",
            f"status {item.get('status', '-')}",
        ]
        if recovery_command:
            meta.append("recovery command available")
        runtime_rows.append(
            ui_row(
                str(item.get("name") or "runtime check"),
                str(item.get("details") or recovery_command or ""),
                tone="ok" if bool(item.get("ok")) else "warn",
                meta=meta,
            )
        )
    blocks = [
        ui_block(
            "judgement",
            "Machine lifecycle judgement",
            f"Install {bool_word(payload.get('install_ready'))}, session entry {bool_word(payload.get('session_entry_ready'))}, reconnect {bool_word(payload.get('reconnect_ready'))}, online sync {bool_word(payload.get('online_sync_ready'))}.",
            title_ko="머신 lifecycle 판단",
            summary_ko=f"설치 {bool_word(payload.get('install_ready'))}, session entry {bool_word(payload.get('session_entry_ready'))}, reconnect {bool_word(payload.get('reconnect_ready'))}, online sync {bool_word(payload.get('online_sync_ready'))}.",
            tone=tone,
            metrics=[
                ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
                ui_metric("Checks", payload.get("check_count", len(checks)), label_ko="점검"),
                ui_metric("Errors", error_count, label_ko="오류", tone="error" if error_count else "ok"),
                ui_metric("Warnings", warning_count, label_ko="경고", tone="warn" if warning_count else "ok"),
                ui_metric("Runtime ready", bool_word(payload.get("runtime_ready")), label_ko="Runtime 준비"),
            ],
        ),
        ui_block(
            "records",
            "Lifecycle checks",
            "Important install, session, identity, and online sync checks.",
            title_ko="Lifecycle 점검",
            summary_ko="설치, session, identity, online sync 주요 점검입니다.",
            tone="info",
            rows=rows,
        ),
    ]
    if interpretation_rows:
        blocks.append(
            ui_block(
                "records",
                "Warning interpretation",
                "Lifecycle warnings should be interpreted by operator impact before taking repair actions.",
                title_ko="경고 해석",
                summary_ko="Lifecycle 경고는 복구 조치를 하기 전에 운영 영향 기준으로 해석해야 합니다.",
                tone="info" if not error_count else "warn",
                rows=interpretation_rows[:8],
            )
        )
    if repo_rows:
        repo_tone = "warn" if any(row.get("tone") == "warn" for row in repo_rows) else "ok"
        blocks.append(
            ui_block(
                "records",
                "Repo sync posture",
                "Git roots, sync source, and remote alignment for this machine.",
                title_ko="Repo sync 자세",
                summary_ko="이 머신의 git root, sync source, remote 정렬 상태입니다.",
                tone=repo_tone,
                rows=repo_rows,
            )
        )
    if runtime_rows:
        runtime_tone = "warn" if not bool(runtime_check.get("ok", True)) else "info"
        blocks.append(
            ui_block(
                "records",
                "Runtime snapshot",
                "Read-only service, tmux, and collab runtime status. Recovery commands are shown as context only.",
                title_ko="Runtime snapshot",
                summary_ko="읽기 전용 service, tmux, collab runtime 상태입니다. 복구 명령은 참고용으로만 표시됩니다.",
                tone=runtime_tone,
                rows=runtime_rows,
            )
        )
    if approval_rows:
        blocks.append(
            ui_block(
                "findings",
                "Approval boundaries",
                "These actions remain outside read-only machine lifecycle readiness and require fresh operator approval.",
                title_ko="승인 경계",
                summary_ko="아래 항목은 읽기 전용 machine lifecycle 준비도 점검 범위를 벗어나며 fresh operator approval이 필요합니다.",
                tone="warn",
                rows=approval_rows,
            )
        )
    blocks.append(
        ui_block(
            "next_actions",
            "Useful commands",
            "Machine maintenance commands reported by CLUTCH, classified by command and approval boundary.",
            title_ko="유용한 명령",
            summary_ko="CLUTCH가 보고한 머신 유지보수 명령을 명령/승인 경계 기준으로 분류했습니다.",
            tone="info",
            actions=lifecycle_actions,
        )
    )
    return blocks


def build_online_identity_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    gh = payload.get("gh") if isinstance(payload.get("gh"), dict) else {}
    auth = gh.get("auth") if isinstance(gh.get("auth"), dict) else {}
    ssh = payload.get("ssh") if isinstance(payload.get("ssh"), dict) else {}
    github_ssh = ssh.get("github_ssh") if isinstance(ssh.get("github_ssh"), dict) else {}
    registered_keys = ssh.get("github_registered_keys") if isinstance(ssh.get("github_registered_keys"), dict) else {}
    expected = (
        payload.get("expected_github_repo_access")
        if isinstance(payload.get("expected_github_repo_access"), list)
        else []
    )
    rows = [
        ui_row(
            str(item.get("github_repo") or item.get("repo_id") or "Repository"),
            str(item.get("project_id") or ""),
            tone="ok" if bool(item.get("approved")) else "warn" if bool(item.get("approval_required")) else "info",
            meta=[
                f"repo {item.get('repo_id', '-')}",
                f"remote {item.get('online_remote_name', '-')}",
                f"approved {bool_word(item.get('approved'))}",
            ],
        )
        for item in expected[:20]
        if isinstance(item, dict)
    ]
    public_keys = ssh.get("public_keys") if isinstance(ssh.get("public_keys"), list) else []
    key_rows = [
        ui_row(
            str(item.get("identity_file_basename") or item.get("path") or "SSH key"),
            str(item.get("fingerprint") or ""),
            tone="ok" if bool(item.get("ok")) else "warn",
            meta=[str(item.get("comment") or ""), f"type {item.get('key_type', '-')}"],
        )
        for item in public_keys[:8]
        if isinstance(item, dict)
    ]
    tone = "ok" if bool(payload.get("ok")) and bool(auth.get("authenticated")) and bool(github_ssh.get("ok")) else "warn"
    return [
        ui_block(
            "judgement",
            "Online identity judgement",
            f"GitHub login {auth.get('active_login', '-')}; gh auth {bool_word(auth.get('authenticated'))}; SSH auth {str(github_ssh.get('status') or '-')}.",
            title_ko="온라인 identity 판단",
            summary_ko=f"GitHub login {auth.get('active_login', '-')}, gh 인증 {bool_word(auth.get('authenticated'))}, SSH 인증 {str(github_ssh.get('status') or '-')}.",
            tone=tone,
            metrics=[
                ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
                ui_metric("GitHub login", auth.get("active_login", "-"), label_ko="GitHub login"),
                ui_metric("gh auth", bool_word(auth.get("authenticated")), label_ko="gh 인증"),
                ui_metric("SSH auth", str(github_ssh.get("status") or "-"), label_ko="SSH 인증"),
                ui_metric("Key listing", str(registered_keys.get("status") or "-"), label_ko="키 조회"),
            ],
        ),
        ui_block(
            "records",
            "Expected repository access",
            "Approved online project repositories this PC is expected to reach.",
            title_ko="예상 repo 접근",
            summary_ko="이 PC가 접근해야 하는 승인된 온라인 프로젝트 repo입니다.",
            tone="info",
            rows=rows,
        ),
        ui_block(
            "records",
            "Local public keys",
            "Public SSH keys discovered locally; private keys are not included.",
            title_ko="로컬 공개키",
            summary_ko="로컬에서 발견한 공개 SSH key입니다. private key는 포함하지 않습니다.",
            tone="info",
            rows=key_rows,
        ),
    ]


def build_project_backups_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    snapshots = payload.get("snapshots") if isinstance(payload.get("snapshots"), list) else []

    def repo_results_for(item: dict[str, Any]) -> tuple[list[Any], bool]:
        repo_results = item.get("repo_results")
        if not isinstance(repo_results, list):
            return [], False
        return repo_results, True

    def count_dirty_repos(repo_results: list[Any]) -> int:
        return sum(1 for item in repo_results if isinstance(item, dict) and bool(item.get("dirty")))

    def count_repo_status(repo_results: list[Any], key: str, expected: str) -> int:
        return sum(
            1
            for item in repo_results
            if isinstance(item, dict) and str(item.get(key) or "") == expected
        )

    latest_backup = snapshots[0] if snapshots and isinstance(snapshots[0], dict) else {}
    latest_repo_results, _ = repo_results_for(latest_backup)
    latest_dirty_repos = count_dirty_repos(latest_repo_results)
    latest_bundled_repos = count_repo_status(latest_repo_results, "status", "bundled")
    latest_online_enabled = count_repo_status(latest_repo_results, "online_backup_status", "enabled")
    rows = []
    for item in snapshots[:12]:
        if not isinstance(item, dict):
            continue
        repo_results, has_repo_results = repo_results_for(item)
        repo_meta = (
            [
                f"dirty repos {count_dirty_repos(repo_results)}",
                f"bundled repos {count_repo_status(repo_results, 'status', 'bundled')}",
                f"online enabled {count_repo_status(repo_results, 'online_backup_status', 'enabled')}",
            ]
            if has_repo_results
            else []
        )
        rows.append(
            ui_row(
                str(item.get("snapshot_id") or item.get("created_at_local") or "Backup"),
                str(item.get("manifest_path") or item.get("snapshot_root") or ""),
                tone="warn" if count_dirty_repos(repo_results) else "info",
                meta=[
                    str(item.get("created_at_local") or item.get("mtime_local") or ""),
                    f"repos {item.get('repo_count')}" if item.get("repo_count") is not None else "",
                    f"files {item.get('file_count')}" if item.get("file_count") is not None else "",
                    *repo_meta,
                    str(item.get("machine_id") or ""),
                ],
            )
        )
    return [
        ui_block(
            "judgement",
            "Local backup judgement",
            f"{payload.get('snapshot_count', len(snapshots))} local backup snapshots are known; showing {len(snapshots)}.",
            title_ko="로컬 백업 판단",
            summary_ko=f"로컬 backup snapshot {payload.get('snapshot_count', len(snapshots))}개 확인, {len(snapshots)}개 표시.",
            tone="warn" if latest_dirty_repos else "ok" if snapshots else "info",
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Backups", payload.get("snapshot_count", len(snapshots)), label_ko="백업"),
                ui_metric("Returned", len(snapshots), label_ko="반환"),
                ui_metric("Limit", payload.get("limit", "-"), label_ko="제한"),
                ui_metric("Latest", latest_backup.get("snapshot_id", "-"), label_ko="최신"),
                ui_metric("Latest files", Number(latest_backup.get("file_count")), label_ko="최신 file"),
                ui_metric("Latest repos", Number(latest_backup.get("repo_count")), label_ko="최신 repo"),
                ui_metric(
                    "Latest dirty repos",
                    latest_dirty_repos,
                    label_ko="최신 dirty repo",
                    tone="warn" if latest_dirty_repos else "neutral",
                ),
                ui_metric("Latest bundled repos", latest_bundled_repos, label_ko="최신 bundled repo"),
                ui_metric("Online-enabled repos", latest_online_enabled, label_ko="온라인 backup repo"),
            ],
        ),
        ui_block(
            "records",
            "Recent local backups",
            "Local backup bundles available on this PC.",
            title_ko="최근 로컬 백업",
            summary_ko="이 PC에서 사용 가능한 로컬 backup bundle입니다.",
            tone="info",
            rows=rows,
        ),
    ]


def build_snapshots_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    snapshots = payload.get("snapshots", payload.get("items", []))
    snapshots = snapshots if isinstance(snapshots, list) else []
    freshness = payload.get("freshness") if isinstance(payload.get("freshness"), dict) else {}
    latest_snapshot = snapshots[0] if snapshots and isinstance(snapshots[0], dict) else {}
    latest_snapshot_id = (
        freshness.get("latest_snapshot_id")
        or payload.get("latest_snapshot")
        or payload.get("latest_project_snapshot")
        or latest_snapshot.get("snapshot_id")
        or "-"
    )
    freshness_status = str(freshness.get("status") or "-")
    freshness_tone = "ok" if freshness_status == "fresh" else "warn" if freshness_status not in {"-", ""} else "info"
    rows = [
        ui_row(
            str(item.get("snapshot_id") or item.get("name") or item.get("created_at_local") or "Snapshot"),
            str(
                item.get("manifest_path")
                or item.get("snapshot_root")
                or item.get("path")
                or item.get("commit")
                or item.get("summary")
                or ""
            ),
            tone="info",
            meta=[
                value
                for value in [
                    str(item.get("created_at_local") or ""),
                    str(item.get("status") or ""),
                    f"repos {item.get('repo_count')}" if item.get("repo_count") is not None else "",
                    f"dirty {item.get('dirty_repo_count')}" if item.get("dirty_repo_count") is not None else "",
                    f"artifacts {item.get('artifact_pointer_count')}" if item.get("artifact_pointer_count") is not None else "",
                    f"validation {item.get('validation_command_count')}" if item.get("validation_command_count") is not None else "",
                    str(item.get("machine_id") or ""),
                ]
                if value
            ],
        )
        for item in snapshots[:12]
        if isinstance(item, dict)
    ]
    source_rows = [
        ui_row(
            "Machine",
            str(payload.get("machine_id") or "-"),
            title_ko="Machine",
            detail_ko=str(payload.get("machine_id") or "-"),
            tone="info",
            meta=["machine-local source"],
        ),
        ui_row(
            "Snapshot root",
            str(payload.get("snapshots_root") or "-"),
            title_ko="Snapshot root",
            detail_ko=str(payload.get("snapshots_root") or "-"),
            tone="info",
            meta=["local filesystem", "not online publication"],
        ),
    ]
    return [
        ui_block(
            "judgement",
            "Local manifest judgement",
            f"{payload.get('snapshot_count', len(snapshots))} machine-local manifests are known; latest is {latest_snapshot_id}",
            title_ko="로컬 manifest 판단",
            summary_ko=f"machine-local manifest {payload.get('snapshot_count', len(snapshots))}개 확인, 최신 항목은 {latest_snapshot_id}",
            tone=freshness_tone if snapshots else "info",
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("This PC manifests", payload.get("snapshot_count", len(snapshots)), label_ko="이 PC manifest"),
                ui_metric("Returned", len(snapshots), label_ko="반환"),
                ui_metric("Limit", payload.get("limit", "-"), label_ko="제한"),
                ui_metric("Freshness", freshness_status, label_ko="Freshness", tone="warn" if freshness_tone == "warn" else "neutral"),
                ui_metric("Latest", latest_snapshot_id, label_ko="최신"),
                ui_metric("Latest age hours", freshness.get("latest_age_hours", "-"), label_ko="최신 age"),
                ui_metric("Stale after hours", freshness.get("stale_after_hours", "-"), label_ko="Stale 기준"),
                ui_metric("Latest dirty repos", Number(latest_snapshot.get("dirty_repo_count")), label_ko="최신 dirty repo", tone="warn" if Number(latest_snapshot.get("dirty_repo_count")) else "neutral"),
                ui_metric("Latest artifact pointers", Number(latest_snapshot.get("artifact_pointer_count")), label_ko="최신 artifact pointer"),
                ui_metric("Latest validations", Number(latest_snapshot.get("validation_command_count")), label_ko="최신 validation"),
            ],
        ),
        ui_block(
            "records",
            "Local manifest source",
            "Machine-local manifests are recovery evidence from this PC; they complement approved git refs and promoted metadata.",
            title_ko="로컬 manifest source",
            summary_ko="Machine-local manifest는 이 PC의 복구 근거이며, 승인된 git ref 및 승격 metadata를 보조합니다.",
            tone="info",
            rows=source_rows,
        ),
        ui_block("records", "Recent local manifests", "Recent machine-local snapshot manifests from this PC.", title_ko="최근 로컬 manifest", summary_ko="이 PC에 저장된 최근 machine-local snapshot manifest입니다.", tone="info", rows=rows),
    ]


def build_restore_readiness_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    blockers = payload.get("blockers") if isinstance(payload.get("blockers"), list) else []
    warnings = payload.get("warnings") if isinstance(payload.get("warnings"), list) else []
    backup = payload.get("backup_verify") if isinstance(payload.get("backup_verify"), dict) else {}
    local_plan = (
        payload.get("machine_local_snapshot_restore_plan")
        if isinstance(payload.get("machine_local_snapshot_restore_plan"), dict)
        else {}
    )
    metadata_plan = payload.get("metadata_restore_plan") if isinstance(payload.get("metadata_restore_plan"), dict) else {}
    restore_smoke = payload.get("restore_smoke") if isinstance(payload.get("restore_smoke"), dict) else {}
    backup_match = (
        payload.get("backup_restore_plan_match")
        if isinstance(payload.get("backup_restore_plan_match"), dict)
        else {}
    )
    tone = "ok" if bool(payload.get("ok")) else "warn"
    local_summary = local_plan.get("summary") if isinstance(local_plan.get("summary"), dict) else {}
    metadata_summary = metadata_plan.get("summary") if isinstance(metadata_plan.get("summary"), dict) else {}
    backup_match_meta = []
    if backup_match:
        backup_match_meta = [
            f"plan match {backup_match.get('mode') or 'none'}",
            f"matched plan {backup_match.get('matched_plan_source') or '-'}",
            f"head matches {Number(backup_match.get('repo_head_match_count'))}/{Number(backup_match.get('plan_repo_count'))}",
        ]
    source_rows = [
        ui_row(
            "Backup snapshot",
            backup.get("snapshot_id") or payload.get("requested_backup_snapshot_id") or "-",
            title_ko="백업 스냅샷",
            detail_ko=backup.get("snapshot_id") or payload.get("requested_backup_snapshot_id") or "-",
            tone="ok" if backup.get("ok") else "warn",
            meta=[
                f"verified {bool_word(backup.get('ok'))}",
                f"repos {Number(backup.get('restorable_repo_count'))}/{Number(backup.get('repo_count'))}",
                f"files {Number(backup.get('file_count'))}",
            ]
            + backup_match_meta,
        ),
        ui_row(
            "Machine-local manifest",
            local_plan.get("snapshot_id") or "-",
            title_ko="Machine-local manifest",
            detail_ko=local_plan.get("snapshot_id") or "-",
            tone="ok" if local_plan.get("available") else "warn",
            meta=[
                f"available {bool_word(local_plan.get('available'))}",
                "source this PC",
                f"head matches {Number(local_summary.get('current_head_match_count'))}",
                f"dirty repos {Number(local_summary.get('dirty_recorded_repo_count'))}",
            ],
        ),
        ui_row(
            "Promoted metadata",
            metadata_plan.get("snapshot_id") or "-",
            title_ko="승격 metadata",
            detail_ko=metadata_plan.get("snapshot_id") or "-",
            tone="ok" if metadata_plan.get("available") else "warn",
            meta=[
                f"available {bool_word(metadata_plan.get('available'))}",
                f"commit {metadata_plan.get('metadata_commit_short') or '-'}",
                f"hash match {bool_word(metadata_summary.get('source_manifest_sha256_matches'))}",
            ],
        ),
        ui_row(
            "Restore smoke",
            restore_smoke.get("status") or "-",
            title_ko="Restore smoke",
            detail_ko=restore_smoke.get("status") or "-",
            tone="ok" if restore_smoke.get("status") == "ok" else "info",
            meta=[
                f"executed {bool_word(restore_smoke.get('executed'))}",
                f"failed {Number(restore_smoke.get('failed_count'))}",
                f"workspace {restore_smoke.get('restore_workspace') or '-'}",
            ],
        ),
        ui_row(
            "In-place restore boundary",
            payload.get("in_place_restore_note")
            or "in-place restore requires a fresh backup and active operator approval",
            title_ko="In-place 복구 경계",
            detail_ko=payload.get("in_place_restore_note")
            or "in-place 복구는 fresh backup과 active operator approval이 필요합니다.",
            tone="warn",
            meta=["approval boundary", "non-destructive review only"],
        ),
    ]
    rows = [
        ui_row(
            str(item),
            "Restore is blocked until this is resolved or explicitly approved.",
            detail_ko="이 항목이 해결되거나 명시 승인되기 전까지 restore는 차단됩니다.",
            tone="warn",
            meta=["blocker"],
        )
        for item in blockers[:8]
    ]
    rows.extend(
        ui_row(
            str(item),
            "Review this warning before treating restore as ready.",
            detail_ko="restore 준비 완료로 판단하기 전에 이 경고를 확인하세요.",
            tone="info",
            meta=["warning"],
        )
        for item in warnings[:8]
    )
    actions = rows_from_next_actions(payload.get("next_actions"), limit=8)
    return [
        ui_block(
            "judgement",
            "Restore readiness judgement",
            f"Non-destructive review {bool_word(payload.get('ready_for_non_destructive_restore_review'))}; in-place restore {bool_word(payload.get('ready_for_in_place_restore'))}; blockers {len(blockers)}.",
            title_ko="복구 준비도 판단",
            summary_ko=f"비파괴 검토 {bool_word(payload.get('ready_for_non_destructive_restore_review'))}, in-place 복구 {bool_word(payload.get('ready_for_in_place_restore'))}, blocker {len(blockers)}개.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Backup verified", bool_word(backup.get("ok")), label_ko="백업 검증"),
                ui_metric(
                    "Backup-plan match",
                    backup_match.get("mode") or "none",
                    label_ko="백업-계획 일치",
                    tone="ok" if backup_match.get("ok") else "warn",
                ),
                ui_metric("Local plan", bool_word(local_plan.get("available")), label_ko="로컬 계획"),
                ui_metric("Metadata plan", bool_word(metadata_plan.get("available")), label_ko="메타데이터 계획"),
                ui_metric("Blockers", len(blockers), label_ko="Blocker", tone="warn" if blockers else "ok"),
            ],
        ),
        ui_block(
            "records",
            "Restore evidence source",
            "Restore readiness is based on backup verification, this PC's machine-local manifest, and promoted metadata; destructive restore remains approval-gated.",
            title_ko="복구 근거 source",
            summary_ko="복구 준비도는 백업 검증, 이 PC의 machine-local manifest, 승격 metadata를 함께 보며, 파괴적 복구는 계속 승인 경계 안에 둡니다.",
            tone="warn" if warnings or blockers else "info",
            rows=source_rows,
        ),
        ui_block(
            "findings",
            "Blockers and warnings",
            "Restore must stay review-only until these items are resolved or explicitly approved.",
            title_ko="Blocker 및 경고",
            summary_ko="아래 항목이 해결되거나 명시 승인되기 전까지 restore는 검토 전용입니다.",
            tone=tone,
            rows=rows,
        ),
        ui_block(
            "next_actions",
            "Suggested restore checks",
            "Non-destructive commands to make restore readiness auditable.",
            title_ko="권장 restore 점검",
            summary_ko="복구 준비도를 검증하기 위한 비파괴 명령입니다.",
            tone="info",
            actions=actions,
        ),
    ]


def build_artifact_pointers_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    artifacts = payload.get("artifact_results") if isinstance(payload.get("artifact_results"), list) else []
    source_errors = payload.get("source_errors") if isinstance(payload.get("source_errors"), list) else []
    policy = payload.get("artifact_pointer_policy") if isinstance(payload.get("artifact_pointer_policy"), dict) else {}
    empty_interpretation = (
        payload.get("empty_artifact_interpretation")
        if isinstance(payload.get("empty_artifact_interpretation"), dict)
        else {}
    )
    next_actions = payload.get("next_actions") if isinstance(payload.get("next_actions"), list) else []
    source_type = str(payload.get("source_type") or "-")
    source_path = str(payload.get("source_path") or "")
    metadata_branch = str(payload.get("metadata_branch") or "")
    metadata_commit = str(payload.get("metadata_commit") or "")
    blocking = Number(summary.get("blocking_count"))
    warnings = Number(summary.get("warning_count"))
    pointer_count = Number(summary.get("artifact_pointer_count", len(artifacts)))
    policy_mode = str(summary.get("artifact_pointer_policy_mode") or policy.get("mode") or "-")
    empty_status = str(empty_interpretation.get("status") or "")
    empty_severity = str(empty_interpretation.get("severity") or "")
    requires_pointer = bool(empty_interpretation.get("requires_artifact_pointer_before_handoff", False))
    source_note_count = len([item for item in source_errors if str(item or "").strip()])
    tone = (
        "error"
        if blocking
        else "warn"
        if warnings or requires_pointer or empty_status == "required_missing"
        else "ok"
        if pointer_count > 0 or empty_status == "none_required"
        else "info"
        if pointer_count == 0
        else "ok"
    )
    rows = [
        ui_row(
            str(item.get("name") or item.get("uri") or item.get("path") or item.get("kind") or "Artifact"),
            str(item.get("details") or item.get("message") or item.get("path") or item.get("uri") or ""),
            tone="ok" if str(item.get("status") or item.get("hash_status") or "") in {"ok", "verified", "hashed"} else "info",
            meta=[
                f"kind {item.get('kind', '-')}",
                f"status {item.get('status', item.get('hash_status', '-'))}",
            ],
        )
        for item in artifacts[:20]
        if isinstance(item, dict)
    ]
    if not rows:
        if empty_status == "required_missing":
            empty_title = "Required artifact pointers missing"
            empty_detail = str(
                empty_interpretation.get("summary")
                or "Project policy requires artifact pointers, but none are recorded by this source."
            )
            empty_title_ko = "필수 Artifact pointer 누락"
            empty_detail_ko = "프로젝트 policy상 artifact pointer가 필요하지만 이 source에는 기록되어 있지 않습니다."
            empty_tone = "warn"
        elif empty_status == "none_required":
            empty_title = "No artifact pointers required"
            empty_detail = str(
                empty_interpretation.get("summary")
                or "Project policy says this state is covered by code/config metadata only."
            )
            empty_title_ko = "Artifact pointer 불필요"
            empty_detail_ko = "프로젝트 policy상 현재 상태는 code/config metadata만으로 충분합니다."
            empty_tone = "ok"
        else:
            empty_title = "No artifact pointers recorded"
            empty_detail = str(
                empty_interpretation.get("summary")
                or "The selected snapshot or metadata source does not record large external artifacts for this project state."
            )
            empty_title_ko = "Artifact pointer 없음"
            empty_detail_ko = "선택된 snapshot 또는 metadata source에 이 프로젝트 상태의 대형 외부 artifact가 기록되어 있지 않습니다."
            empty_tone = "info"
        rows.append(
            ui_row(
                empty_title,
                empty_detail,
                title_ko=empty_title_ko,
                detail_ko=empty_detail_ko,
                tone=empty_tone,
                meta=[
                    f"source {payload.get('source_type', '-')}",
                    "empty artifact manifest",
                    f"policy {policy_mode}",
                    f"handoff pointer required {bool_word(requires_pointer)}",
                ],
            )
        )
    source_note_rows = [
        ui_row(
            "Artifact source note",
            str(item),
            title_ko="Artifact source 참고",
            detail_ko=str(item),
            tone="warn" if not payload.get("ok", True) else "info",
            meta=[f"source {payload.get('source_type', '-')}", "source fallback"],
        )
        for item in source_errors[:8]
        if str(item or "").strip()
    ]
    blocks = [
        ui_block(
            "judgement",
            "Artifact pointer judgement",
            f"{pointer_count} artifact pointers from {payload.get('source_type', '-')}; blocking {blocking}, warnings {warnings}.",
            title_ko="Artifact pointer 판단",
            summary_ko=f"{payload.get('source_type', '-')} 기준 artifact pointer {pointer_count}개, blocking {blocking}, warning {warnings}.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Pointers", pointer_count, label_ko="Pointer"),
                ui_metric("Policy", policy_mode, label_ko="Policy", tone="warn" if requires_pointer else "neutral"),
                ui_metric("Empty status", empty_status or "-", label_ko="Empty status", tone=empty_severity if empty_severity in {"ok", "warn", "error", "info"} else "neutral"),
                ui_metric("Verified", Number(summary.get("verified_count")), label_ko="검증됨"),
                ui_metric("Missing", Number(summary.get("missing_count")), label_ko="누락"),
                ui_metric("Source", payload.get("source_type", "-"), label_ko="Source"),
                ui_metric("Source machine", payload.get("source_machine_id", "-"), label_ko="Source machine"),
                ui_metric("Snapshot", payload.get("snapshot_id", "-"), label_ko="Snapshot"),
                ui_metric("Source notes", source_note_count, label_ko="Source note", tone="warn" if source_note_count and not payload.get("ok", True) else "neutral"),
                ui_metric("Blockers", blocking, label_ko="Blocker", tone="error" if blocking else "neutral"),
                ui_metric("Warnings", warnings, label_ko="경고", tone="warn" if warnings else "ok"),
            ],
        ),
        ui_block(
            "records",
            "Artifact records",
            "Artifact pointers recorded by the selected snapshot or metadata source.",
            title_ko="Artifact 기록",
            summary_ko="선택된 snapshot 또는 metadata source에 기록된 artifact pointer입니다.",
            tone="info",
            rows=rows,
        ),
    ]
    policy_rows = [
        ui_row(
            "Policy mode",
            policy_mode,
            title_ko="Policy mode",
            detail_ko=policy_mode,
            tone="warn" if requires_pointer else "info",
            meta=[
                f"reviewed_by {policy.get('reviewed_by', '-') or '-'}",
                f"reviewed_at {policy.get('reviewed_at_local', '-') or '-'}",
            ],
        ),
        ui_row(
            "Artifact boundary",
            str(empty_interpretation.get("summary") or "Artifact pointer policy is available for this project."),
            title_ko="Artifact 경계",
            detail_ko=str(empty_interpretation.get("summary") or "이 프로젝트의 artifact pointer policy입니다."),
            tone="warn" if requires_pointer else "ok" if empty_status == "none_required" else "info",
            meta=[f"requires handoff pointer {bool_word(requires_pointer)}"],
        ),
    ]
    if policy.get("reason"):
        policy_rows.append(
            ui_row(
                "Policy reason",
                str(policy.get("reason") or ""),
                title_ko="Policy reason",
                detail_ko=str(policy.get("reason") or ""),
                tone="info",
            )
        )
    blocks.append(
        ui_block(
            "records",
            "Artifact policy",
            "Project-specific data policy determines whether an empty artifact pointer set is ok, informational, or a handoff gap.",
            title_ko="Artifact policy",
            summary_ko="프로젝트별 데이터 policy가 artifact pointer 0개의 의미를 결정합니다.",
            tone="warn" if requires_pointer else "info",
            rows=policy_rows,
        )
    )
    source_rows: list[dict[str, Any]] = [
        ui_row(
            "Source",
            source_type,
            title_ko="Source",
            detail_ko=source_type,
            tone="info",
            meta=[
                f"machine {payload.get('source_machine_id', '-')}",
                f"read-only {bool_word(payload.get('read_only', True))}",
            ],
        )
    ]
    if payload.get("snapshot_id"):
        source_rows.append(
            ui_row(
                "Snapshot",
                str(payload.get("snapshot_id")),
                title_ko="Snapshot",
                detail_ko=str(payload.get("snapshot_id")),
                tone="info",
                meta=["artifact pointer source"],
            )
        )
    if source_path:
        source_rows.append(
            ui_row(
                "Source path",
                source_path,
                title_ko="Source path",
                detail_ko=source_path,
                tone="info",
                meta=["manifest or metadata path"],
            )
        )
    if metadata_branch or metadata_commit:
        source_rows.append(
            ui_row(
                "Metadata ref",
                metadata_branch or "-",
                title_ko="Metadata ref",
                detail_ko=metadata_branch or "-",
                tone="info",
                meta=[f"commit {metadata_commit or '-'}"],
            )
        )
    blocks.append(
        ui_block(
            "records",
            "Artifact source",
            "Where CLUTCH read the artifact pointer evidence from; this does not copy or publish large artifacts.",
            title_ko="Artifact source",
            summary_ko="CLUTCH가 artifact pointer 근거를 읽은 위치입니다. 대형 artifact를 복사하거나 publish하지 않습니다.",
            tone="info",
            rows=source_rows,
        )
    )
    if source_note_rows:
        blocks.append(ui_block("findings", "Artifact source notes", "Source fallback or lookup notes returned while reading artifact pointers.", title_ko="Artifact source 참고", summary_ko="Artifact pointer를 읽는 동안 반환된 source fallback 또는 조회 참고 사항입니다.", tone="info" if payload.get("ok", True) else "warn", rows=source_note_rows))
    if next_actions:
        blocks.append(
            ui_block(
                "next_actions",
                "Artifact next checks",
                "Read-only checks or operator steps for the current artifact pointer policy.",
                title_ko="Artifact 다음 점검",
                summary_ko="현재 artifact pointer policy에 맞춘 읽기 전용 점검 또는 작업자 단계입니다.",
                tone="warn" if requires_pointer else "info",
                actions=[
                    ui_row(
                        str(action),
                        "Use the active Codex session or terminal; this Web result does not copy or publish artifacts.",
                        detail_ko="활성 Codex 세션 또는 터미널에서 처리하세요. 이 Web 결과는 artifact를 복사하거나 publish하지 않습니다.",
                        tone="warn" if requires_pointer else "info",
                        meta=["operator step", "no artifact copy"],
                    )
                    for action in next_actions[:5]
                    if str(action or "").strip()
                ],
            )
        )
    return blocks


def build_away_cycles_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    entries = payload.get("entries") if isinstance(payload.get("entries"), list) else []
    soak = payload.get("soak") if isinstance(payload.get("soak"), dict) else {}
    summary_file = payload.get("summary_file") if isinstance(payload.get("summary_file"), dict) else {}
    status = str(soak.get("status") or "")
    latest_decision = str(payload.get("latest_decision") or "")
    latest_action = str(payload.get("latest_recommended_next_action") or "")
    project_id = str(payload.get("project_id") or "")
    latest_entry = entries[-1] if entries and isinstance(entries[-1], dict) else {}
    latest_phase_closeout = bool(latest_entry.get("phase_closeout", False))
    summary_aligned = bool(summary_file.get("aligned_with_cycle_log", True))
    resume_warning_match = bool(
        summary_file.get("latest_resume_warning_count_matches_latest_cycle", True)
    )
    resume_info_match = bool(
        summary_file.get("latest_resume_info_count_matches_latest_cycle", True)
    )
    resume_alignment_ok = summary_aligned and resume_warning_match and resume_info_match
    tone = "info" if status == "no_cycles" else away_cycle_tone(
        ok=bool(payload.get("ok")),
        decision=latest_decision,
        soak_status=status,
    )
    if not resume_alignment_ok:
        tone = "warn"
    resume_warning_display = (
        f"{summary_file.get('latest_resume_warning_count')} / "
        f"{summary_file.get('expected_latest_resume_warning_count')}"
        if summary_file.get("latest_resume_warning_count") is not None
        or summary_file.get("expected_latest_resume_warning_count") is not None
        else "-"
    )
    resume_info_display = (
        f"{summary_file.get('latest_resume_info_count')} / "
        f"{summary_file.get('expected_latest_resume_info_count')}"
        if summary_file.get("latest_resume_info_count") is not None
        or summary_file.get("expected_latest_resume_info_count") is not None
        else "-"
    )
    rows = [
        ui_row(
            str(item.get("cycle_id") or item.get("created_at_local") or "Away cycle"),
            str(
                item.get("phase_decision_note")
                or item.get("objective")
                or item.get("recommended_next_action")
                or item.get("summary")
                or ""
            ),
            tone=away_cycle_row_tone(str(item.get("decision") or "")),
            meta=[
                value
                for value in [
                    f"decision {item.get('decision', '-')}",
                    f"phase {item.get('phase')}" if item.get("phase") else "",
                    "phase closeout" if item.get("phase_closeout") else "",
                    str(item.get("created_at_local") or ""),
                ]
                if value
            ],
        )
        for item in entries[:12]
        if isinstance(item, dict)
    ]
    actions: list[Any] = []
    if latest_action:
        actions.append(latest_action)
    if away_cycle_needs_review(latest_decision, status):
        actions.append(
            {
                "title": "Compare the current operator instruction with the active away plan.",
                "detail": "Continue only if the new instruction is still inside the recorded objective, allowed scope, and stop conditions.",
                "kind": "operator review",
            }
        )
    if not resume_alignment_ok:
        actions.append(
            {
                "title": "Inspect away-cycle Markdown and JSONL alignment.",
                "detail": "The readable Markdown summary no longer matches the latest machine-local cycle log. Treat the JSONL log as authoritative and repair the summary before relying on it.",
                "kind": "integrity check",
            }
        )
    if project_id:
        actions.extend(
            [
                f"python3 scripts/clutch_ctl.py project-away-work --project {project_id} --include-plan-text --json",
                f"python3 scripts/clutch_ctl.py project-away-report --project {project_id} --skip-runtime --json",
            ]
        )
    blocks = [
        ui_block(
            "judgement",
            "Away cycle judgement",
            f"Valid cycles {payload.get('valid_cycle_count', 0)}, latest decision {latest_decision or '-'}, soak status {status or '-'}.",
            title_ko="자리비움 cycle 판단",
            summary_ko=f"유효 cycle {payload.get('valid_cycle_count', 0)}개, 최신 decision {latest_decision or '-'}, soak 상태 {status or '-'}.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Valid cycles", payload.get("valid_cycle_count", 0), label_ko="유효 cycle"),
                ui_metric("Returned", payload.get("returned_count", len(entries)), label_ko="반환"),
                ui_metric("Log present", bool_word(payload.get("log_present")), label_ko="로그 존재"),
                ui_metric("Latest decision", latest_decision or "-", label_ko="최신 decision", tone=tone),
                ui_metric("Latest closeout", bool_word(latest_phase_closeout), label_ko="최신 closeout"),
                ui_metric("Soak status", status or "-", label_ko="Soak 상태"),
                ui_metric("Continue streak", soak.get("continue_streak_count", 0), label_ko="Continue streak"),
                ui_metric("Remaining", soak.get("remaining_cycles", 0), label_ko="남은 cycle"),
                ui_metric("Summary aligned", bool_word(resume_alignment_ok), label_ko="요약 정합", tone="ok" if resume_alignment_ok else "warn"),
                ui_metric("Resume warnings", resume_warning_display, label_ko="재개 warning", tone="ok" if resume_warning_match else "warn"),
                ui_metric("Resume infos", resume_info_display, label_ko="재개 info", tone="ok" if resume_info_match else "warn"),
            ],
        ),
        ui_block(
            "records",
            "Recent away cycles",
            "Recent queued away-development cycle records.",
            title_ko="최근 자리비움 cycle",
            summary_ko="최근 queued away-development cycle 기록입니다.",
            tone="info",
            rows=rows,
        ),
    ]
    if actions:
        blocks.append(
            ui_block(
                "next_actions",
                "Away continuation checks",
                "Use these checks before treating queued away-development as safely continued.",
                title_ko="자리비움 계속 진행 점검",
                summary_ko="queued 자리비움 개발을 안전하게 계속하기 전에 아래 확인을 사용하세요.",
                tone="warn" if away_cycle_needs_review(latest_decision, status) else "info",
                actions=rows_from_next_actions(actions, limit=6),
            )
        )
    return blocks


def build_away_report_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    plan = payload.get("away_plan") if isinstance(payload.get("away_plan"), dict) else {}
    cycles = payload.get("away_cycles") if isinstance(payload.get("away_cycles"), dict) else {}
    counts = payload.get("attention_severity_counts") if isinstance(payload.get("attention_severity_counts"), dict) else {}
    resume = payload.get("resume_summary") if isinstance(payload.get("resume_summary"), dict) else {}
    pre_web = payload.get("pre_web_readiness") if isinstance(payload.get("pre_web_readiness"), dict) else {}
    latest_cycle = resume.get("latest_cycle") if isinstance(resume.get("latest_cycle"), dict) else {}
    latest_decision = str(latest_cycle.get("decision") or cycles.get("latest_decision") or "")
    soak = resume.get("soak") if isinstance(resume.get("soak"), dict) else cycles.get("soak") if isinstance(cycles.get("soak"), dict) else {}
    summary_file = cycles.get("summary_file") if isinstance(cycles.get("summary_file"), dict) else {}
    soak_status = str(soak.get("status") or "")
    blocker_count = Number(resume.get("blocker_count", 0))
    warning_count = Number(resume.get("warning_count", 0))
    info_count = Number(resume.get("info_count", 0))
    summary_aligned = bool(summary_file.get("aligned_with_cycle_log", True))
    resume_warning_match = bool(
        summary_file.get("latest_resume_warning_count_matches_latest_cycle", True)
    )
    resume_info_match = bool(
        summary_file.get("latest_resume_info_count_matches_latest_cycle", True)
    )
    resume_alignment_ok = summary_aligned and resume_warning_match and resume_info_match
    resume_warning_display = (
        f"{summary_file.get('latest_resume_warning_count')} / "
        f"{summary_file.get('expected_latest_resume_warning_count')}"
        if summary_file.get("latest_resume_warning_count") is not None
        or summary_file.get("expected_latest_resume_warning_count") is not None
        else "-"
    )
    resume_info_display = (
        f"{summary_file.get('latest_resume_info_count')} / "
        f"{summary_file.get('expected_latest_resume_info_count')}"
        if summary_file.get("latest_resume_info_count") is not None
        or summary_file.get("expected_latest_resume_info_count") is not None
        else "-"
    )
    base_tone = attention_tone(counts, ok=bool(payload.get("ok", True)))
    can_start = bool(plan.get("ready_for_queued_away_work", payload.get("can_start", False)))
    resume_ready = bool(resume.get("ready_for_unattended_continuation", payload.get("ready_for_unattended_continuation", can_start)))
    pre_web_ready_raw = resume.get("pre_web_ready", pre_web.get("ok") if pre_web else None)
    pre_web_ready = pre_web_ready_raw if isinstance(pre_web_ready_raw, bool) else None
    pre_web_ready_display = "-" if pre_web_ready is None else bool_word(pre_web_ready)
    pre_web_ready_tone = "neutral" if pre_web_ready is None else "ok" if pre_web_ready else "warn"
    pre_web_actions = resume.get("pre_web_next_actions") if isinstance(resume.get("pre_web_next_actions"), list) else []
    pre_web_gate_ready = pre_web.get("required_gate_ready_count")
    pre_web_gate_count = pre_web.get("required_gate_count")
    pre_web_gate_display = (
        f"{pre_web_gate_ready}/{pre_web_gate_count}"
        if pre_web_gate_ready is not None or pre_web_gate_count is not None
        else "-"
    )
    tone = (
        "error"
        if base_tone == "error"
        else "warn"
        if (
            blocker_count
            or not resume_ready
            or pre_web_ready is False
            or away_cycle_needs_review(latest_decision, soak_status)
            or not resume_alignment_ok
        )
        else "warn"
        if warning_count or base_tone == "warn"
        else base_tone
    )
    rows = rows_from_next_actions(payload.get("next_actions"))
    recommendations = plan.get("safety_guidance", {}).get("recommendations") if isinstance(plan.get("safety_guidance"), dict) else []
    rows.extend(rows_from_next_actions(recommendations, limit=6))
    resume_action = str(resume.get("recommended_next_action") or "")
    if resume_action:
        rows.extend(rows_from_next_actions([resume_action], limit=1))
    rows.extend(rows_from_next_actions(resume.get("pre_web_next_actions"), limit=4))
    if away_cycle_needs_review(latest_decision, soak_status):
        rows.extend(
            rows_from_next_actions(
                [
                    {
                        "title": "Compare the current operator instruction with the active away plan.",
                        "detail": "If the instruction is outside the recorded scope, stop and create a fresh away plan.",
                        "kind": "operator review",
                    }
                ],
                limit=1,
            )
        )
    if not resume_alignment_ok:
        rows.extend(
            rows_from_next_actions(
                [
                    {
                        "title": "Inspect away-cycle Markdown and JSONL alignment.",
                        "detail": "The readable cycle summary no longer matches the latest machine-local cycle log. Use project-away-cycles --json to inspect the mismatch.",
                        "kind": "integrity check",
                    }
                ],
                limit=1,
            )
        )
    finding_rows = [
        ui_row(
            str(item),
            "Resolve this blocker before treating away development as resumable.",
            detail_ko="자리비움 개발을 재개 가능하다고 보기 전에 이 blocker를 해결하세요.",
            tone="warn",
            meta=["blocker"],
        )
        for item in (resume.get("blockers") if isinstance(resume.get("blockers"), list) else [])[:8]
    ]
    finding_rows.extend(
        ui_row(
            str(item),
            "Review this warning before relying on the away resume state.",
            detail_ko="자리비움 resume 상태를 신뢰하기 전에 이 경고를 확인하세요.",
            tone="info",
            meta=["warning"],
        )
        for item in (resume.get("warnings") if isinstance(resume.get("warnings"), list) else [])[:8]
    )
    finding_rows.extend(
        ui_row(
            str(item),
            "Informational context for the current away resume state.",
            detail_ko="현재 자리비움 resume 상태에 대한 정보입니다.",
            tone="info",
            meta=["info"],
        )
        for item in (resume.get("infos") if isinstance(resume.get("infos"), list) else [])[:8]
    )
    pre_web_interpretation = (
        pre_web.get("gate_interpretation", {})
        if isinstance(pre_web.get("gate_interpretation"), dict)
        else {}
    )
    pre_web_backend = (
        pre_web.get("web_backend_generation", {})
        if isinstance(pre_web.get("web_backend_generation"), dict)
        else {}
    )
    pre_web_blocking_gates = (
        pre_web.get("blocking_gates", [])
        if isinstance(pre_web.get("blocking_gates"), list)
        else []
    )
    blocks = [
        ui_block(
            "judgement",
            "Away development judgement",
            f"Away plan present: {bool_word(plan.get('present', payload.get('plan_present', False)))}; queued work ready: {bool_word(can_start)}; cycles {cycles.get('valid_cycle_count', '-')}.",
            title_ko="자리비움 개발 판단",
            summary_ko=f"자리비움 계획 존재 {bool_word(plan.get('present', payload.get('plan_present', False)))}, 큐 작업 준비 {bool_word(can_start)}, 사이클 {cycles.get('valid_cycle_count', '-')}.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Plan present", bool_word(plan.get("present", payload.get("plan_present", False))), label_ko="계획 존재"),
                ui_metric("Queued ready", bool_word(can_start), label_ko="큐 준비"),
                ui_metric("Resume ready", bool_word(resume_ready), label_ko="재개 준비", tone="ok" if resume_ready else "warn"),
                ui_metric("Pre-web ready", pre_web_ready_display, label_ko="Pre-web 준비", tone=pre_web_ready_tone),
                ui_metric("Pre-web gates", pre_web_gate_display, label_ko="Pre-web gate", tone=pre_web_ready_tone),
                ui_metric("Pre-web actions", len(pre_web_actions), label_ko="Pre-web action", tone="info" if pre_web_actions else "neutral"),
                ui_metric("Cycles", cycles.get("valid_cycle_count", payload.get("valid_cycle_count", "-")), label_ko="사이클"),
                ui_metric("Latest decision", latest_decision or "-", label_ko="최신 decision", tone="warn" if away_cycle_needs_review(latest_decision, soak_status) else "ok"),
                ui_metric("Resume blockers", blocker_count, label_ko="재개 blocker", tone="warn" if blocker_count else "ok"),
                ui_metric("Resume info", info_count, label_ko="재개 정보", tone="info" if info_count else "neutral"),
                ui_metric("Cycle summary aligned", bool_word(resume_alignment_ok), label_ko="Cycle 요약 정합", tone="ok" if resume_alignment_ok else "warn"),
                ui_metric("Cycle resume warnings", resume_warning_display, label_ko="Cycle 재개 warning", tone="ok" if resume_warning_match else "warn"),
                ui_metric("Cycle resume infos", resume_info_display, label_ko="Cycle 재개 info", tone="ok" if resume_info_match else "warn"),
                ui_metric("Attention", payload.get("attention_count", counts.get("total_count", 0)), label_ko="주의 항목", tone=tone),
            ],
        ),
    ]
    if finding_rows:
        blocks.append(
            ui_block(
                "findings",
                "Resume findings",
                "Items affecting whether the current away plan can be resumed without fresh scope changes.",
                title_ko="재개 판단 항목",
                summary_ko="현재 away plan을 새 범위 변경 없이 재개할 수 있는지에 영향을 주는 항목입니다.",
                tone="warn" if blocker_count else "info",
                rows=finding_rows,
            )
        )
    if pre_web and (pre_web_interpretation or pre_web_backend or pre_web_blocking_gates):
        boundary_status = str(pre_web_interpretation.get("status") or "")
        boundary_summary = str(pre_web_interpretation.get("summary") or "")
        boundary_tone = (
            "ok"
            if pre_web_ready is True
            else "warn"
            if boundary_status
            in {"web_ready_project_cleanliness_blocked", "project_cleanliness_blocked", "blocked"}
            else "error"
            if boundary_status == "web_backend_needs_review"
            else "info"
        )
        boundary_rows: list[dict[str, Any]] = []
        if pre_web_backend:
            backend_ready = bool(pre_web_backend.get("ok")) and str(pre_web_backend.get("status") or "") == "ready"
            boundary_rows.append(
                ui_row(
                    "Web backend generation",
                    (
                        f"status={pre_web_backend.get('status', '-')} "
                        f"process={pre_web_backend.get('process_version', '-')} "
                        f"expected={pre_web_backend.get('expected_version', '-')} "
                        f"commands={pre_web_backend.get('command_count', 0)}"
                    ),
                    title_ko="Web backend generation",
                    detail_ko=(
                        f"상태={pre_web_backend.get('status', '-')} "
                        f"프로세스={pre_web_backend.get('process_version', '-')} "
                        f"기대={pre_web_backend.get('expected_version', '-')} "
                        f"명령={pre_web_backend.get('command_count', 0)}"
                    ),
                    tone="ok" if backend_ready else "warn",
                    meta=[
                        "web backend ready" if backend_ready else "web backend review",
                        f"default {pre_web_backend.get('default_command_count', 0)}",
                        f"advanced {pre_web_backend.get('advanced_command_count', 0)}",
                    ],
                )
            )
        if pre_web_interpretation:
            meta = [boundary_status] if boundary_status else []
            if pre_web_interpretation.get("web_backend_ready"):
                meta.append("web backend ready")
            if pre_web_interpretation.get("project_cleanliness_only"):
                meta.append("project clean gate")
            if pre_web_interpretation.get("reproducibility_ready"):
                meta.append("recovery evidence ready")
            if pre_web_interpretation.get("publication_status"):
                meta.append(f"publication {pre_web_interpretation.get('publication_status')}")
            boundary_rows.append(
                ui_row(
                    "Pre-web gate interpretation",
                    boundary_summary,
                    title_ko="Pre-web gate 해석",
                    detail_ko=boundary_summary,
                    tone=boundary_tone,
                    meta=meta,
                )
            )
        for gate in pre_web_blocking_gates[:4]:
            if not isinstance(gate, dict):
                continue
            gate_name = str(gate.get("name") or "gate")
            details = str(gate.get("details") or gate.get("next_action") or "")
            meta = [
                value
                for value in [
                    str(gate.get("category") or ""),
                    str(gate.get("status") or ""),
                    str(gate.get("project_id") or ""),
                ]
                if value
            ]
            boundary_rows.append(
                ui_row(
                    gate_name,
                    details,
                    title_ko=gate_name,
                    detail_ko=details,
                    tone="warn",
                    meta=meta,
                )
            )
        blocks.append(
            ui_block(
                "findings",
                "Pre-web gate boundary",
                "This separates Web runtime readiness from the current project clean sync/publication gate.",
                title_ko="Pre-web gate 경계",
                summary_ko="Web runtime 준비 상태와 현재 프로젝트 clean sync/publish gate를 분리해서 보여줍니다.",
                tone=boundary_tone,
                metrics=[
                    ui_metric(
                        "Web backend",
                        "ready" if pre_web_interpretation.get("web_backend_ready") else "review",
                        label_ko="Web backend",
                        tone="ok" if pre_web_interpretation.get("web_backend_ready") else "warn",
                    ),
                    ui_metric(
                        "Project gate",
                        "cleanliness only" if pre_web_interpretation.get("project_cleanliness_only") else "mixed",
                        label_ko="프로젝트 gate",
                        tone="warn" if pre_web_interpretation.get("project_cleanliness_only") else "neutral",
                    ),
                    ui_metric(
                        "Dirty repos",
                        Number(pre_web_interpretation.get("dirty_repo_count")),
                        label_ko="Dirty repo",
                        tone="warn" if Number(pre_web_interpretation.get("dirty_repo_count")) else "neutral",
                    ),
                    ui_metric(
                        "Publication",
                        pre_web_interpretation.get("publication_status", "-"),
                        label_ko="Publish",
                        tone="warn" if pre_web_interpretation.get("publication_status") else "neutral",
                    ),
                ],
                rows=boundary_rows,
            )
        )
    blocks.append(
        ui_block(
            "next_actions",
            "Suggested next checks",
            "Use these items to decide whether queued away work can continue.",
            title_ko="권장 다음 확인",
            summary_ko="큐 자리비움 작업을 계속할 수 있는지 판단할 때 아래 항목을 사용하세요.",
            tone="warn" if tone in {"warn", "error"} else "info",
            actions=rows,
        )
    )
    return blocks


def build_snapshot_manifest_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    repos = payload.get("repo_versions") if isinstance(payload.get("repo_versions"), list) else []
    artifacts = payload.get("artifact_pointers") if isinstance(payload.get("artifact_pointers"), list) else []
    dry_run = bool(payload.get("dry_run", True))
    rows = [
        ui_row(
            str(repo.get("repo_id") or repo.get("path") or "Repo"),
            str(repo.get("path") or ""),
            tone="warn" if bool(repo.get("dirty")) else "ok",
            meta=[
                f"head {str(repo.get('head') or '')[:7]}",
                f"branch {repo.get('branch', '-')}",
                f"dirty {bool_word(repo.get('dirty'))}",
            ],
        )
        for repo in repos[:20]
        if isinstance(repo, dict)
    ]
    return [
        ui_block(
            "judgement",
            "Snapshot result",
            f"Snapshot {payload.get('snapshot_id', '-')} {'previewed' if dry_run else 'written'} with {len(repos)} repos and {len(artifacts)} artifact pointers.",
            title_ko="스냅샷 결과",
            summary_ko=f"스냅샷 {payload.get('snapshot_id', '-')} {'미리보기' if dry_run else '기록'} 완료. repo {len(repos)}개, artifact pointer {len(artifacts)}개.",
            tone="ok",
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Snapshot", payload.get("snapshot_id", "-"), label_ko="스냅샷"),
                ui_metric("Repos", len(repos), label_ko="Repo"),
                ui_metric("Artifacts", len(artifacts), label_ko="Artifact"),
                ui_metric("Dry run", bool_word(dry_run), label_ko="Dry run"),
            ],
        ),
        ui_block("records", "Repo versions", "Repo heads captured by this snapshot.", title_ko="Repo 버전", summary_ko="이 스냅샷에 기록된 repo head입니다.", tone="info", rows=rows),
    ]


def build_backup_manifest_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    repos = payload.get("repo_results") if isinstance(payload.get("repo_results"), list) else []
    files = payload.get("file_results") if isinstance(payload.get("file_results"), list) else []
    failed = [
        item
        for item in repos
        if isinstance(item, dict) and str(item.get("status") or "") not in {"bundled", "would_bundle", "skipped"}
    ]
    required_missing_files = [
        item
        for item in files
        if isinstance(item, dict) and str(item.get("status") or "") == "missing" and bool(item.get("required", False))
    ]
    optional_missing_files = [
        item
        for item in files
        if isinstance(item, dict) and str(item.get("status") or "") == "optional_missing"
    ]
    dry_run = bool(payload.get("dry_run", False))
    rows = build_records_from_repo_results(repos)
    file_rows: list[dict[str, Any]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "")
        if status not in {"missing", "optional_missing", "directory_skipped"}:
            continue
        required = bool(item.get("required", False))
        sources = item.get("sources") if isinstance(item.get("sources"), list) else []
        file_rows.append(
            ui_row(
                str(item.get("path") or "file"),
                str(item.get("details") or status),
                tone="warn" if status == "missing" and required else "info",
                meta=[status, "required" if required else "optional", *[str(source) for source in sources[:3]]],
            )
        )
    tone = "warn" if failed or required_missing_files else "ok"
    blocks = [
        ui_block(
            "judgement",
            "Backup result",
            f"Backup {payload.get('snapshot_id', '-')} {'previewed' if dry_run else 'written'}; repos {len(repos)}, files {len(files)}, failed repos {len(failed)}, required missing files {len(required_missing_files)}.",
            title_ko="백업 결과",
            summary_ko=f"백업 {payload.get('snapshot_id', '-')} {'미리보기' if dry_run else '기록'} 완료. repo {len(repos)}개, 파일 {len(files)}개, 실패 repo {len(failed)}개, 필수 누락 파일 {len(required_missing_files)}개.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Snapshot", payload.get("snapshot_id", "-"), label_ko="스냅샷"),
                ui_metric("Repos", len(repos), label_ko="Repo"),
                ui_metric("Files", len(files), label_ko="파일"),
                ui_metric(
                    "Required missing",
                    len(required_missing_files),
                    label_ko="필수 누락",
                    tone="warn" if required_missing_files else "ok",
                ),
                ui_metric("Optional missing", len(optional_missing_files), label_ko="선택 누락"),
                ui_metric("Dry run", bool_word(dry_run), label_ko="Dry run"),
            ],
        ),
        ui_block("records", "Repo backups", "Bundle status by repo.", title_ko="Repo 백업", summary_ko="Repo별 bundle 상태입니다.", tone="info", rows=rows),
    ]
    if file_rows:
        blocks.append(
            ui_block(
                "records",
                "Context files",
                "Missing optional re-entry files are recorded separately from required project context files.",
                title_ko="Context 파일",
                summary_ko="선택 re-entry 파일 누락은 필수 프로젝트 context 누락과 분리해서 표시합니다.",
                tone="warn" if required_missing_files else "info",
                rows=file_rows,
            )
        )
    return blocks


def build_metadata_sync_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    repos = payload.get("repo_results") if isinstance(payload.get("repo_results"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    direction = str(payload.get("direction") or "sync")
    project_id = str(payload.get("project_id") or "-")
    write = bool(payload.get("write"))
    preview_only = bool(payload.get("read_only")) or not write
    failed = Number(summary.get("failed_repo_count"))
    synced = Number(summary.get("synced_repo_count"))
    would_sync = Number(summary.get("would_sync_count"))

    rows: list[dict[str, Any]] = []
    for item in repos[:20]:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "-")
        item_tone = "warn"
        if not bool(item.get("ok")):
            item_tone = "error"
        elif status.startswith("would_"):
            item_tone = "info"
        elif bool(item.get("synced")) or status in {"synced", "fetched", "pushed", "already_current", "up_to_date"}:
            item_tone = "ok"
        rows.append(
            ui_row(
                str(item.get("repo_id") or item.get("display_name") or "Repo"),
                str(item.get("remote_url") or ""),
                tone=item_tone,
                meta=[
                    f"status {status}",
                    f"mode {'preview' if preview_only else 'write'}",
                    f"source {item.get('remote_source', '-')}",
                    f"local_refs {item.get('local_ref_count', 0)}",
                    f"remote_refs {item.get('remote_ref_count', 0)}",
                ],
            )
        )

    tone = "error" if failed else "info" if preview_only and would_sync else "ok"
    if failed:
        summary_en = f"{direction} failed for {failed} of {len(repos)} repos; no failed repo should be treated as reproducible metadata."
        summary_ko = f"{direction} repo {len(repos)}개 중 {failed}개 실패. 실패 repo는 재현성 metadata로 간주하면 안 됩니다."
    elif preview_only and would_sync:
        summary_en = f"Preview only: {would_sync} repos would update metadata refs; no refs were changed."
        summary_ko = f"미리보기 전용: repo {would_sync}개 metadata ref 갱신 예정이며 실제 ref는 변경하지 않았습니다."
    elif preview_only:
        summary_en = f"Preview only: {direction} checked {len(repos)} repos and found no metadata ref writes to perform."
        summary_ko = f"미리보기 전용: {direction} repo {len(repos)}개 확인, 실행할 metadata ref 쓰기 없음."
    else:
        summary_en = f"{direction} wrote metadata refs for {synced} of {len(repos)} repos; failed {failed}."
        summary_ko = f"{direction} repo {len(repos)}개 중 {synced}개 metadata ref 기록, 실패 {failed}."

    blocks = [
        ui_block(
            "judgement",
            "Metadata sync result",
            summary_en,
            title_ko="메타데이터 동기화 결과",
            summary_ko=summary_ko,
            tone=tone,
            metrics=[
                ui_metric("Project", project_id, label_ko="프로젝트"),
                ui_metric("Mode", "preview" if preview_only else "write", label_ko="모드", tone="info" if preview_only else "warn"),
                ui_metric("Direction", direction, label_ko="방향"),
                ui_metric("Repos", len(repos), label_ko="Repo"),
                ui_metric("Synced", synced, label_ko="동기화됨"),
                ui_metric("Would sync", would_sync, label_ko="동기화 예정", tone="info" if would_sync else "neutral"),
                ui_metric("Local refs", summary.get("local_ref_count", 0), label_ko="Local refs"),
                ui_metric("Remote refs", summary.get("remote_ref_count", 0), label_ko="Remote refs"),
                ui_metric("Failed", failed, label_ko="실패", tone="error" if failed else "neutral"),
            ],
        ),
        ui_block("records", "Repo metadata refs", "Metadata refs by repo and selected remote.", title_ko="Repo 메타데이터 refs", summary_ko="Repo별 metadata ref와 선택된 remote입니다.", tone="info", rows=rows),
    ]
    if preview_only and would_sync and not failed:
        blocks.append(
            ui_block(
                "next_actions",
                "Optional approved write",
                "The preview found remote metadata refs to fetch. Run the write form only during an approved active operation.",
                title_ko="선택적 승인 쓰기",
                summary_ko="미리보기에서 가져올 remote metadata ref를 발견했습니다. 승인된 활성 작업 중에만 write 형태를 실행하세요.",
                tone="info",
                actions=[
                    ui_row(
                        f"project-snapshot-metadata-sync --project {project_id} --direction {direction} --write --yes",
                        "Updates local metadata refs from the approved remote; keep this out of unattended away execution unless explicitly preapproved.",
                        detail_ko="승인된 remote에서 local metadata ref를 갱신합니다. 명시적 사전 승인이 없다면 자리비움 자동 실행 범위에 넣지 마세요.",
                        tone="warn",
                        meta=["state-changing", "approval required"],
                    )
                ],
            )
        )
    return blocks


def build_attention_resolution_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    counts = payload.get("attention_severity_counts") if isinstance(payload.get("attention_severity_counts"), dict) else {}
    tone = attention_tone(counts, ok=Number(payload.get("attention_count")) == 0)
    status_en, status_ko = status_label_for_tone(tone)
    attention_count = Number(payload.get("attention_count"))
    step_count = Number(payload.get("resolution_step_count"))
    approval_count = Number(payload.get("approval_required_count"))
    blocked_count = Number(payload.get("blocked_count"))
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    safe_count = Number(summary.get("safe_command_count"))
    blocks = [
        ui_block(
            "judgement",
            "Attention resolution plan",
            f"{status_en}: {attention_count} attention items mapped to {step_count} review steps; {approval_count} fixes need approval.",
            title_ko="주의 항목 해결 계획",
            summary_ko=f"{status_ko}: 주의 항목 {attention_count}개를 해결 단계 {step_count}개로 정리했고, 승인 필요 수정은 {approval_count}개입니다.",
            tone=tone,
            metrics=[
                ui_metric("Projects", payload.get("project_count", 0), label_ko="프로젝트"),
                ui_metric("Attention", attention_count, label_ko="주의 항목", tone=tone),
                ui_metric("Steps", step_count, label_ko="해결 단계"),
                ui_metric("Safe checks", safe_count, label_ko="안전 확인"),
                ui_metric("Approval fixes", approval_count, label_ko="승인 필요 수정", tone="warn" if approval_count else "ok"),
                ui_metric("Blocked", blocked_count, label_ko="차단", tone="error" if blocked_count else "ok"),
            ],
        )
    ]

    rows: list[dict[str, Any]] = []
    steps = payload.get("steps")
    if isinstance(steps, list):
        for step in steps[:16]:
            if not isinstance(step, dict):
                continue
            severity = str(step.get("severity") or "")
            state = str(step.get("state") or "")
            row_tone = "error" if state == "blocked_review" else "warn" if state in {"review", "approval_required"} else "info"
            title = f"{step.get('project_id', '-')}: {step.get('kind', 'attention')}"
            detail = str(step.get("operator_summary") or step.get("message") or "")
            meta = [
                value
                for value in [
                    severity,
                    state,
                    str(step.get("plan_type") or ""),
                    str(step.get("repo_id") or ""),
                ]
                if value
            ]
            rows.append(ui_row(title, detail, tone=row_tone, meta=meta))
    if rows:
        blocks.append(
            ui_block(
                "findings",
                "Resolution steps",
                "Each row names the issue, the review state, and what to inspect first.",
                title_ko="해결 단계",
                summary_ko="각 행은 문제, 검토 상태, 먼저 확인할 내용을 보여줍니다.",
                tone=tone,
                rows=rows,
            )
        )

    action_rows: list[dict[str, Any]] = []
    next_safe = payload.get("next_safe_commands")
    if isinstance(next_safe, list):
        for command in next_safe[:8]:
            action_rows.append(
                ui_row(
                    str(command),
                    "Read-only or preview command that can be run before approving a fix.",
                    detail_ko="수정을 승인하기 전에 실행할 수 있는 읽기 전용 또는 미리보기 명령입니다.",
                    tone="info",
                )
            )
    approval_commands = payload.get("approval_required_commands")
    if isinstance(approval_commands, list):
        for command in approval_commands[:6]:
            action_rows.append(
                ui_row(
                    str(command),
                    "Do not run automatically; this command changes local or online state.",
                    detail_ko="자동 실행하지 마세요. 이 명령은 로컬 또는 온라인 상태를 변경합니다.",
                    tone="warn",
                    meta=["approval required"],
                )
            )
    if action_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Safe checks and gated fixes",
                "Start with safe checks; run gated fixes only after explicit approval.",
                title_ko="안전 확인과 승인 필요 수정",
                summary_ko="먼저 안전 확인을 실행하고, 상태 변경 명령은 명시적 승인 후에만 실행하세요.",
                tone="info",
                actions=action_rows,
            )
        )
    return blocks


def build_attention_apply_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    dry_run = bool(payload.get("dry_run", True))
    confirmation_required = bool(payload.get("confirmation_required"))
    failed = Number(payload.get("failed_count"))
    skipped = Number(payload.get("skipped_count"))
    before = Number(payload.get("before_attention_count"))
    after = Number(payload.get("after_attention_count"))
    tone = "error" if failed else "warn" if confirmation_required or skipped or after else "ok"
    status_en, status_ko = status_label_for_tone(tone)
    mode_en = "Preview" if dry_run else "Apply"
    mode_ko = "미리보기" if dry_run else "적용"
    blocks = [
        ui_block(
            "judgement",
            "Attention fix preview" if dry_run else "Attention fix result",
            f"{mode_en}: {before} before, {after} after, skipped {skipped}, failed {failed}.",
            title_ko="주의 해결 미리보기" if dry_run else "주의 해결 결과",
            summary_ko=f"{mode_ko}: 이전 {before}, 이후 {after}, 건너뜀 {skipped}, 실패 {failed}.",
            tone=tone,
            metrics=[
                ui_metric("Status", status_en, label_ko="상태"),
                ui_metric("Before", before, label_ko="이전"),
                ui_metric("After", after, label_ko="이후"),
                ui_metric("Planned", payload.get("planned_command_count", 0), label_ko="계획"),
                ui_metric("Skipped", skipped, label_ko="건너뜀", tone="warn" if skipped else "neutral"),
                ui_metric("Failed", failed, label_ko="실패", tone="error" if failed else "neutral"),
            ],
        )
    ]

    action_rows: list[dict[str, Any]] = []
    actions = payload.get("actions")
    if isinstance(actions, list):
        for action in actions[:12]:
            if not isinstance(action, dict):
                continue
            commands = action.get("commands")
            command_count = len(commands) if isinstance(commands, list) else 0
            status = str(action.get("status") or "")
            row_tone = "ok" if status == "applied" else "info" if status == "previewed" else "warn"
            action_rows.append(
                ui_row(
                    f"{action.get('project_id', '-')}: {action.get('kind', '-')}",
                    str(action.get("reason") or ""),
                    tone=row_tone,
                    meta=[value for value in [status, f"commands {command_count}"] if value],
                )
            )
    skipped_rows: list[dict[str, Any]] = []
    skipped_items = payload.get("skipped")
    if isinstance(skipped_items, list):
        for item in skipped_items[:8]:
            if not isinstance(item, dict):
                continue
            skipped_rows.append(
                ui_row(
                    f"{item.get('project_id', '-')}: {item.get('kind', '-')}",
                    str(item.get("reason") or item.get("message") or ""),
                    tone="warn",
                    meta=[str(item.get("severity") or "")] if item.get("severity") else [],
                )
            )
    if action_rows or skipped_rows:
        blocks.append(
            ui_block(
                "records",
                "Fix steps",
                "What CLUTCH can preview or apply for the current attention items.",
                title_ko="해결 단계",
                summary_ko="현재 주의 항목에 대해 CLUTCH가 미리보기 또는 적용할 수 있는 단계입니다.",
                tone=tone,
                rows=[*action_rows, *skipped_rows],
            )
        )

    apply_hint = str(payload.get("apply_command_hint") or "")
    if apply_hint:
        blocks.append(
            ui_block(
                "next_actions",
                "Terminal apply command",
                "Run this only when you want CLUTCH to apply the planned fixes.",
                title_ko="터미널 적용 명령",
                summary_ko="계획된 해결을 실제 적용하려면 이 명령을 터미널에서 실행하세요.",
                tone="info",
                actions=[
                    ui_row(
                        apply_hint,
                        "Requires explicit terminal execution; web console remains preview-only here.",
                        detail_ko="명시적으로 터미널에서 실행해야 합니다. 웹 콘솔에서는 여기까지 미리보기입니다.",
                        tone="info",
                    )
                ],
            )
        )
    return blocks


def operator_intent_status_tone(status: str) -> str:
    if status == "pending":
        return "info"
    if status == "consumed":
        return "ok"
    if status in {"expired", "superseded"}:
        return "warn"
    return "neutral"


def build_operator_intents_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    intents = payload.get("intents") if isinstance(payload.get("intents"), list) else []
    status_counts: dict[str, int] = {}
    normalized_intents: list[dict[str, Any]] = []
    for item in intents:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "pending")
        status_counts[status] = status_counts.get(status, 0) + 1
        normalized_intents.append(item)

    pending_count = Number(payload.get("pending_intent_count", status_counts.get("pending", 0)))
    expired_count = status_counts.get("expired", 0)
    consumed_count = status_counts.get("consumed", 0)
    total_count = Number(payload.get("intent_count", len(normalized_intents)))
    latest_intent = normalized_intents[0] if normalized_intents else {}
    latest_status = str(latest_intent.get("status") or "-")
    latest_type = str(latest_intent.get("intent_type") or "-")
    latest_expires = str(latest_intent.get("expires_at_local") or "-")
    tone = "warn" if latest_status == "expired" else "info" if pending_count else "ok"

    rows: list[dict[str, Any]] = []
    for item in normalized_intents[:12]:
        status = str(item.get("status") or "pending")
        meta = [
            value
            for value in [
                f"status {status}",
                f"id {item.get('intent_id', '-')}",
                f"created {item.get('created_at_local', '-')}",
                f"expires {item.get('expires_at_local', '-')}",
                str(item.get("source_web_command") or ""),
            ]
            if value
        ]
        rows.append(
            ui_row(
                str(item.get("intent_type") or "operator_intent"),
                str(item.get("objective") or ""),
                title_ko=str(item.get("intent_type") or "operator_intent"),
                detail_ko=str(item.get("objective") or ""),
                tone=operator_intent_status_tone(status),
                meta=meta,
            )
        )

    actions: list[dict[str, Any]] = []
    if pending_count:
        pending = next((item for item in normalized_intents if str(item.get("status") or "pending") == "pending"), {})
        pending_type = str(pending.get("intent_type") or "")
        if pending_type.startswith("away_"):
            actions.append(
                ui_row(
                    "Tell Codex `자리비움 개발해` when the active away plan still matches your objective.",
                    "This consumes no authority by itself; Codex still checks the away plan, stop conditions, and current prompt.",
                    title_ko="활성 away plan이 현재 목표와 맞으면 Codex에게 `자리비움 개발해`라고 지시하세요.",
                    detail_ko="이 intent 자체가 권한을 추가하지는 않습니다. Codex가 away plan, 중단 조건, 현재 지시를 다시 확인합니다.",
                    tone="info",
                    meta=["operator step"],
                )
            )
            project_id = str(payload.get("project_id") or "")
            if project_id:
                actions.append(
                    ui_row(
                        f"python3 scripts/clutch_ctl.py project-away-work --project {project_id} --include-plan-text --json",
                        "Read-only check of the active away plan and pending intent before continuing.",
                        detail_ko="계속하기 전에 활성 away plan과 대기 intent를 읽기 전용으로 확인합니다.",
                        tone="info",
                        meta=["terminal command", "read-only/check"],
                    )
                )
        elif pending_type == "collab_delegate":
            actions.append(
                ui_row(
                    "Tell Codex the concrete worker task, for example `서브에게 맡겨: ...`.",
                    "The web intent only records the handoff boundary; Codex decides and routes the actual collab request.",
                    title_ko="Codex에게 구체적인 worker 작업을 지시하세요. 예: `서브에게 맡겨: ...`",
                    detail_ko="웹 intent는 handoff 경계만 기록합니다. 실제 collab 요청 판단과 라우팅은 Codex가 수행합니다.",
                    tone="info",
                    meta=["operator step"],
                )
            )
        else:
            actions.append(
                ui_row(
                    "Tell Codex the concrete natural-language task that should use this pending intent.",
                    "The pending intent is durable context, not an automatic executor.",
                    title_ko="이 pending intent를 사용할 구체적인 자연어 작업을 Codex에게 말하세요.",
                    detail_ko="pending intent는 durable context이며 자동 실행기가 아닙니다.",
                    tone="info",
                    meta=["operator step"],
                )
            )
    elif latest_status == "expired":
        actions.append(
            ui_row(
                "Create a fresh intent before relying on this queue.",
                "The newest recorded intent expired, so the next Codex prompt should not treat it as active authority.",
                title_ko="이 queue를 근거로 삼기 전에 fresh intent를 새로 만드세요.",
                detail_ko="가장 최근 intent가 만료되었으므로 다음 Codex 지시가 이를 active authority로 취급하면 안 됩니다.",
                tone="warn",
                meta=["operator step"],
            )
        )
    else:
        actions.append(
            ui_row(
                "No pending operator intent is waiting.",
                "Use Prepare Away or an advanced intent button only when durable handoff context is useful.",
                title_ko="대기 중인 operator intent가 없습니다.",
                detail_ko="durable handoff context가 필요할 때만 자리비움 준비 또는 고급 intent 버튼을 사용하세요.",
                tone="info",
                meta=["operator step"],
            )
        )

    blocks = [
        ui_block(
            "judgement",
            "Operator intent queue",
            f"{pending_count} pending of {total_count} recent operator intents; latest is {latest_type}/{latest_status}.",
            title_ko="운영자 intent queue",
            summary_ko=f"최근 operator intent {total_count}개 중 대기 {pending_count}개입니다. 최신 상태는 {latest_type}/{latest_status}입니다.",
            tone=tone,
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
                ui_metric("Pending", pending_count, label_ko="대기", tone="info" if pending_count else "neutral"),
                ui_metric("Expired", expired_count, label_ko="만료", tone="warn" if latest_status == "expired" else "neutral"),
                ui_metric("Consumed", consumed_count, label_ko="사용됨"),
                ui_metric("Total shown", total_count, label_ko="표시 합계"),
                ui_metric("Latest status", latest_status, label_ko="최신 상태", tone=operator_intent_status_tone(latest_status)),
                ui_metric("Latest expiry", latest_expires, label_ko="최신 만료"),
            ],
        )
    ]
    if rows:
        blocks.append(
            ui_block(
                "records",
                "Recent intents",
                "Machine-local durable operator intents by most recent file update.",
                title_ko="최근 intent",
                summary_ko="machine-local durable operator intent를 최신 파일 순서로 표시합니다.",
                tone="info",
                rows=rows,
            )
        )
    blocks.append(
        ui_block(
            "next_actions",
            "Intent lifecycle next step",
            "Use the intent as context for the next Codex prompt; the web console does not execute the prompt itself.",
            title_ko="Intent lifecycle 다음 단계",
            summary_ko="이 intent는 다음 Codex 프롬프트의 context입니다. 웹 콘솔이 프롬프트를 직접 실행하지는 않습니다.",
            tone="info",
            actions=actions,
        )
    )
    return blocks


def build_operator_intent_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    intent = payload.get("intent") if isinstance(payload.get("intent"), dict) else {}
    allowed = intent.get("allowed_scope") if isinstance(intent.get("allowed_scope"), list) else []
    verification = intent.get("verification_commands") if isinstance(intent.get("verification_commands"), list) else []
    stops = intent.get("stop_conditions") if isinstance(intent.get("stop_conditions"), list) else []
    rows = [
        ui_row(
            str(intent.get("intent_type") or "operator_intent"),
            str(intent.get("objective") or ""),
            title_ko=str(intent.get("intent_type") or "operator_intent"),
            detail_ko=str(intent.get("objective") or ""),
            tone="info",
            meta=[
                f"id {intent.get('intent_id', '-')}",
                f"status {intent.get('status', '-')}",
                f"expires {intent.get('expires_at_local', '-')}",
            ],
        )
    ]
    for item in allowed[:5]:
        rows.append(ui_row("Allowed scope", str(item), title_ko="허용 범위", detail_ko=str(item), tone="neutral"))
    action_rows = [
        ui_row("Next prompt", str(payload.get("recommended_next_prompt") or ""), title_ko="다음 프롬프트", detail_ko=str(payload.get("recommended_next_prompt") or ""), tone="info")
    ]
    for item in verification[:5]:
        action_rows.append(ui_row("Verification", str(item), title_ko="검증", detail_ko=str(item), tone="neutral"))
    for item in stops[:5]:
        action_rows.append(ui_row("Stop condition", str(item), title_ko="중단 조건", detail_ko=str(item), tone="warn"))
    return [
        ui_block(
            "judgement",
            "Operator intent recorded",
            "A durable CLUTCH operator intent was recorded for the selected project.",
            title_ko="운영자 intent 기록",
            summary_ko="선택 프로젝트의 CLUTCH 운영자 intent를 로컬 상태에 기록했습니다.",
            tone="ok" if payload.get("wrote") else "info",
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
                ui_metric("Wrote", bool(payload.get("wrote")), label_ko="기록"),
                ui_metric("Pending", payload.get("pending_intent_count", 0), label_ko="대기 intent"),
            ],
            rows=rows,
        ),
        ui_block(
            "next_actions",
            "Next Codex prompt",
            "Use the next natural-language prompt to tell Codex what to do with this intent.",
            title_ko="다음 Codex 프롬프트",
            summary_ko="다음 자연어 지시에서 Codex에게 이 intent로 무엇을 할지 말하세요.",
            tone="info",
            actions=action_rows,
        ),
    ]


def build_checkpoint_workflow_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    steps = payload.get("steps") if isinstance(payload.get("steps"), list) else []
    required_failed = sum(1 for item in steps if isinstance(item, dict) and item.get("required") and not item.get("ok"))
    project_id = str(payload.get("project_id") or "")
    rows = []
    for item in steps:
        if not isinstance(item, dict):
            continue
        rows.append(
            ui_row(
                str(item.get("label") or item.get("command_key") or "step"),
                str(item.get("operator_summary") or item.get("command") or ""),
                title_ko=str(item.get("label_ko") or item.get("label") or item.get("command_key") or "단계"),
                detail_ko=str(item.get("operator_summary_ko") or item.get("operator_summary") or item.get("command") or ""),
                tone="ok" if item.get("ok") else "warn",
                meta=[
                    f"return {item.get('returncode')}",
                    "required" if item.get("required") else "optional",
                ],
            )
        )
    blocks = [
        ui_block(
            "judgement",
            "Checkpoint workflow",
            "Created a machine-local backup and reproducibility manifest for this project.",
            title_ko="체크포인트 workflow",
            summary_ko="이 프로젝트의 machine-local backup과 재현 manifest를 생성했습니다.",
            tone="warn" if required_failed else "ok",
            metrics=[
                ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
                ui_metric("Steps", len(steps), label_ko="단계"),
                ui_metric("Required failed", required_failed, label_ko="필수 실패", tone="warn" if required_failed else "neutral"),
            ],
            rows=rows,
        )
    ]
    if project_id and not required_failed:
        blocks.append(
            ui_block(
                "next_actions",
                "Suggested checkpoint checks",
                "Use these read-only checks before relying on this checkpoint for recovery or publication.",
                title_ko="권장 체크포인트 점검",
                summary_ko="이 체크포인트를 복구나 publish 근거로 쓰기 전에 아래 읽기 전용 점검을 실행하세요.",
                tone="info",
                actions=rows_from_next_actions(
                    [
                        f"python3 scripts/clutch_ctl.py project-restore-readiness --project {project_id} --json",
                        f"python3 scripts/clutch_ctl.py project-versioning-readiness --project {project_id} --json",
                        f"python3 scripts/clutch_ctl.py project-artifact-pointers --project {project_id} --json",
                    ],
                    limit=3,
                ),
            )
        )
    return blocks


def build_generic_summary_blocks(command_key: str, payload: dict[str, Any], *, ok: bool) -> list[dict[str, Any]]:
    counts = payload.get("attention_severity_counts") if isinstance(payload.get("attention_severity_counts"), dict) else {}
    findings = rows_from_findings(payload.get("findings") or payload.get("attention_items"))
    actions = rows_from_next_actions(payload.get("next_actions"))
    tone = attention_tone(counts, ok=ok) if counts else ("ok" if ok else "warn")
    metrics = [
        ui_metric("Schema", payload.get("schema", "-"), label_ko="Schema"),
        ui_metric("OK", bool_word(payload.get("ok", ok)), label_ko="정상"),
        ui_metric("Status", payload.get("status", "-"), label_ko="상태"),
        ui_metric("Project", payload.get("project_id", "-"), label_ko="프로젝트"),
        ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
    ]
    blocks = [
        ui_block(
            "judgement",
            "Command judgement",
            f"{command_key}: CLUTCH returned {'ok' if ok else 'review'} with schema {payload.get('schema', '-')}.",
            title_ko="명령 판단",
            summary_ko=f"{command_key}: CLUTCH가 {'정상' if ok else '확인 필요'} 결과를 반환했습니다. schema {payload.get('schema', '-')}.",
            tone=tone,
            metrics=metrics,
        )
    ]
    if findings:
        blocks.append(ui_block("findings", "Findings", "Findings returned by the command.", title_ko="점검 항목", summary_ko="명령이 반환한 점검 항목입니다.", tone=tone, rows=findings))
    if actions:
        blocks.append(ui_block("next_actions", "Suggested next checks", "Follow-up actions returned by the command.", title_ko="권장 다음 확인", summary_ko="명령이 반환한 후속 작업입니다.", tone="info", actions=actions))
    return blocks


def integrity_label(value: Any, *, present: Any = True) -> str:
    if not bool(present):
        return "missing"
    return "ok" if bool(value) else "review"


def integrity_tone(value: Any, *, present: Any = True) -> str:
    if not bool(present):
        return "warn"
    return "ok" if bool(value) else "warn"


def build_web_console_status_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    health = payload.get("health") if isinstance(payload.get("health"), dict) else {}
    processes = payload.get("processes") if isinstance(payload.get("processes"), list) else []
    status = str(payload.get("status") or health.get("status") or "-")
    running = bool(payload.get("running"))
    ready = bool(payload.get("ready"))
    version_matches = health.get("version_matches")
    registry_present = health.get("command_registry_integrity_present", True)
    registry_ok = health.get("command_registry_integrity_ok")
    surface_present = health.get("command_surface_integrity_present", True)
    surface_ok = health.get("command_surface_integrity_ok")
    render_present = health.get("command_surface_render_ready_present")
    render_ready = health.get("command_surface_render_ready")
    render_ok = True if render_present is None else render_ready is not False
    render_label = "-" if render_present is None else integrity_label(render_ready, present=render_present)
    render_tone = "neutral" if render_present is None else integrity_tone(render_ready, present=render_present)
    integrity_ok = registry_ok is not False and surface_ok is not False and render_ok
    version_ok = version_matches is not False
    tone = "ok" if ready and version_ok and integrity_ok else "warn" if running else "error"
    status_en, status_ko = status_label_for_tone(tone)
    process_count = Number(payload.get("process_count", len(processes)))
    process_version = health.get("process_version") or "-"
    expected_version = payload.get("expected_version") or health.get("expected_version") or "-"
    version_aligned_value = "-" if version_matches is None else bool_word(version_matches)
    if tone == "ok":
        summary_en = "Local Web console is ready, version-aligned, and command surface checks passed."
        summary_ko = "로컬 Web 콘솔이 준비되었고 버전과 명령 표면 점검이 정렬되어 있습니다."
    elif running:
        summary_en = "Local Web console is running but needs review before operators trust this surface."
        summary_ko = "로컬 Web 콘솔이 실행 중이지만 운영자가 이 화면을 신뢰하기 전에 확인이 필요합니다."
    else:
        summary_en = "Local Web console is not running on the configured local endpoint."
        summary_ko = "설정된 로컬 endpoint에서 Web 콘솔이 실행 중이지 않습니다."

    process_tone = "ok" if process_count == 1 and running else "warn" if process_count != 1 else "neutral"
    blocks = [
        ui_block(
            "judgement",
            "Web console status",
            f"{status_en}: {summary_en}",
            title_ko="Web 콘솔 상태",
            summary_ko=f"{status_ko}: {summary_ko}",
            tone=tone,
            metrics=[
                ui_metric("URL", payload.get("url", "-"), label_ko="URL"),
                ui_metric("Status", status, label_ko="상태", tone=tone),
                ui_metric("Running", bool_word(running), label_ko="실행 중", tone="ok" if running else "warn"),
                ui_metric("Ready", bool_word(ready), label_ko="준비", tone="ok" if ready else "warn"),
                ui_metric("Processes", process_count, label_ko="프로세스", tone=process_tone),
                ui_metric(
                    "Version aligned",
                    version_aligned_value,
                    label_ko="버전 정렬",
                    tone="ok" if version_matches is True else "warn" if version_matches is False else "neutral",
                ),
                ui_metric(
                    "Process version",
                    process_version,
                    label_ko="프로세스 버전",
                    tone="ok" if version_matches is True else "warn" if version_matches is False else "neutral",
                ),
                ui_metric("Expected", expected_version, label_ko="기대 버전"),
                ui_metric("Commands", Number(health.get("command_count")), label_ko="명령"),
                ui_metric("Default", Number(health.get("default_command_count")), label_ko="기본"),
                ui_metric("Advanced", Number(health.get("advanced_command_count")), label_ko="고급"),
                ui_metric(
                    "Registry integrity",
                    integrity_label(registry_ok, present=registry_present),
                    label_ko="Registry 무결성",
                    tone=integrity_tone(registry_ok, present=registry_present),
                ),
                ui_metric(
                    "Surface integrity",
                    integrity_label(surface_ok, present=surface_present),
                    label_ko="표면 무결성",
                    tone=integrity_tone(surface_ok, present=surface_present),
                ),
                ui_metric(
                    "Render ready",
                    render_label,
                    label_ko="렌더 준비",
                    tone=render_tone,
                ),
            ],
        )
    ]

    rows = []
    for item in processes[:8]:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("pid") or "-")
        host = str(item.get("host") or payload.get("host") or "-")
        port = str(item.get("port") or payload.get("port") or "-")
        command = str(item.get("command") or "")
        rows.append(
            ui_row(
                f"pid {pid}",
                command,
                title_ko=f"pid {pid}",
                detail_ko=command,
                tone="ok" if ready else "info" if running else "warn",
                meta=[f"host {host}", f"port {port}"],
            )
        )
    if rows:
        blocks.append(
            ui_block(
                "records",
                "Web console processes",
                "Process candidates matching the configured local Web console endpoint.",
                title_ko="Web 콘솔 프로세스",
                summary_ko="설정된 로컬 Web 콘솔 endpoint와 일치하는 프로세스 후보입니다.",
                tone="info",
                rows=rows,
            )
        )

    def compact_string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        result: list[str] = []
        for item in value:
            text = str(item or "").strip()
            if text and text not in result:
                result.append(text)
        return result

    command_surface_rows = []
    default_command_keys = compact_string_list(health.get("default_command_keys"))
    if default_command_keys:
        command_surface_rows.append(
            ui_row(
                "Default commands",
                ", ".join(default_command_keys),
                title_ko="기본 명령",
                detail_ko=", ".join(default_command_keys),
                tone="info",
            )
        )
    preview_only_default_command_keys = compact_string_list(health.get("preview_only_default_command_keys"))
    if preview_only_default_command_keys:
        command_surface_rows.append(
            ui_row(
                "Default previews",
                ", ".join(preview_only_default_command_keys),
                title_ko="기본 미리보기",
                detail_ko=", ".join(preview_only_default_command_keys),
                tone="info",
            )
        )
    attention_shortcuts = health.get("attention_shortcuts") if isinstance(health.get("attention_shortcuts"), dict) else {}
    kind_commands = (
        attention_shortcuts.get("kind_commands", {})
        if isinstance(attention_shortcuts.get("kind_commands"), dict)
        else {}
    )
    repo_sync_shortcuts = compact_string_list(kind_commands.get("repo_sync"))
    if repo_sync_shortcuts:
        command_surface_rows.append(
            ui_row(
                "Repo sync shortcuts",
                ", ".join(repo_sync_shortcuts),
                title_ko="Repo sync shortcut",
                detail_ko=", ".join(repo_sync_shortcuts),
                tone="info",
            )
        )
    if command_surface_rows:
        blocks.append(
            ui_block(
                "records",
                "Command surface summary",
                "Compact command-surface keys exposed by the active Web backend health endpoint.",
                title_ko="명령 표면 요약",
                summary_ko="활성 Web backend health endpoint가 노출한 명령 표면 키 요약입니다.",
                tone="info",
                rows=command_surface_rows,
            )
        )

    details = str(health.get("details") or "").strip()
    if details:
        blocks.append(
            ui_block(
                "records",
                "Health details",
                "Backend readiness details returned by the Web health endpoint.",
                title_ko="Health 세부 정보",
                summary_ko="Web health endpoint가 반환한 backend readiness 세부 정보입니다.",
                tone="info" if tone == "ok" else tone,
                rows=[
                    ui_row(
                        "details",
                        details,
                        title_ko="세부 정보",
                        detail_ko=details,
                        tone="info" if tone == "ok" else tone,
                    )
                ],
            )
        )

    action_rows = rows_from_next_actions(payload.get("next_actions"))
    if action_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Suggested next checks",
                "Follow these checks to recover or confirm the local Web console.",
                title_ko="권장 다음 확인",
                summary_ko="아래 항목으로 로컬 Web 콘솔을 복구하거나 상태를 확인하세요.",
                tone="info" if tone == "ok" else "warn",
                actions=action_rows,
            )
        )
    return blocks


def build_web_console_browser_smoke_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    screenshot = payload.get("screenshot") if isinstance(payload.get("screenshot"), dict) else {}
    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    browser = payload.get("browser") if isinstance(payload.get("browser"), dict) else {}
    browser_attempts = payload.get("browser_attempts") if isinstance(payload.get("browser_attempts"), list) else []
    status = str(payload.get("status") or "-")
    passed = bool(payload.get("passed"))
    skipped = bool(payload.get("skipped"))
    if passed:
        tone = "ok"
        summary_en = "Headless browser smoke captured a nonblank Web console screenshot."
        summary_ko = "Headless 브라우저 smoke가 비어 있지 않은 Web 콘솔 screenshot을 캡처했습니다."
    elif skipped:
        tone = "info"
        if browser_attempts or browser:
            summary_en = "Browser smoke was skipped because available browser commands did not produce a screenshot."
            summary_ko = "사용 가능한 브라우저 명령이 screenshot을 만들지 못해 browser smoke를 건너뛰었습니다."
        else:
            summary_en = "Browser smoke was skipped because no compatible browser was available on this machine."
            summary_ko = "이 머신에서 호환 브라우저를 찾지 못해 browser smoke를 건너뛰었습니다."
    else:
        tone = "warn"
        summary_en = "Browser smoke did not prove the Web console visual surface."
        summary_ko = "Browser smoke가 Web 콘솔 시각 표면을 증명하지 못했습니다."
    status_en, status_ko = status_label_for_tone(tone)
    width = Number(screenshot.get("width"))
    height = Number(screenshot.get("height"))
    dimensions = f"{width}x{height}" if width or height else "-"
    nonwhite_ratio = screenshot.get("nonwhite_ratio", 0)
    try:
        nonwhite_percent = f"{float(nonwhite_ratio) * 100:.2f}%"
    except (TypeError, ValueError):
        nonwhite_percent = "-"
    blocks = [
        ui_block(
            "judgement",
            "Browser smoke",
            f"{status_en}: {summary_en}",
            title_ko="브라우저 Smoke",
            summary_ko=f"{status_ko}: {summary_ko}",
            tone=tone,
            metrics=[
                ui_metric("Status", status, label_ko="상태", tone=tone),
                ui_metric("URL", payload.get("url") or "-", label_ko="URL"),
                ui_metric(
                    "Browser",
                    browser.get("name") or Path(str(browser.get("path") or "")).name or "-",
                    label_ko="브라우저",
                    tone="ok" if browser else "info" if skipped else "warn",
                ),
                ui_metric("Attempts", Number(len(browser_attempts)), label_ko="시도 수", tone="info" if browser_attempts else "neutral"),
                ui_metric("Screenshot", "yes" if screenshot.get("exists") else "no", label_ko="Screenshot", tone="ok" if screenshot.get("exists") else "warn"),
                ui_metric("Dimensions", dimensions, label_ko="크기", tone="ok" if screenshot.get("dimensions_ok") else "warn"),
                ui_metric("Bytes", Number(screenshot.get("byte_count")), label_ko="바이트", tone="ok" if screenshot.get("file_size_ok") else "warn"),
                ui_metric(
                    "Nonwhite pixels",
                    nonwhite_percent,
                    label_ko="비흰색 픽셀",
                    tone="ok" if screenshot.get("nonwhite_ratio_ok") else "warn" if screenshot.get("pixel_analysis_ok") else "neutral",
                ),
                ui_metric(
                    "Distinct colors",
                    Number(screenshot.get("distinct_sampled_color_count")),
                    label_ko="색상 수",
                    tone="ok" if screenshot.get("distinct_color_ok") else "warn" if screenshot.get("pixel_analysis_ok") else "neutral",
                ),
            ],
        )
    ]
    check_rows = []
    for key, value in checks.items():
        label = str(key).replace("_", " ")
        check_rows.append(
            ui_row(
                label,
                "pass" if value else "not passed",
                title_ko=label,
                detail_ko="통과" if value else "미통과",
                tone="ok" if value else "info" if skipped and key == "browser_available" else "warn",
            )
        )
    if check_rows:
        blocks.append(
            ui_block(
                "records",
                "Smoke checks",
                "Browser, screenshot, dimensions, and image variation checks.",
                title_ko="Smoke 점검",
                summary_ko="브라우저, screenshot, 크기, 이미지 변화량 점검입니다.",
                tone=tone,
                rows=check_rows,
            )
        )
    evidence_rows = []
    if payload.get("command"):
        evidence_rows.append(ui_row("Command", str(payload.get("command")), title_ko="명령", detail_ko=str(payload.get("command")), tone="info"))
    if browser_attempts:
        attempt_summaries = []
        for index, attempt in enumerate(browser_attempts, start=1):
            if not isinstance(attempt, dict):
                continue
            attempt_browser = attempt.get("browser") if isinstance(attempt.get("browser"), dict) else {}
            browser_name = attempt_browser.get("name") or Path(str(attempt_browser.get("path") or "")).name or "browser"
            attempt_summaries.append(
                f"{index}. {browser_name}: {attempt.get('status') or '-'}"
                f" rc={attempt.get('returncode')}"
                f" screenshot={'yes' if attempt.get('screenshot_exists') else 'no'}"
            )
        if attempt_summaries:
            evidence_rows.append(
                ui_row(
                    "Browser attempts",
                    "; ".join(attempt_summaries[:5]),
                    title_ko="브라우저 시도",
                    detail_ko="; ".join(attempt_summaries[:5]),
                    tone="info" if skipped or passed else "warn",
                )
            )
    if screenshot.get("path"):
        evidence_rows.append(ui_row("Screenshot path", str(screenshot.get("path")), title_ko="Screenshot 경로", detail_ko=str(screenshot.get("path")), tone="info"))
    stderr = str(payload.get("stderr") or "").strip()
    if stderr and not passed:
        evidence_rows.append(ui_row("Browser stderr", stderr[:500], title_ko="브라우저 stderr", detail_ko=stderr[:500], tone="warn"))
    if evidence_rows:
        blocks.append(
            ui_block(
                "evidence",
                "Browser evidence",
                "Screenshot command and output evidence for release validation.",
                title_ko="브라우저 근거",
                summary_ko="Release 검증용 screenshot 명령과 출력 근거입니다.",
                tone="info" if passed or skipped else "warn",
                rows=evidence_rows,
            )
        )
    action_rows = rows_from_next_actions(payload.get("next_actions"))
    if action_rows:
        blocks.append(
            ui_block(
                "next_actions",
                "Suggested next checks",
                "Use these checks to complete or repair browser smoke validation.",
                title_ko="권장 다음 확인",
                summary_ko="Browser smoke 검증을 완료하거나 복구하려면 아래 항목을 확인하세요.",
                tone="info" if passed or skipped else "warn",
                actions=action_rows,
            )
        )
    return blocks


def compact_tag_value(tags: Any) -> str:
    if not isinstance(tags, list):
        return "-"
    clean_tags = [str(tag) for tag in tags if str(tag)]
    if not clean_tags:
        return "-"
    if len(clean_tags) == 1:
        return clean_tags[0]
    return f"{clean_tags[-1]} (+{len(clean_tags) - 1} more)"


def compact_exact_tag_meta(tags: Any) -> list[str]:
    if not isinstance(tags, list):
        return []
    clean_tags = [str(tag) for tag in tags if str(tag)]
    if not clean_tags:
        return []
    if len(clean_tags) == 1:
        return [f"exact tag {clean_tags[0]}"]
    return [f"latest exact tag {clean_tags[-1]}", f"exact tag count {len(clean_tags)}"]


def build_machine_version_state_summary_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    repos = payload.get("repos") if isinstance(payload.get("repos"), list) else []
    attention = Number(summary.get("attention_repo_count"))
    dirty = Number(summary.get("dirty_repo_count"))
    missing = Number(summary.get("missing_repo_count"))
    clean = Number(summary.get("clean_repo_count"))
    repo_count = Number(summary.get("repo_count"))
    alignment = str(summary.get("release_alignment_status") or "")
    alignment_needs_review = bool(alignment and alignment != "exact_tag_aligned")
    tone = "warn" if attention or alignment_needs_review or not payload.get("ok", True) else "ok"
    rows = []
    for item in repos[:12]:
        if not isinstance(item, dict):
            continue
        ahead_behind = item.get("ahead_behind") if isinstance(item.get("ahead_behind"), dict) else {}
        tags = item.get("exact_tags") if isinstance(item.get("exact_tags"), list) else []
        meta = [
            f"status {item.get('status', '-')}",
            f"branch {item.get('current_branch') or item.get('branch') or '-'}",
            f"head {item.get('head_short') or '-'}",
            f"ahead {ahead_behind.get('ahead')} behind {ahead_behind.get('behind')}",
        ]
        meta.extend(compact_exact_tag_meta(tags))
        rows.append(
            ui_row(
                str(item.get("repo_name") or "repo"),
                str(item.get("operator_summary") or item.get("path") or ""),
                title_ko=str(item.get("repo_name") or "repo"),
                detail_ko=str(item.get("operator_summary") or item.get("path") or ""),
                tone=str(item.get("operator_tone") or ("warn" if item.get("dirty") else "ok")),
                meta=meta,
            )
        )
    blocks = [
        ui_block(
            "judgement",
            "Machine version judgement",
            str(payload.get("operator_summary") or "Machine CLUTCH checkout state was inspected."),
            title_ko="머신 버전 판단",
            summary_ko=str(payload.get("operator_summary") or "이 PC의 CLUTCH checkout 상태를 확인했습니다."),
            tone=tone,
            metrics=[
                ui_metric("Machine", payload.get("machine_id", "-"), label_ko="머신"),
                ui_metric("Repos", repo_count, label_ko="Repo"),
                ui_metric("Clean", clean, label_ko="Clean"),
                ui_metric("Dirty", dirty, label_ko="Dirty", tone="warn" if dirty else "neutral"),
                ui_metric("Missing", missing, label_ko="Missing", tone="warn" if missing else "neutral"),
                ui_metric("Attention", attention, label_ko="주의", tone="warn" if attention else "neutral"),
                ui_metric("Release tags", summary.get("release_alignment_status", "-"), label_ko="Release tags"),
                ui_metric("Common tag", compact_tag_value(summary.get("common_exact_tags")), label_ko="공통 tag"),
            ],
        ),
        ui_block(
            "records",
            "Repo version records",
            "Local foundation, ops, and collab checkout state by repo.",
            title_ko="Repo 버전 기록",
            summary_ko="foundation, ops, collab 로컬 checkout 상태입니다.",
            tone="info",
            rows=rows,
        ),
    ]
    action_rows = rows_from_next_actions(payload.get("next_actions"))
    if action_rows:
        blocks.append(ui_block("next_actions", "Suggested next checks", "Use these checks to validate rollout parity across CLUTCH PCs.", title_ko="권장 다음 확인", summary_ko="아래 확인으로 CLUTCH PC 간 rollout 정렬을 검증하세요.", tone="info", actions=action_rows))
    return blocks


def build_command_summary_blocks(command_key: str, payload: Any, *, ok: bool, returncode: int) -> list[dict[str, Any]]:
    if payload is None:
        return [
            ui_block(
                "judgement",
                "Command output was not JSON",
                f"Return code {returncode}. Use Raw JSON/output for evidence.",
                title_ko="명령 출력이 JSON이 아닙니다",
                summary_ko=f"반환 코드 {returncode}. 근거는 Raw JSON/output에서 확인하세요.",
                tone="warn" if returncode else "info",
            )
        ]
    if isinstance(payload, list):
        return build_bindings_summary_blocks(payload)
    if not isinstance(payload, dict):
        return build_generic_summary_blocks(command_key, {"value": payload}, ok=ok)
    schema = str(payload.get("schema") or "")
    if command_key == "overview" or "overview" in schema:
        return build_overview_summary_blocks(payload)
    if "attention_resolution_plan" in schema or command_key in {"attention-resolution-plan", "project-attention-resolution-plan"}:
        return build_attention_resolution_summary_blocks(payload)
    if "attention_resolution_apply" in schema or command_key in {"attention-resolution-fix-preview", "project-attention-resolution-fix-preview"}:
        return build_attention_apply_summary_blocks(payload)
    if command_key == "bindings":
        return build_bindings_summary_blocks(payload.get("bindings", []))
    if command_key == "binding-check":
        return build_binding_check_summary_blocks(payload)
    if "reboot_readiness" in schema or command_key == "reboot-readiness":
        return build_reboot_readiness_summary_blocks(payload)
    if "machine_lifecycle_readiness" in schema or command_key == "machine-lifecycle-readiness":
        return build_machine_lifecycle_readiness_summary_blocks(payload)
    if "online_identity" in schema or command_key == "online-identity":
        return build_online_identity_summary_blocks(payload)
    if "machine_version_state" in schema or command_key == "machine-version-state":
        return build_machine_version_state_summary_blocks(payload)
    if "runtime_check" in schema or command_key == "runtime-check":
        return build_runtime_check_summary_blocks(payload)
    if "web_console_status" in schema or command_key == "web-console-status":
        return build_web_console_status_summary_blocks(payload)
    if "web_console_browser_smoke" in schema or command_key == "web-console-browser-smoke":
        return build_web_console_browser_smoke_summary_blocks(payload)
    if "worker_status" in schema or command_key == "worker-status":
        return build_worker_status_summary_blocks(payload)
    if "collab_monitor_status" in schema or command_key == "collab-monitor-status":
        return build_collab_monitor_status_summary_blocks(payload)
    if "project_status" in schema or command_key == "project-status":
        return build_project_status_summary_blocks(payload)
    if "project_versioning_readiness" in schema or command_key == "project-versioning-readiness":
        return build_versioning_summary_blocks(payload)
    if "project_refresh" in schema or command_key in {"project-refresh-preview", "project-refresh-apply"}:
        return build_project_refresh_summary_blocks(payload)
    if "project_history" in schema or command_key == "project-history":
        return build_project_history_summary_blocks(payload)
    if "project_sync" in schema or command_key == "project-sync-preview":
        return build_project_sync_summary_blocks(payload)
    if "project_online_publish" in schema or command_key == "project-online-publish-preview":
        return build_publish_preview_summary_blocks(payload)
    if "collab_binding_align" in schema or command_key == "collab-binding-align-preview":
        return build_collab_align_summary_blocks(payload)
    if "collab_transport_readiness" in schema or command_key == "collab-transport-readiness":
        return build_collab_transport_readiness_summary_blocks(payload)
    if "machine_collab_guide" in schema or command_key == "machine-collab-guide":
        return build_machine_collab_guide_summary_blocks(payload)
    if "project_snapshot_metadata_sync" in schema or command_key == "project-metadata-fetch-write":
        return build_metadata_sync_summary_blocks(payload)
    if "project_snapshot_manifest" in schema or command_key == "project-local-snapshot-write":
        return build_snapshot_manifest_summary_blocks(payload)
    if "project_backup_manifest" in schema or command_key == "project-backup-write":
        return build_backup_manifest_summary_blocks(payload)
    if "project_backups" in schema or command_key == "project-backups":
        return build_project_backups_summary_blocks(payload)
    if "project_snapshots" in schema or command_key == "project-snapshots":
        return build_snapshots_summary_blocks(payload)
    if "project_restore_readiness" in schema or command_key == "project-restore-readiness":
        return build_restore_readiness_summary_blocks(payload)
    if "project_artifact_pointers" in schema or command_key == "project-artifact-pointers":
        return build_artifact_pointers_summary_blocks(payload)
    if "project_away_report" in schema or command_key == "project-away-report":
        return build_away_report_summary_blocks(payload)
    if "project_away_cycles" in schema or command_key == "project-away-cycles":
        return build_away_cycles_summary_blocks(payload)
    if "project_operator_intents" in schema or command_key == "project-operator-intents":
        return build_operator_intents_summary_blocks(payload)
    if "project_operator_intent" in schema or command_key in {"project-away-prepare-intent", "project-away-continue-intent", "project-collab-delegate-intent"}:
        return build_operator_intent_summary_blocks(payload)
    if "web.workflow_checkpoint" in schema or command_key == "project-checkpoint-write":
        return build_checkpoint_workflow_summary_blocks(payload)
    return build_generic_summary_blocks(command_key, payload, ok=ok)


def run_cli_step(command_key: str, label: str, label_ko: str, argv: list[str], *, required: bool = True) -> dict[str, Any]:
    started = time.time()
    result = subprocess.run(
        argv,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        timeout=READ_TIMEOUT_SEC,
    )
    output = result.stdout or ""
    parsed: Any = None
    parse_error = ""
    if output.strip():
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
    return {
        "command_key": command_key,
        "label": label,
        "label_ko": label_ko,
        "required": bool(required),
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "duration_sec": round(time.time() - started, 3),
        "argv": argv,
        "command": command_line(argv),
        "stdout": output,
        "stdout_json": parsed,
        "json_parse_error": parse_error,
        "operator_summary": "Step completed." if result.returncode == 0 else "Step needs review.",
        "operator_summary_ko": "단계가 완료되었습니다." if result.returncode == 0 else "단계 확인이 필요합니다.",
    }


def run_checkpoint_workflow(command_key: str, project: str, *, confirmed: bool) -> dict[str, Any]:
    project_text = project.strip()
    if not project_text:
        raise ValueError(f"unsupported or incomplete command: {command_key}")
    if command_requires_confirmation(command_key) and not confirmed:
        raise ValueError(f"confirmation_required: {command_key}")
    base = [sys.executable, str(CLUTCH_CTL)]
    started = time.time()
    step_specs = [
        (
            "project-backup-write",
            "Local backup",
            "로컬 백업",
            [*base, "project-backup", "--project", project_text, "--json"],
            True,
        ),
        (
            "project-local-snapshot-write",
            "Local manifest",
            "로컬 manifest",
            [*base, "project-snapshot", "--project", project_text, "--skip-runtime", "--write", "--json"],
            True,
        ),
    ]
    steps = [
        run_cli_step(step_key, label, label_ko, argv, required=required)
        for step_key, label, label_ko, argv, required in step_specs
    ]
    ok = all(bool(item.get("ok")) for item in steps if item.get("required"))
    parsed = {
        "schema": "clutch.web.workflow_checkpoint.v1",
        "ok": ok,
        "project_id": project_text,
        "steps": steps,
        "required_step_count": sum(1 for item in steps if item.get("required")),
        "failed_required_step_count": sum(1 for item in steps if item.get("required") and not item.get("ok")),
    }
    summary_blocks = build_command_summary_blocks(command_key, parsed, ok=ok, returncode=0 if ok else 1)
    return {
        "schema": "clutch.web.command_result.v1",
        "ok": ok,
        "command_key": command_key,
        "project": project_text,
        "new_machine_id": "",
        "connection_mode": "",
        "argv": [],
        "command": "workflow: project-checkpoint-write",
        "returncode": 0 if ok else 1,
        "duration_sec": round(time.time() - started, 3),
        "stdout": json.dumps(parsed, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "stdout_json": parsed,
        "json_parse_error": "",
        "read_only": False,
        "state_changing": True,
        "confirmation_required": command_requires_confirmation(command_key),
        "confirmed": bool(confirmed),
        "operator_judgement": command_operator_judgement(summary_blocks, ok=ok),
        "summary_blocks": summary_blocks,
    }


def run_safe_command(
    command_key: str,
    project: str = "",
    ops_root: Path | None = None,
    *,
    confirmed: bool = False,
    new_machine_id: str = "",
    connection_mode: str = "auto",
) -> dict[str, Any]:
    state_changing = command_changes_state(command_key)
    if command_key == "project-checkpoint-write":
        return run_checkpoint_workflow(command_key, project, confirmed=confirmed)
    argv = safe_command_argv(
        command_key,
        project,
        confirmed=confirmed,
        new_machine_id=new_machine_id,
        connection_mode=connection_mode,
    )
    started = time.time()
    result = subprocess.run(
        argv,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        timeout=READ_TIMEOUT_SEC,
    )
    output = result.stdout or ""
    parsed: Any = None
    parse_error = ""
    if output.strip():
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
    ok = result.returncode == 0
    summary_payload = parsed
    if command_key == "overview" and isinstance(parsed, dict):
        summary_payload = filter_web_overview_attention(parsed, active_web_project_ids(ops_root or default_ops_root()))
    summary_blocks = build_command_summary_blocks(
        command_key,
        summary_payload,
        ok=ok,
        returncode=result.returncode,
    )
    return {
        "schema": "clutch.web.command_result.v1",
        "ok": ok,
        "command_key": command_key,
        "project": project,
        "new_machine_id": new_machine_id,
        "connection_mode": connection_mode,
        "argv": argv,
        "command": command_line(argv),
        "returncode": result.returncode,
        "duration_sec": round(time.time() - started, 3),
        "stdout": output,
        "stdout_json": parsed,
        "json_parse_error": parse_error,
        "read_only": not state_changing,
        "state_changing": state_changing,
        "confirmation_required": command_requires_confirmation(command_key),
        "confirmed": bool(confirmed),
        "operator_judgement": command_operator_judgement(summary_blocks, ok=ok),
        "summary_blocks": summary_blocks,
    }


def active_web_bindings() -> tuple[list[dict[str, Any]], int]:
    raw_bindings = load_active_bindings().get("bindings", [])
    bindings = [item for item in raw_bindings if isinstance(item, dict)]
    active = [
        item
        for item in bindings
        if str(item.get("status") or "active") == "active" and is_binding_active(item)
    ]
    return active, len(bindings)


def binding_updated_ns(binding: dict[str, Any]) -> int:
    for key in ("updated_time_ns", "created_time_ns"):
        value = binding.get(key)
        if isinstance(value, int):
            return value
    return 0


def collab_project_id_for_worker(worker: dict[str, Any]) -> str:
    peer = worker.get("peer") if isinstance(worker.get("peer"), dict) else {}
    for payload_key in ("current_task",):
        payload = worker.get(payload_key)
        if isinstance(payload, dict) and payload.get("project_id"):
            return str(payload.get("project_id") or "")
    peer_task = peer.get("current_task") if isinstance(peer.get("current_task"), dict) else {}
    if peer_task.get("project_id"):
        return str(peer_task.get("project_id") or "")
    return ""


def merged_cluster_web_bindings(ops_root: Path) -> tuple[list[dict[str, Any]], int, int]:
    local_active, raw_binding_count = active_web_bindings()
    merged: list[dict[str, Any]] = [dict(item) for item in local_active]
    inferred_count = 0

    by_project_machine: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in merged:
        key = (str(item.get("project_id") or ""), str(item.get("machine_id") or ""))
        by_project_machine.setdefault(key, []).append(item)

    normalized: list[dict[str, Any]] = []
    for items in by_project_machine.values():
        non_observer = [item for item in items if str(item.get("role") or "") in {"main", "worker"}]
        candidates = non_observer or items
        by_role: dict[str, dict[str, Any]] = {}
        for item in candidates:
            role = str(item.get("role") or "")
            current = by_role.get(role)
            if current is None or binding_updated_ns(item) >= binding_updated_ns(current):
                by_role[role] = item
        normalized.extend(by_role.values())

    normalized.sort(
        key=lambda item: (
            str(item.get("project_id") or ""),
            {"main": 0, "worker": 1, "observer": 2}.get(str(item.get("role") or ""), 9),
            str(item.get("machine_id") or ""),
        )
    )
    return normalized, raw_binding_count, inferred_count


def role_counts_for_bindings(bindings: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "main": sum(1 for item in bindings if str(item.get("role") or "") == "main"),
        "worker": sum(1 for item in bindings if str(item.get("role") or "") == "worker"),
        "observer": sum(1 for item in bindings if str(item.get("role") or "") == "observer"),
    }


def active_web_project_ids(ops_root: Path) -> set[str]:
    bindings, _, _ = merged_cluster_web_bindings(ops_root)
    return {str(item.get("project_id") or "") for item in bindings if item.get("project_id")}


def attention_severity_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "error_count": 0,
        "info_count": 0,
        "needs_approval_count": 0,
        "total_count": 0,
        "unknown_count": 0,
        "warning_count": 0,
    }
    for item in items:
        severity = str(item.get("severity") or "unknown")
        key = {
            "error": "error_count",
            "info": "info_count",
            "needs_approval": "needs_approval_count",
            "warning": "warning_count",
        }.get(severity, "unknown_count")
        counts[key] += 1
        counts["total_count"] += 1
    return counts


def web_attention_item_visible(
    item: dict[str, Any],
    *,
    active_project_ids: set[str],
    default_project_id: str = "",
) -> bool:
    project_id = str(item.get("project_id") or default_project_id)
    kind = str(item.get("kind") or "")
    if kind == "collab_readiness" and project_id and project_id not in active_project_ids:
        return False
    return True


def filter_web_overview_attention(payload: dict[str, Any], active_project_ids: set[str]) -> dict[str, Any]:
    """Hide inactive-project collab warnings from the web operator display."""
    filtered = copy.deepcopy(payload)
    projects = filtered.get("projects") if isinstance(filtered.get("projects"), dict) else {}
    project_items = projects.get("items") if isinstance(projects.get("items"), list) else []
    for project in project_items:
        if not isinstance(project, dict):
            continue
        project_id = str(project.get("project_id") or "")
        attention_items = project.get("attention_items")
        if not isinstance(attention_items, list):
            continue
        visible_items = [
            item
            for item in attention_items
            if isinstance(item, dict)
            and web_attention_item_visible(item, active_project_ids=active_project_ids, default_project_id=project_id)
        ]
        project["attention_items"] = visible_items
        project["attention_count"] = len(visible_items)
        project["attention_severity_counts"] = attention_severity_counts(visible_items)

    top_items = filtered.get("attention_items")
    if isinstance(top_items, list):
        visible_top_items = [
            item
            for item in top_items
            if isinstance(item, dict)
            and web_attention_item_visible(item, active_project_ids=active_project_ids)
        ]
        filtered["attention_items"] = visible_top_items
        filtered["attention_count"] = len(visible_top_items)
        filtered["attention_severity_counts"] = attention_severity_counts(visible_top_items)
    return filtered


def primary_machine_role(roles: list[str]) -> str:
    for role in ("main", "worker", "observer"):
        if role in roles:
            return role
    return roles[0] if roles else "unknown"


def group_bindings_by_machine(bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for binding in bindings:
        machine_id = str(binding.get("machine_id") or "unknown")
        grouped.setdefault(machine_id, []).append(binding)

    machines: list[dict[str, Any]] = []
    for machine_id, machine_bindings in grouped.items():
        roles = sorted(
            {str(item.get("role") or "unknown") for item in machine_bindings},
            key=lambda role: {"main": 0, "worker": 1, "observer": 2}.get(role, 9),
        )
        thread_ids = sorted(
            {str(item.get("thread_id") or "") for item in machine_bindings if item.get("thread_id")}
        )
        workspace_paths = sorted(
            {str(item.get("workspace_path") or "") for item in machine_bindings if item.get("workspace_path")}
        )
        machines.append(
            {
                "machine_id": machine_id,
                "primary_role": primary_machine_role(roles),
                "roles": roles,
                "role_counts": role_counts_for_bindings(machine_bindings),
                "binding_count": len(machine_bindings),
                "thread_count": len(thread_ids),
                "thread_ids": thread_ids,
                "workspace_paths": workspace_paths,
                "bindings": machine_bindings,
            }
        )
    return sorted(
        machines,
        key=lambda item: (
            {"main": 0, "worker": 1, "observer": 2}.get(str(item.get("primary_role")), 9),
            str(item.get("machine_id") or ""),
        ),
    )


def role_counts_for_machines(machines: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "main": sum(1 for item in machines if str(item.get("primary_role") or "") == "main"),
        "worker": sum(1 for item in machines if str(item.get("primary_role") or "") == "worker"),
        "observer": sum(1 for item in machines if str(item.get("primary_role") or "") == "observer"),
    }


def machine_id_for_collab_host(ops_root: Path, host: str) -> str:
    host_text = str(host or "").strip().lower()
    if not host_text:
        return ""
    for machine in load_registry(ops_root, "machines.json", "machines"):
        machine_id = str(machine.get("machine_id") or "")
        display = str(machine.get("display_name") or "").strip().lower()
        hostname = str(machine.get("hostname") or "").strip().lower()
        if (
            machine_id.lower().startswith(host_text)
            or display == host_text
            or hostname.startswith(host_text)
            or host_text in machine_id.lower().split("-")
        ):
            return machine_id
    return ""


def project_id_for_collab_link(
    active_bindings: list[dict[str, Any]],
    *,
    local_machine_id: str,
    local_role: str,
    peer_machine_id: str,
    peer_role: str,
) -> str:
    candidates: set[str] = set()
    for binding in active_bindings:
        project_id = str(binding.get("project_id") or "")
        machine_id = str(binding.get("machine_id") or "")
        role = str(binding.get("role") or "")
        if (
            project_id
            and (
                (machine_id == local_machine_id and role == local_role)
                or (machine_id == peer_machine_id and role == peer_role)
            )
        ):
            candidates.add(project_id)
    return next(iter(candidates)) if len(candidates) == 1 else ""


def binding_match_status(
    bindings: list[dict[str, Any]],
    *,
    project_id: str,
    machine_id: str,
    role: str,
    thread_id: str,
) -> str:
    if not project_id or not machine_id or not role:
        return "unknown"
    same_machine_role = []
    for binding in bindings:
        if str(binding.get("project_id") or "") != project_id:
            continue
        if str(binding.get("machine_id") or "") != machine_id:
            continue
        if str(binding.get("role") or "") != role:
            continue
        same_machine_role.append(binding)
        if thread_id and str(binding.get("thread_id") or "") == thread_id:
            return "bound"
    return "machine_role_bound" if same_machine_role else "unbound"


def primary_binding_role_for_machine(
    bindings: list[dict[str, Any]],
    *,
    project_id: str,
    machine_id: str,
) -> str:
    roles: list[str] = []
    for binding in bindings:
        if str(binding.get("project_id") or "") != project_id:
            continue
        if str(binding.get("machine_id") or "") != machine_id:
            continue
        role = str(binding.get("role") or "")
        if role in {"main", "worker", "observer"} and role not in roles:
            roles.append(role)
    return primary_machine_role(roles) if roles else ""


def collab_links_for_sessions(ops_root: Path, active_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    worker_payload = build_worker_status_payload(host_filter="", collab_stale_sec=DEFAULT_COLLAB_STALE_SEC)
    links: list[dict[str, Any]] = []
    for worker in worker_payload.get("workers", []):
        if not isinstance(worker, dict):
            continue
        peer = worker.get("peer") if isinstance(worker.get("peer"), dict) else {}
        health = worker.get("health") if isinstance(worker.get("health"), dict) else {}
        peer_role = str(peer.get("role") or "")
        if str(health.get("peer_status") or "") != "fresh":
            continue
        peer_machine_id = machine_id_for_collab_host(ops_root, str(peer.get("host") or ""))
        local_machine_id = machine_id_for_collab_host(ops_root, str(worker.get("host") or ""))
        local_role = str(worker.get("role") or "")
        project_id = project_id_for_collab_link(
            active_bindings,
            local_machine_id=local_machine_id,
            local_role=local_role,
            peer_machine_id=peer_machine_id,
            peer_role=peer_role,
        )
        if not project_id:
            project_id = collab_project_id_for_worker(worker)
        thread_id = str(peer.get("session_id") or "")
        peer_binding_role = primary_binding_role_for_machine(
            active_bindings,
            project_id=project_id,
            machine_id=peer_machine_id,
        )
        if peer_role in {"main", "worker", "observer"}:
            status = binding_match_status(
                active_bindings,
                project_id=project_id,
                machine_id=peer_machine_id,
                role=peer_role,
                thread_id=thread_id,
            )
            if status == "unbound" and peer_binding_role:
                status = "transport_role_differs"
        elif peer_binding_role:
            status = "binding_role_only"
        else:
            continue
        links.append(
            {
                "project_id": project_id,
                "status": status,
                "host": str(worker.get("host") or ""),
                "local_machine_id": local_machine_id,
                "local_role": local_role,
                "peer_host": str(peer.get("host") or ""),
                "peer_machine_id": peer_machine_id,
                "peer_role": peer_role,
                "peer_binding_role": peer_binding_role,
                "role_source": "project_binding" if status == "binding_role_only" else "transport_peer",
                "peer_session_id": thread_id,
                "peer_status": str(health.get("peer_status") or ""),
                "peer_age_sec": health.get("peer_age_sec"),
            }
        )
    return links


def build_web_health_payload(ops_root: Path) -> dict[str, Any]:
    machine_id = normalize_machine_id("", ops_root)
    projects = project_entries(ops_root)
    active_bindings, raw_binding_count, inferred_binding_count = merged_cluster_web_bindings(ops_root)
    backend_version = WEB_PROCESS_VERSION
    checkout_version = static_asset_version()
    default_command_keys = web_command_keys(group="default")
    advanced_command_keys = [item["key"] for item in WEB_COMMANDS if item["group"] != "default"]
    attention_shortcuts = build_attention_shortcuts_payload()
    command_registry_integrity = build_command_registry_integrity_payload()
    command_surface_integrity = build_command_surface_integrity_payload()
    command_registry_ready = bool(WEB_COMMAND_REGISTRY and WEB_COMMAND_GROUPS and command_registry_integrity["ok"])
    command_surface_ready = bool(command_surface_integrity["ok"])
    default_command_group_ready = bool(command_registry_ready and command_surface_ready and default_command_keys)
    advanced_command_groups_ready = bool(
        command_registry_ready
        and command_surface_ready
        and advanced_command_keys
        and all(group["command_keys"] for group in WEB_COMMAND_GROUPS if group["group_id"] != "default")
    )
    command_surface_render_ready = bool(default_command_group_ready and advanced_command_groups_ready)
    registry_finding_count = int(command_registry_integrity["summary"].get("finding_count") or 0)
    surface_finding_count = int(command_surface_integrity["summary"].get("finding_count") or 0)
    command_registry_rollout = {
        "schema": "clutch.web.command_registry.v1",
        "backend_version": backend_version,
        "process_version": backend_version,
        "checkout_version": checkout_version,
        "asset_version": backend_version,
        "command_count": len(WEB_COMMAND_REGISTRY),
        "default_command_count": len(default_command_keys),
        "advanced_command_count": len(advanced_command_keys),
        "group_count": len(WEB_COMMAND_GROUPS),
        "integrity_ok": command_registry_integrity["ok"],
        "surface_integrity_ok": command_surface_integrity["ok"],
        "registry_ready": command_registry_ready,
        "surface_ready": command_surface_ready,
        "default_group_ready": default_command_group_ready,
        "advanced_groups_ready": advanced_command_groups_ready,
        "render_ready": command_surface_render_ready,
        "issue_count": registry_finding_count + surface_finding_count,
    }
    return {
        "schema": "clutch.web.health.v1",
        "ok": True,
        "ready": True,
        "status": "ready",
        "machine_id": machine_id,
        "project_ids": [str(item.get("project_id") or "") for item in projects],
        "active_binding_count": len(active_bindings),
        "raw_binding_count": raw_binding_count,
        "cluster_inferred_binding_count": inferred_binding_count,
        "inactive_binding_count": max(raw_binding_count - len(active_bindings), 0),
        "static_root": str(STATIC_ROOT),
        "web_backend_version": backend_version,
        "web_backend_process_version": backend_version,
        "current_checkout_version": checkout_version,
        "static_asset_version": backend_version,
        "command_policy_schema": "clutch.web.command_registry.v1",
        "command_registry_available": True,
        "command_registry_command_count": len(WEB_COMMAND_REGISTRY),
        "default_command_count": len(default_command_keys),
        "advanced_command_count": len(advanced_command_keys),
        "command_group_count": len(WEB_COMMAND_GROUPS),
        "command_registry_rollout": command_registry_rollout,
        "command_registry_integrity_ok": command_registry_integrity["ok"],
        "command_registry_integrity": command_registry_integrity,
        "command_surface_integrity_ok": command_surface_integrity["ok"],
        "command_surface_integrity": command_surface_integrity,
        "command_registry_ready": command_registry_ready,
        "command_surface_ready": command_surface_ready,
        "default_command_group_ready": default_command_group_ready,
        "advanced_command_groups_ready": advanced_command_groups_ready,
        "command_surface_render_ready": command_surface_render_ready,
        "command_surface_issue_count": registry_finding_count + surface_finding_count,
        "command_registry": copy.deepcopy(WEB_COMMAND_REGISTRY),
        "command_groups": copy.deepcopy(WEB_COMMAND_GROUPS),
        "attention_shortcuts": attention_shortcuts,
        "default_command_keys": default_command_keys,
        "preview_only_default_command_keys": [
            item["key"] for item in WEB_COMMANDS if item["group"] == "default" and item["preview_only"]
        ],
        "advanced_command_keys": advanced_command_keys,
        "advanced_apply_command_keys": web_command_keys(predicate="advanced_apply"),
        "read_only_commands": web_command_keys(predicate="read_only"),
        "state_changing_commands": sorted(STATE_CHANGING_COMMANDS),
        "confirmation_required_commands": sorted(CONFIRMATION_REQUIRED_COMMANDS),
    }


def build_web_sessions_payload(ops_root: Path) -> dict[str, Any]:
    machine_id = normalize_machine_id("", ops_root)
    bindings, raw_binding_count, inferred_binding_count = merged_cluster_web_bindings(ops_root)
    collab_links = collab_links_for_sessions(ops_root, bindings)
    projects = []
    registry_projects = project_entries(ops_root)
    project_ids = [str(item.get("project_id") or "") for item in registry_projects]
    project_by_id = {str(item.get("project_id") or ""): item for item in registry_projects}
    for project_id in project_ids:
        project_config = project_by_id.get(project_id, {})
        configured_roles = project_machine_role_summary(project_config) if isinstance(project_config, dict) else {}
        project_bindings = [
            item for item in bindings if str(item.get("project_id") or "") == project_id
        ]
        project_collab_links = [
            item for item in collab_links if str(item.get("project_id") or "") == project_id
        ]
        machines = group_bindings_by_machine(project_bindings)
        machine_role_counts = role_counts_for_machines(machines)
        binding_role_counts = role_counts_for_bindings(project_bindings)
        if not machines:
            status = "no_sessions"
        elif machine_role_counts["main"] == 0:
            status = "no_main"
        elif machine_role_counts["main"] > 1:
            status = "multiple_main"
        else:
            status = "ready"
        projects.append(
            {
                "project_id": project_id,
                "status": status,
                "role_counts": machine_role_counts,
                "machine_role_counts": machine_role_counts,
                "binding_role_counts": binding_role_counts,
                "machine_count": len(machines),
                "binding_count": len(project_bindings),
                "configured_machine_roles": configured_roles,
                "machines": machines,
                "bindings": project_bindings,
                "collab_links": project_collab_links,
                "monitor_context": session_collab_monitor_context(project_id),
                "collab_alignment_status": (
                    "unbound"
                    if any(
                        str(item.get("status") or "") in {"unbound", "transport_role_differs"}
                        for item in project_collab_links
                    )
                    else "bound"
                    if project_collab_links
                    else "none"
                ),
            }
        )
    return {
        "schema": "clutch.web.sessions.v1",
        "ok": True,
        "machine_id": machine_id,
        "binding_count": len(bindings),
        "active_binding_count": len(bindings),
        "raw_binding_count": raw_binding_count,
        "cluster_inferred_binding_count": inferred_binding_count,
        "inactive_binding_count": max(raw_binding_count - len(bindings), 0),
        "project_count": len(projects),
        "projects": projects,
        "bindings": bindings,
        "collab_links": collab_links,
    }


def build_web_collab_monitor_payload(ops_root: Path, *, project_id: str = "") -> dict[str, Any]:
    project_text = project_id.strip()
    payload = build_collab_monitor_status_payload(
        ops_root=ops_root,
        project_name=project_text,
        host_filter="",
        collab_stale_sec=DEFAULT_COLLAB_STALE_SEC,
    )
    summary_blocks = build_collab_monitor_status_summary_blocks(payload)
    return {
        "schema": "clutch.web.collab_monitor.v1",
        "ok": bool(payload.get("ok")),
        "project_id": payload.get("project_id") or project_text,
        "generated_at_ns": time.time_ns(),
        "refresh_interval_sec": 5,
        "monitor_status": payload,
        "summary_blocks": summary_blocks,
        "operator_judgement": command_operator_judgement(summary_blocks, ok=bool(payload.get("ok"))),
    }


class ClutchWebHandler(BaseHTTPRequestHandler):
    server_version = "CLUTCHWeb/0.1"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # Browser reloads or tab switches can cancel an in-flight request.
            # Treat that as a client abort, not as a console backend failure.
            return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        data = self.rfile.read(length)
        try:
            payload = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    @property
    def ops_root(self) -> Path:
        return self.server.ops_root  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            if path in {"/", "/index.html"}:
                self._send(*static_response(STATIC_ROOT / "index.html"))
                return
            if path.startswith("/assets/"):
                target = STATIC_ROOT / path.removeprefix("/assets/")
                if not target.resolve().is_relative_to(STATIC_ROOT.resolve()):
                    self._send(*error_payload(403, "forbidden"))
                    return
                self._send(*static_response(target))
                return
            if path == "/api/health":
                self._send(*json_response(build_web_health_payload(self.ops_root)))
                return
            if path == "/api/overview":
                include_runtime = parse_bool(query.get("runtime", ["true"])[0], True)
                include_workers = parse_bool(query.get("workers", ["true"])[0], True)
                include_hardware = parse_bool(query.get("hardware", ["false"])[0], False)
                payload = build_overview_payload(
                    ops_root=self.ops_root,
                    project_filters=query.get("project", []),
                    machine_id_arg=query.get("machine_id", [""])[0],
                    backups_root=PROJECT_BACKUPS_ROOT,
                    backup_limit=3,
                    collab_stale_sec=DEFAULT_COLLAB_STALE_SEC,
                    hardware_limit=5,
                    include_runtime=include_runtime,
                    include_workers=include_workers,
                    include_hardware=include_hardware,
                )
                payload = filter_web_overview_attention(payload, active_web_project_ids(self.ops_root))
                self._send(*json_response(payload))
                return
            if path == "/api/sessions":
                self._send(*json_response(build_web_sessions_payload(self.ops_root)))
                return
            if path == "/api/collab-monitor":
                project_id = query.get("project", [""])[0]
                self._send(*json_response(build_web_collab_monitor_payload(self.ops_root, project_id=project_id)))
                return
            self._send(*error_payload(404, "not found"))
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            self._send(*error_payload(500, str(exc)))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/command":
                payload = self._read_json()
                command_key = str(payload.get("command_key") or "")
                project = str(payload.get("project") or "")
                confirmed = bool(payload.get("confirm", False))
                new_machine_id = str(payload.get("new_machine_id") or "")
                connection_mode = str(payload.get("connection_mode") or "auto")
                result = run_safe_command(
                    command_key,
                    project,
                    self.ops_root,
                    confirmed=confirmed,
                    new_machine_id=new_machine_id,
                    connection_mode=connection_mode,
                )
                self._send(*json_response(result, 200 if result["ok"] else 422))
                return
            self._send(*error_payload(404, "not found"))
        except ValueError as exc:
            self._send(*error_payload(400, str(exc)))
        except subprocess.TimeoutExpired:
            self._send(*error_payload(504, "command timed out"))
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            self._send(*error_payload(500, str(exc)))

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("clutch-web " + format % args + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local CLUTCH web console.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_WEB_PORT)
    parser.add_argument("--ops-root", default=str(default_ops_root()))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ClutchWebHandler)
    server.ops_root = Path(args.ops_root).expanduser()  # type: ignore[attr-defined]
    print(f"CLUTCH web console listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
