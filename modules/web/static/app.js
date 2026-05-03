const LANG_STORAGE_KEY = "clutch.web.lang";
const SUPPORTED_LANGS = new Set(["en", "ko"]);

const TEXT = {
  en: {
    "brand.subtitle": "Operator Console",
    "topbar.kicker": "Local-first control plane",
    "action.refresh": "Refresh",
    "action.open": "Open",
    "nav.dashboard": "Dashboard",
    "nav.sessions": "Sessions",
    "nav.monitor": "Monitor",
    "nav.projects": "Projects",
    "nav.backups": "Backups",
    "nav.machines": "Machines",
    "nav.commands": "Commands",
    "nav.help": "Help",
    "label.machine": "Machine",
    "label.projects": "Projects",
    "label.workers": "Workers",
    "label.attention": "Attention",
    "label.consistency": "Consistency",
    "label.sessions": "Sessions",
    "label.selectedProject": "Selected Project",
    "label.backups": "Backups",
    "label.repos": "Repos",
    "label.console": "Console",
    "label.output": "Output",
    "label.system": "System",
    "label.project": "Project",
    "label.currentMachine": "Current Machine",
    "label.lifecycle": "Lifecycle",
    "label.onlineSync": "Online Sync",
    "label.agentEntry": "Agent Entry",
    "label.collab": "Collab",
    "label.newMachine": "New Machine",
    "label.connectionMode": "Connection Mode",
    "label.sync": "Repo Sync",
    "label.versioning": "Versioning",
    "label.publicationGate": "Publication Gate",
    "label.recoveryCoverage": "Recovery Coverage",
    "label.dirtyWip": "Dirty WIP",
    "label.localSnapshotCoverage": "Local Snapshot",
    "label.metadataCoverage": "Metadata Coverage",
    "label.away": "Away",
    "label.pcRoles": "PC Roles",
    "label.visibility": "Visibility",
    "label.integration": "Integration",
    "label.dataHandling": "Data Handling",
    "label.recoveryEvidence": "Recovery Evidence",
    "label.latest": "Latest",
    "label.guidance": "Guidance",
    "label.localBackups": "Local Backups",
    "label.snapshots": "Snapshots",
    "label.localSnapshots": "This PC Manifests",
    "label.localSnapshotManifests": "This PC Manifests",
    "label.localSnapshotFreshness": "Manifest Freshness",
    "label.promotedMetadata": "Promoted Metadata",
    "label.metadataRefs": "Metadata Refs",
    "label.artifactPointers": "Artifact Pointers",
    "label.artifactManifest": "Artifact Manifest",
    "label.dataLocations": "Data Locations",
    "label.dataNote": "Data Note",
    "label.localWorkspaces": "Local Workspaces",
    "label.latestBackup": "Latest Backup",
    "label.latestSnapshot": "Latest Local Manifest",
    "label.latestMetadata": "Latest Metadata",
    "heading.operationalState": "Operational State",
    "heading.peerFreshness": "Worker Links",
    "heading.attentionNextSteps": "Attention Next Steps",
    "heading.displayAudit": "Display Audit",
    "heading.projectPcRoles": "Project PC Roles",
    "heading.snapshotsMetadata": "Snapshots / Metadata",
    "heading.codexPeers": "Codex Links",
    "heading.foundationOps": "Foundation / Ops",
    "heading.commandConsole": "Command Console",
    "heading.collabMonitor": "Collab Monitor",
    "heading.monitorHosts": "Monitor Hosts",
    "heading.monitorGuidance": "Monitor Guidance",
    "heading.monitorTaskContext": "Task Context",
    "heading.monitorWorkerLinks": "Worker Links",
    "command.scope.systemDiagnostics": "System diagnostics",
    "command.scope.projectDiagnostics": "Project diagnostics",
    "command.scope.previewOnly": "Preview only",
    "command.scope.collabOnboarding": "Collab onboarding",
    "command.scope.projectActions": "State-changing project actions",
    "command.group.globalDiagnostics": "Global Diagnostics",
    "command.group.projectActions": "Project Actions",
    "command.group.collabOnboarding": "Collab / Onboarding",
    "command.group.coreWorkflows": "Core Workflows",
    "command.group.advancedDiagnostics": "Advanced Diagnostics",
    "command.advanced.summary": "Show advanced features",
    "command.confirmStateChange": "This command changes CLUTCH or project state. Continue?",
    "command.meta.none": "No command selected.",
    "command.empty.initial": "Run a command to see a readable result summary.",
    "command.empty.projectRequired": "Select a project before running this command.",
    "command.meta.projectRequired": "Project command needs a selected project.",
    "command.meta.projectTarget": "Project command target:",
    "command.meta.projectSelect": "Select a project before running project-scoped commands.",
    "command.runningPrefix": "Running",
    "command.section.runSummary": "Run Summary",
    "command.section.executed": "Executed",
    "command.section.rawJson": "Raw JSON",
    "command.section.executionEvidence": "Execution Evidence",
    "command.section.bindingRecords": "Binding Records",
    "command.section.collabAlignment": "Collab Alignment",
    "command.section.workerStatus": "Workers",
    "command.section.overview": "Overview",
    "command.section.projectStatus": "Project Status",
    "command.section.versioningReadiness": "Versioning Readiness",
    "command.section.syncPreview": "Sync Preview",
    "command.section.snapshots": "Snapshots",
    "command.section.awayReport": "Away Report",
    "command.section.readableSummary": "Readable Summary",
    "command.noItems": "No items.",
    "command.noCompactSummary": "No compact summary is available yet. Use Raw JSON for full details.",
    "command.readOnlyDiagnostic": "CLUTCH read-only diagnostic command.",
    "command.failed": "Command failed",
    "empty.noProjects": "No projects",
    "empty.noWorkers": "No workers",
    "empty.noSessions": "No sessions",
    "empty.noActivePcBindings": "No active PC bindings.",
    "empty.none": "None",
    "empty.noProjectSelected": "No project selected",
    "empty.noRepos": "No repos",
    "empty.noAttention": "No visible attention items.",
    "monitor.empty": "No collab monitor data yet.",
    "monitor.loading": "Refreshing monitor state.",
    "monitor.noTasks": "No active collab task context.",
    "monitor.noRepair": "No monitor repair action needed.",
    "monitor.bindingRoleSource": "CLUTCH binding is the role source; transport role is diagnostic.",
    "monitor.roleSource.alignedDetail": "binding and transport agree",
    "monitor.roleSource.bindingOnlyDetail": "binding source; transport diagnostic",
    "monitor.roleSource.differsDetail": "review before delegation",
    "monitor.roleSource.unknownDetail": "role source unavailable",
    "monitor.noGuidance": "No monitor guidance is available yet.",
    "monitor.auto": "auto refresh",
    "monitor.visible": "visible",
    "monitor.hidden": "hidden",
    "monitor.missing": "missing",
    "monitor.roleMismatch": "role mismatch",
    "monitor.lastUpdated": "last updated",
    "monitor.taskScope.selected": "selected project",
    "monitor.taskScope.different": "other project history",
    "monitor.taskScope.none": "no task project",
    "monitor.taskNote.active": "active task context",
    "monitor.taskNote.selectedHistory": "selected-project history",
    "monitor.taskNote.otherProjectHistory": "history from another project",
    "monitor.taskNote.staleHistory": "stale history, not an active task",
    "monitor.taskNote.staleOtherProject": "stale history from another project, not an active selected-project task",
    "monitor.taskNote.recentHistory": "recent result history",
    "monitor.taskOnlyOtherHistory": "Only old history from another project is present. There is no active task for the selected project.",
    "monitor.taskStatus.active": "active",
    "monitor.taskStatus.recent_history": "recent history",
    "monitor.taskStatus.stale_history": "stale history",
    "monitor.taskStatus.history_unknown_age": "history",
    "monitor.taskStatus.none": "none",
    "monitor.taskActive": "active",
    "monitor.taskSelected": "selected",
    "monitor.taskHistory": "history",
    "monitor.taskStale": "stale",
    "audit.cleanTitle": "No display consistency issues detected.",
    "audit.cleanDetail": "Health, overview, and session counts agree.",
    "audit.projectListMismatch": "Project list mismatch",
    "audit.sessionProjectMismatch": "Session project mismatch",
    "audit.activeBindingMismatch": "Active binding total mismatch",
    "audit.healthSessionMismatch": "Health/session binding mismatch",
    "audit.archivedPresent": "Archived bindings are present",
    "audit.multipleMainDetail": "Only one active main PC should own a project.",
    "audit.noMainDetail": "This is acceptable for observer-only work, but main/sub collaboration is not active.",
    "status.ready": "Ready",
    "status.review": "Review",
    "status.blocked": "Blocked",
    "status.observe": "Observe",
    "status.loading": "Loading",
    "status.error": "Error",
    "status.running": "Running",
    "status.complete": "Complete",
    "status.idle": "Idle",
    "status.approval": "Approval",
    "status.metadata": "Metadata",
    "status.metadata_only": "Metadata only",
    "status.fresh": "Fresh",
    "status.dirty": "Dirty",
    "status.available": "Available",
    "status.missing": "Missing",
    "status.disabled": "Disabled",
    "status.busy": "Busy",
    "status.stale": "Stale",
    "status.failed": "Failed",
    "status.no_main": "No main",
    "status.no_sessions": "No sessions",
    "status.multiple_main": "Multiple main",
    "status.unbound": "Binding unaligned",
    "status.aligned": "Aligned",
    "status.binding_role_only": "Binding role source",
    "status.transport_role_differs": "Transport role differs",
    "status.bound": "Bound",
    "status.unassigned": "Unassigned",
    "status.warning": "Warning",
    "status.legacy_import": "Legacy import",
    "status.formalizing": "Formalizing",
    "status.unknown": "Unknown",
    "status.clean": "clean",
    "status.mismatch": "mismatch",
    "status.archive": "archive",
    "status.conflict": "conflict",
    "status.needs_artifact_pointers": "Needs artifact pointers",
    "status.artifact_pointers_recorded": "Artifact pointers recorded",
    "status.code_metadata_only": "Code/metadata only",
    "status.audit_when_empty": "Audit when empty",
    "status.canonical_online_ready": "Canonical online ready",
    "status.recovery_ready_publication_review": "Recovery ready, publish review",
    "status.attention_required": "Attention required",
    "status.review_recommended": "Review recommended",
    "status.clean_publication_ready": "Clean publication ready",
    "status.publication_review_required": "Publication review required",
    "role.main": "Main PC",
    "role.worker": "Sub PC",
    "role.observer": "Observer PC",
    "role.unknown": "Unknown PC",
    "role.unassigned": "Unassigned",
    "word.yes": "yes",
    "word.no": "no",
    "word.present": "present",
    "word.none": "none",
    "word.ready": "ready",
    "word.review": "review",
    "word.match": "match",
    "word.warning": "warning",
    "word.clean": "clean",
    "word.mutating": "mutating",
    "word.readOnly": "read-only",
    "word.complete": "complete",
    "word.return": "return",
    "field.command": "command",
    "field.scope": "scope",
    "field.result": "result",
    "field.duration": "duration",
    "field.confirmationRequired": "confirmation required",
    "field.confirmed": "confirmed",
    "field.status": "status",
    "field.thread": "thread",
    "field.project": "project",
    "field.aligned": "aligned",
    "field.created": "created",
    "field.warnings": "warnings",
    "field.dryRun": "dry run",
    "field.workers": "workers",
    "field.available": "available",
    "field.busy": "busy",
    "field.stale": "stale",
    "field.machine": "machine",
    "field.attention": "attention",
    "field.workspace": "workspace",
    "field.syncReady": "repo sync",
    "field.mainSub": "main/sub",
    "field.onlineBackup": "online backup",
    "field.ok": "ok",
    "field.routinePublish": "routine publish",
    "field.reproducibility": "reproducibility",
    "field.blockers": "blockers",
    "field.required": "required repos",
    "field.count": "count",
    "field.latest": "latest",
    "field.limit": "limit",
    "field.planPresent": "plan present",
    "field.decision": "decision",
    "field.cycles": "cycles",
  },
  ko: {
    "brand.subtitle": "운영 콘솔",
    "topbar.kicker": "로컬 우선 제어 계층",
    "action.refresh": "새로고침",
    "action.open": "열기",
    "nav.dashboard": "대시보드",
    "nav.sessions": "세션",
    "nav.monitor": "모니터",
    "nav.projects": "프로젝트",
    "nav.backups": "백업",
    "nav.machines": "머신",
    "nav.commands": "명령",
    "nav.help": "도움말",
    "label.machine": "머신",
    "label.projects": "프로젝트",
    "label.workers": "워커",
    "label.attention": "주의 항목",
    "label.consistency": "일관성",
    "label.sessions": "세션",
    "label.selectedProject": "선택된 프로젝트",
    "label.backups": "백업",
    "label.repos": "저장소",
    "label.console": "콘솔",
    "label.output": "출력",
    "label.system": "시스템",
    "label.project": "프로젝트",
    "label.currentMachine": "현재 머신",
    "label.lifecycle": "생명주기",
    "label.onlineSync": "온라인 동기화",
    "label.agentEntry": "에이전트 진입",
    "label.collab": "Collab",
    "label.newMachine": "새 머신",
    "label.connectionMode": "연결 모드",
    "label.sync": "Repo 동기화",
    "label.versioning": "버전 관리",
    "label.publicationGate": "Publish gate",
    "label.recoveryCoverage": "복구 coverage",
    "label.dirtyWip": "Dirty WIP",
    "label.localSnapshotCoverage": "로컬 snapshot",
    "label.metadataCoverage": "Metadata coverage",
    "label.away": "자리비움",
    "label.pcRoles": "PC 역할",
    "label.visibility": "가시성",
    "label.integration": "통합",
    "label.dataHandling": "데이터 처리",
    "label.recoveryEvidence": "복구 근거",
    "label.latest": "최신 항목",
    "label.guidance": "안내",
    "label.localBackups": "로컬 백업",
    "label.snapshots": "스냅샷",
    "label.localSnapshots": "이 PC manifest",
    "label.localSnapshotManifests": "이 PC manifest",
    "label.localSnapshotFreshness": "manifest 신선도",
    "label.promotedMetadata": "승격 metadata",
    "label.metadataRefs": "Metadata refs",
    "label.artifactPointers": "Artifact pointer",
    "label.artifactManifest": "Artifact manifest",
    "label.dataLocations": "데이터 위치",
    "label.dataNote": "데이터 노트",
    "label.localWorkspaces": "로컬 workspace",
    "label.latestBackup": "최신 백업",
    "label.latestSnapshot": "최신 로컬 manifest",
    "label.latestMetadata": "최신 메타데이터",
    "heading.operationalState": "운영 상태",
    "heading.peerFreshness": "워커 연결",
    "heading.attentionNextSteps": "주의 항목 다음 확인",
    "heading.displayAudit": "표시 일관성 점검",
    "heading.projectPcRoles": "프로젝트별 PC 역할",
    "heading.snapshotsMetadata": "스냅샷 / 메타데이터",
    "heading.codexPeers": "Codex 연결",
    "heading.foundationOps": "Foundation / Ops",
    "heading.commandConsole": "명령 콘솔",
    "heading.collabMonitor": "Collab 모니터",
    "heading.monitorHosts": "모니터 호스트",
    "heading.monitorGuidance": "Monitor 안내",
    "heading.monitorTaskContext": "작업 context",
    "heading.monitorWorkerLinks": "워커 연결",
    "command.scope.systemDiagnostics": "시스템 진단",
    "command.scope.projectDiagnostics": "프로젝트 진단",
    "command.scope.previewOnly": "미리보기 전용",
    "command.scope.collabOnboarding": "Collab 합류 안내",
    "command.scope.projectActions": "상태 변경 프로젝트 작업",
    "command.group.globalDiagnostics": "전체 진단",
    "command.group.projectActions": "프로젝트 작업",
    "command.group.collabOnboarding": "Collab / 새 PC 합류",
    "command.group.coreWorkflows": "핵심 workflow",
    "command.group.advancedDiagnostics": "고급 진단",
    "command.advanced.summary": "고급 기능 열기",
    "command.confirmStateChange": "이 명령은 CLUTCH 또는 프로젝트 상태를 변경합니다. 계속할까요?",
    "command.meta.none": "아직 선택된 명령이 없습니다.",
    "command.empty.initial": "명령을 실행하면 사람이 읽기 쉬운 결과 요약이 여기에 표시됩니다.",
    "command.empty.projectRequired": "이 명령을 실행하려면 먼저 프로젝트를 선택해야 합니다.",
    "command.meta.projectRequired": "프로젝트 범위 명령에는 선택된 프로젝트가 필요합니다.",
    "command.meta.projectTarget": "프로젝트 명령 대상:",
    "command.meta.projectSelect": "프로젝트 범위 명령을 실행하려면 프로젝트를 선택하세요.",
    "command.runningPrefix": "실행 중",
    "command.section.runSummary": "실행 요약",
    "command.section.executed": "실행 명령",
    "command.section.rawJson": "원본 JSON",
    "command.section.executionEvidence": "실행 근거",
    "command.section.bindingRecords": "Binding 기록",
    "command.section.collabAlignment": "Collab 정렬",
    "command.section.workerStatus": "워커 상태",
    "command.section.overview": "전체 개요",
    "command.section.projectStatus": "프로젝트 상태",
    "command.section.versioningReadiness": "버전 관리 준비도",
    "command.section.syncPreview": "동기화 미리보기",
    "command.section.snapshots": "스냅샷",
    "command.section.awayReport": "자리비움 보고",
    "command.section.readableSummary": "읽기 요약",
    "command.noItems": "항목이 없습니다.",
    "command.noCompactSummary": "아직 간단 요약이 없습니다. 전체 내용은 원본 JSON에서 확인하세요.",
    "command.readOnlyDiagnostic": "CLUTCH 읽기 전용 진단 명령입니다.",
    "command.failed": "명령 실행 실패",
    "empty.noProjects": "프로젝트가 없습니다.",
    "empty.noWorkers": "워커가 없습니다.",
    "empty.noSessions": "세션이 없습니다.",
    "empty.noActivePcBindings": "활성 PC binding이 없습니다.",
    "empty.none": "없음",
    "empty.noProjectSelected": "선택된 프로젝트가 없습니다.",
    "empty.noRepos": "저장소가 없습니다.",
    "empty.noAttention": "표시할 주의 항목이 없습니다.",
    "monitor.empty": "아직 collab monitor 데이터가 없습니다.",
    "monitor.loading": "monitor 상태를 갱신하는 중입니다.",
    "monitor.noTasks": "활성 collab 작업 context가 없습니다.",
    "monitor.noRepair": "monitor 복구 조치가 필요 없습니다.",
    "monitor.bindingRoleSource": "CLUTCH binding이 역할 기준이며 transport role은 진단 상태입니다.",
    "monitor.roleSource.alignedDetail": "binding과 transport가 일치",
    "monitor.roleSource.bindingOnlyDetail": "binding 기준, transport는 진단",
    "monitor.roleSource.differsDetail": "위임 전 확인 필요",
    "monitor.roleSource.unknownDetail": "역할 기준 확인 불가",
    "monitor.noGuidance": "아직 표시할 monitor 안내가 없습니다.",
    "monitor.auto": "자동 갱신",
    "monitor.visible": "보임",
    "monitor.hidden": "숨김",
    "monitor.missing": "없음",
    "monitor.roleMismatch": "역할 불일치",
    "monitor.lastUpdated": "마지막 갱신",
    "monitor.taskScope.selected": "선택 project",
    "monitor.taskScope.different": "다른 project 이력",
    "monitor.taskScope.none": "작업 project 없음",
    "monitor.taskNote.active": "활성 작업 context",
    "monitor.taskNote.selectedHistory": "선택 project 이력",
    "monitor.taskNote.otherProjectHistory": "다른 project 이력",
    "monitor.taskNote.staleHistory": "오래된 이력이며 활성 작업이 아님",
    "monitor.taskNote.staleOtherProject": "다른 project의 오래된 이력이며 선택 project의 활성 작업이 아님",
    "monitor.taskNote.recentHistory": "최근 결과 이력",
    "monitor.taskOnlyOtherHistory": "다른 project의 오래된 이력만 있습니다. 선택 project의 활성 작업은 없습니다.",
    "monitor.taskStatus.active": "활성",
    "monitor.taskStatus.recent_history": "최근 이력",
    "monitor.taskStatus.stale_history": "오래된 이력",
    "monitor.taskStatus.history_unknown_age": "이력",
    "monitor.taskStatus.none": "없음",
    "monitor.taskActive": "활성",
    "monitor.taskSelected": "선택",
    "monitor.taskHistory": "이력",
    "monitor.taskStale": "오래됨",
    "audit.cleanTitle": "표시 일관성 문제가 감지되지 않았습니다.",
    "audit.cleanDetail": "Health, overview, session 집계가 서로 일치합니다.",
    "audit.projectListMismatch": "프로젝트 목록 불일치",
    "audit.sessionProjectMismatch": "세션 프로젝트 불일치",
    "audit.activeBindingMismatch": "활성 binding 합계 불일치",
    "audit.healthSessionMismatch": "Health/session binding 불일치",
    "audit.archivedPresent": "보관된 binding이 있습니다.",
    "audit.multipleMainDetail": "한 프로젝트는 활성 main PC 하나만 가져야 합니다.",
    "audit.noMainDetail": "Observer-only 작업에서는 가능하지만 main/sub 협업은 활성 상태가 아닙니다.",
    "status.ready": "준비됨",
    "status.review": "확인 필요",
    "status.blocked": "차단됨",
    "status.observe": "관찰",
    "status.loading": "불러오는 중",
    "status.error": "오류",
    "status.running": "실행 중",
    "status.complete": "완료",
    "status.idle": "대기",
    "status.approval": "승인 필요",
    "status.metadata": "메타데이터",
    "status.metadata_only": "메타데이터만",
    "status.fresh": "최신",
    "status.dirty": "변경 있음",
    "status.available": "사용 가능",
    "status.missing": "없음",
    "status.disabled": "비활성",
    "status.busy": "작업 중",
    "status.stale": "오래됨",
    "status.failed": "실패",
    "status.no_main": "main 없음",
    "status.no_sessions": "세션 없음",
    "status.multiple_main": "main 중복",
    "status.unbound": "binding 미정렬",
    "status.aligned": "정렬됨",
    "status.binding_role_only": "binding 기준",
    "status.transport_role_differs": "transport 역할 다름",
    "status.bound": "연결됨",
    "status.unassigned": "미지정",
    "status.warning": "경고",
    "status.legacy_import": "레거시 통합",
    "status.formalizing": "정식화 중",
    "status.unknown": "알 수 없음",
    "status.clean": "깨끗함",
    "status.mismatch": "불일치",
    "status.archive": "보관",
    "status.conflict": "충돌",
    "status.needs_artifact_pointers": "Artifact pointer 필요",
    "status.artifact_pointers_recorded": "Artifact pointer 기록됨",
    "status.code_metadata_only": "코드/메타데이터만",
    "status.audit_when_empty": "빈 경우 감사",
    "status.canonical_online_ready": "온라인 기준 준비됨",
    "status.recovery_ready_publication_review": "복구 준비, publish 확인",
    "status.attention_required": "확인 필요",
    "status.review_recommended": "검토 권장",
    "status.clean_publication_ready": "깨끗한 publish 준비됨",
    "status.publication_review_required": "publish 확인 필요",
    "role.main": "메인 PC",
    "role.worker": "서브 PC",
    "role.observer": "관찰 PC",
    "role.unknown": "알 수 없는 PC",
    "role.unassigned": "미지정",
    "word.yes": "ok",
    "word.no": "no",
    "word.present": "있음",
    "word.none": "없음",
    "word.ready": "준비됨",
    "word.review": "확인 필요",
    "word.match": "일치",
    "word.warning": "경고",
    "word.clean": "깨끗함",
    "word.mutating": "변경 가능",
    "word.readOnly": "읽기 전용",
    "word.complete": "완료",
    "word.return": "반환",
    "field.command": "명령",
    "field.scope": "범위",
    "field.result": "결과",
    "field.duration": "소요 시간",
    "field.confirmationRequired": "확인 필요",
    "field.confirmed": "확인됨",
    "field.status": "상태",
    "field.thread": "thread",
    "field.project": "프로젝트",
    "field.aligned": "정렬됨",
    "field.created": "생성됨",
    "field.warnings": "경고",
    "field.dryRun": "dry run",
    "field.workers": "워커",
    "field.available": "사용 가능",
    "field.busy": "작업 중",
    "field.stale": "오래됨",
    "field.machine": "머신",
    "field.attention": "주의 항목",
    "field.workspace": "작업 경로",
    "field.syncReady": "Repo 동기화",
    "field.mainSub": "main/sub",
    "field.onlineBackup": "온라인 백업",
    "field.ok": "정상",
    "field.routinePublish": "일상 publish",
    "field.reproducibility": "재현성",
    "field.blockers": "차단 항목",
    "field.required": "필수 repo",
    "field.count": "개수",
    "field.latest": "최신",
    "field.limit": "제한",
    "field.planPresent": "계획 존재",
    "field.decision": "판단",
    "field.cycles": "사이클",
  },
};

const MONITOR_REFRESH_MS = 5000;
let monitorRefreshTimer = null;

const state = {
  activeView: initialView(),
  lang: initialLang(),
  health: null,
  overview: null,
  sessions: null,
  selectedProject: "",
  commandResult: null,
  collabMonitor: null,
  collabMonitorLoading: false,
  collabMonitorProject: "",
  collabMonitorError: "",
};

const $ = (id) => document.getElementById(id);

function initialLang() {
  const queryLang = new URLSearchParams(window.location.search).get("lang");
  if (SUPPORTED_LANGS.has(queryLang)) {
    window.localStorage.setItem(LANG_STORAGE_KEY, queryLang);
    return queryLang;
  }
  const stored = window.localStorage.getItem(LANG_STORAGE_KEY);
  if (SUPPORTED_LANGS.has(stored)) return stored;
  return "ko";
}

function displayLang() {
  return state.lang;
}

function t(key, fallback = key) {
  const lang = displayLang();
  return TEXT[lang]?.[key] || TEXT.en[key] || fallback;
}

function localizedStatus(value) {
  if (value === null || value === undefined || value === "") return "-";
  const key = String(value).toLowerCase().replaceAll(" ", "_");
  return t(`status.${key}`, String(value));
}

function localizedWord(value) {
  if (value === null || value === undefined || value === "") return "-";
  const key = String(value).toLowerCase().replaceAll(" ", "_");
  return t(`word.${key}`, localizedStatus(value));
}

function boolText(value) {
  return value ? t("word.yes") : t("word.no");
}

function renderI18nText() {
  const lang = displayLang();
  document.documentElement.lang = lang;
  document.title = lang === "ko" ? "CLUTCH 콘솔" : "CLUTCH Console";
  document.body.dataset.lang = lang;
  document.body.dataset.view = state.activeView;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-lang]").forEach((button) => {
    const active = button.dataset.lang === state.lang;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  document.querySelectorAll("[data-help-lang]").forEach((node) => {
    const active = node.dataset.helpLang === lang;
    node.hidden = !active;
    node.setAttribute("aria-hidden", String(!active));
  });
  renderCommandSurface();
}

function localizedMeta(value, fallback = "") {
  if (!value) return fallback;
  if (typeof value === "string") return value;
  return value[state.lang] || value.en || Object.values(value)[0] || fallback;
}

function commandRegistryEntry(commandKey) {
  return state.health?.command_registry?.[commandKey] || null;
}

function commandGroupKeys(groupId) {
  const group = (state.health?.command_groups || []).find((item) => item.group_id === groupId);
  if (group?.command_keys) return group.command_keys;
  if (groupId === "default") return state.health?.default_command_keys || [];
  return [];
}

function commandGroupEntry(groupId) {
  return (state.health?.command_groups || []).find((item) => item.group_id === groupId) || null;
}

function commandRegistryAvailable() {
  return Boolean(state.health?.command_registry && Array.isArray(state.health?.command_groups));
}

function commandRegistrySurfaceOk() {
  const surface = state.health?.command_surface_integrity;
  if (surface) return Boolean(surface.ok);
  return Boolean(state.health?.command_surface_integrity_ok ?? state.health?.command_registry_rollout?.surface_integrity_ok);
}

function commandSurfaceRenderReady() {
  const rollout = state.health?.command_registry_rollout || {};
  if (typeof state.health?.command_surface_render_ready === "boolean") return state.health.command_surface_render_ready;
  if (typeof rollout.render_ready === "boolean") return rollout.render_ready;
  return false;
}

function defaultCommandGroupReady() {
  const rollout = state.health?.command_registry_rollout || {};
  if (typeof state.health?.default_command_group_ready === "boolean") return state.health.default_command_group_ready;
  if (typeof rollout.default_group_ready === "boolean") return rollout.default_group_ready;
  return commandSurfaceRenderReady() && (state.health?.default_command_keys || []).length > 0;
}

function commandRegistryLoadingText() {
  return state.lang === "ko"
    ? "명령 registry를 불러오는 중입니다."
    : "Loading command registry.";
}

function commandRegistryWarningText() {
  return state.lang === "ko"
    ? "명령 registry를 불러오지 못했습니다. CLUTCH web UI 프로세스를 재시작한 뒤 새로고침하세요."
    : "Command registry is unavailable. Restart the CLUTCH web UI process, then refresh this page.";
}

function commandSurfaceWarningText() {
  return state.lang === "ko"
    ? "명령 화면 점검이 필요합니다. CLUTCH web UI 프로세스와 정적 asset 버전을 확인하세요."
    : "Command surface needs review. Check the CLUTCH web UI process and static asset version.";
}

function commandGroupEmptyText() {
  return state.lang === "ko"
    ? "이 명령 그룹에 연결된 버튼이 없습니다. registry rollout 상태를 확인하세요."
    : "No buttons are linked to this command group. Check registry rollout state.";
}

function commandRegistryMetaText() {
  if (!state.health) return state.lang === "ko" ? "명령 registry 불러오는 중" : "Loading command registry";
  if (!commandRegistryAvailable()) return commandRegistryWarningText();
  const rollout = state.health.command_registry_rollout || {};
  const commandCount = rollout.command_count ?? state.health.command_registry_command_count ?? Object.keys(state.health.command_registry || {}).length;
  const defaultCount = rollout.default_command_count ?? state.health.default_command_count ?? (state.health.default_command_keys || []).length;
  const advancedCount = rollout.advanced_command_count ?? state.health.advanced_command_count ?? (state.health.advanced_command_keys || []).length;
  const version = rollout.backend_version || state.health.web_backend_version || "-";
  const integrity = state.health.command_registry_integrity;
  const integrityOk = integrity ? Boolean(integrity.ok) : Boolean(rollout.integrity_ok ?? state.health.command_registry_integrity_ok);
  const findingCount = integrity?.summary?.finding_count ?? 0;
  const surface = state.health.command_surface_integrity;
  const surfaceOk = commandRegistrySurfaceOk();
  const surfaceFindingCount = surface?.summary?.finding_count ?? 0;
  if (integrity && !integrityOk) {
    return state.lang === "ko"
      ? `명령 registry 점검 필요: finding ${findingCount}개 / backend ${version}`
      : `Command registry needs review: ${findingCount} findings / backend ${version}`;
  }
  if (!surfaceOk) {
    return state.lang === "ko"
      ? `명령 화면 점검 필요: finding ${surfaceFindingCount}개 / backend ${version}`
      : `Command surface needs review: ${surfaceFindingCount} findings / backend ${version}`;
  }
  if (!commandSurfaceRenderReady()) {
    return state.lang === "ko"
      ? `명령 버튼 렌더 준비 안 됨 / backend ${version}`
      : `Command buttons are not render-ready / backend ${version}`;
  }
  return state.lang === "ko"
    ? `명령 registry ${commandCount}개 / 기본 ${defaultCount}개 / 고급 ${advancedCount}개 / 무결성 OK / backend ${version}`
    : `Command registry ${commandCount} / default ${defaultCount} / advanced ${advancedCount} / integrity OK / backend ${version}`;
}

function updateCommandGroupHeading(groupNode) {
  const group = commandGroupEntry(groupNode.dataset.commandGroup);
  if (!group) return;
  const labelNode = groupNode.querySelector(":scope > .command-group-title .small-label");
  const titleNode = groupNode.querySelector(":scope > .command-group-title strong");
  if (labelNode) labelNode.textContent = localizedMeta(group.label, group.group_id || "");
  if (titleNode) titleNode.textContent = localizedMeta(group.title, group.group_id || "");
}

function commandRequiresProject(commandKey) {
  const entry = commandRegistryEntry(commandKey);
  if (entry) return Boolean(entry.project_scoped);
  return commandKey.startsWith("project-") || commandKey.startsWith("collab-") || commandKey === "machine-collab-guide";
}

function commandChangesStateClient(commandKey) {
  const entry = commandRegistryEntry(commandKey);
  if (entry) return Boolean(entry.state_changing);
  return (state.health?.state_changing_commands || []).includes(commandKey);
}

function commandRequiresConfirmationClient(commandKey) {
  const entry = commandRegistryEntry(commandKey);
  if (entry) return Boolean(entry.confirmation_required);
  return (state.health?.confirmation_required_commands || state.health?.state_changing_commands || []).includes(commandKey);
}

function commandPolicyBadges(commandKey) {
  const entry = commandRegistryEntry(commandKey);
  if (Array.isArray(entry?.policy_badges) && entry.policy_badges.length) return entry.policy_badges;
  return [
    {
      label: commandChangesStateClient(commandKey) ? t("word.mutating") : t("word.readOnly"),
      tone: commandChangesStateClient(commandKey) ? "write" : "read",
    },
  ];
}

function createCommandButton(commandKey) {
  const details = commandDetails(commandKey);
  const button = document.createElement("button");
  button.className = `button command${commandChangesStateClient(commandKey) ? " write" : ""}`;
  button.type = "button";
  button.dataset.command = commandKey;
  const title = document.createElement("strong");
  title.textContent = details.title;
  const detail = document.createElement("span");
  detail.className = "command-detail";
  detail.textContent = details.detail;
  const badges = document.createElement("div");
  badges.className = "command-badge-row";
  for (const badge of commandPolicyBadges(commandKey)) {
    const item = document.createElement("span");
    item.className = `command-badge ${badge.tone || "neutral"}`;
    item.textContent = localizedMeta(badge.label, String(badge.label || ""));
    badges.appendChild(item);
  }
  button.append(title, detail, badges);
  return button;
}

function renderCommandSurface() {
  document.querySelectorAll("[data-command-group]").forEach((groupNode) => {
    updateCommandGroupHeading(groupNode);
    groupNode.querySelectorAll(":scope > button.command").forEach((button) => button.remove());
    groupNode.querySelectorAll(":scope > .command-registry-warning").forEach((node) => node.remove());
    if (!state.health) {
      if (groupNode.dataset.commandGroup === "default") {
        const loading = document.createElement("div");
        loading.className = "command-registry-warning";
        loading.textContent = commandRegistryLoadingText();
        groupNode.appendChild(loading);
      }
      return;
    }
    if (!commandRegistryAvailable()) {
      if (groupNode.dataset.commandGroup === "default") {
        const warning = document.createElement("div");
        warning.className = "command-registry-warning";
        warning.textContent = commandRegistryWarningText();
        groupNode.appendChild(warning);
      }
      return;
    }
    if (!commandRegistrySurfaceOk() && groupNode.dataset.commandGroup === "default") {
      const warning = document.createElement("div");
      warning.className = "command-registry-warning";
      warning.textContent = commandSurfaceWarningText();
      groupNode.appendChild(warning);
    }
    if (groupNode.dataset.commandGroup === "default" && !defaultCommandGroupReady()) {
      const warning = document.createElement("div");
      warning.className = "command-registry-warning";
      warning.textContent = commandGroupEmptyText();
      groupNode.appendChild(warning);
    }
    const groupKeys = commandGroupKeys(groupNode.dataset.commandGroup);
    if (!groupKeys.length) {
      const warning = document.createElement("div");
      warning.className = "command-registry-warning";
      warning.textContent = commandGroupEmptyText();
      groupNode.appendChild(warning);
      return;
    }
    for (const commandKey of groupKeys) {
      groupNode.appendChild(createCommandButton(commandKey));
    }
  });
}

function initialView() {
  const view = window.location.hash.replace("#", "").trim();
  return ["dashboard", "sessions", "monitor", "projects", "backups", "machines", "commands", "help"].includes(view)
    ? view
    : "dashboard";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pill(text, status = "neutral") {
  return `<span class="pill ${status}">${escapeHtml(text)}</span>`;
}

function token(text) {
  return `<span class="token">${escapeHtml(text)}</span>`;
}

function statusTone({ ok = false, warning = false, error = false, info = false } = {}) {
  if (error) return "error";
  if (ok) return "ok";
  if (warning) return "warn";
  if (info) return "info";
  return "neutral";
}

function projectDisplay(project) {
  const counts = project?.attention_severity_counts || {};
  if (!project) return { key: "unknown", label: localizedStatus("unknown"), tone: "neutral" };
  if (
    Number(counts.error_count || 0) > 0 ||
    Number(counts.needs_approval_count || 0) > 0
  ) {
    return { key: "blocked", label: localizedStatus("blocked"), tone: "error" };
  }
  if (!project.ok || Number(counts.warning_count || 0) > 0) {
    return { key: "review", label: localizedStatus("review"), tone: "warn" };
  }
  if (Number(counts.info_count || 0) > 0) {
    return { key: "observe", label: localizedStatus("observe"), tone: "info" };
  }
  return { key: "ready", label: localizedStatus("ready"), tone: "ok" };
}

function integrationDisplay(project) {
  const profile = project?.integration_profile || {};
  const mode = profile.mode || "";
  if (mode === "legacy_import") {
    const status = profile.status || "formalizing";
    return {
      key: "legacy_import",
      label: localizedStatus("legacy_import"),
      status,
      statusLabel: localizedStatus(status),
      tone: status === "complete" ? "ok" : "info",
      canonicalMachine: profile.canonical_machine_id || profile.origin_machine_id || "",
    };
  }
  return {
    key: mode || "native",
    label: state.lang === "ko" ? "CLUTCH native" : "CLUTCH native",
    status: profile.status || "",
    statusLabel: profile.status ? localizedStatus(profile.status) : "",
    tone: "neutral",
    canonicalMachine: "",
  };
}

function integrationToken(project) {
  const display = integrationDisplay(project);
  if (display.key !== "legacy_import") return "";
  const parts = [display.label, display.canonicalMachine].filter(Boolean);
  return token(parts.join(" / "));
}

function projectTone(project) {
  return projectDisplay(project).tone;
}

function workerTone(worker) {
  return statusTone({
    ok: worker?.state_status === "fresh" || worker?.peer_status === "fresh",
    warning: worker?.state_status === "stale" || worker?.peer_status === "unknown",
    error: worker?.state_status === "failed",
  });
}

function bindingTone(project) {
  return statusTone({
    ok: project?.status === "ready",
    warning: project?.status === "no_main" || project?.status === "no_sessions",
    error: project?.status === "multiple_main",
  });
}

function roleLabel(role) {
  return t(`role.${role || "unknown"}`, role || t("role.unknown"));
}

function roleValue(role) {
  if (!role) return "-";
  return t(`role.${role}`, role);
}

function commandDetails(commandKey) {
  const entry = commandRegistryEntry(commandKey);
  if (entry) {
    return {
      title: localizedMeta(entry.title, commandKey || "Command"),
      scope: localizedMeta(entry.scope, commandRequiresProject(commandKey) ? t("label.project") : t("label.system")),
      detail: localizedMeta(entry.detail, ""),
    };
  }
  return {
    title: commandKey || "Command",
    scope: commandRequiresProject(commandKey) ? t("label.project") : t("label.system"),
    detail: "",
  };
}

function globalDisplayState() {
  const overview = state.overview || {};
  const counts = overview.attention_severity_counts || {};
  if (!overview.ok || !state.sessions?.ok || !state.health?.ok) {
    return { label: localizedStatus("review"), tone: "warn" };
  }
  if (Number(counts.error_count || 0) > 0 || Number(counts.needs_approval_count || 0) > 0) {
    return { label: localizedStatus("blocked"), tone: "error" };
  }
  if (Number(counts.warning_count || 0) > 0) {
    return { label: localizedStatus("review"), tone: "warn" };
  }
  if (Number(counts.info_count || 0) > 0) {
    return { label: localizedStatus("observe"), tone: "info" };
  }
  return { label: localizedStatus("ready"), tone: "ok" };
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  let payload = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch (_error) {
    payload = { ok: false, error: text };
  }
  if (!response.ok && payload.ok !== false) {
    payload.ok = false;
  }
  return payload;
}

function settledPayload(result) {
  if (result.status === "fulfilled") return result.value;
  return { ok: false, error: result.reason?.stack || String(result.reason) };
}

function availableProjectIds() {
  const ids = [];
  for (const id of state.health?.project_ids || []) ids.push(id);
  for (const project of state.overview?.projects?.items || []) ids.push(project.project_id);
  for (const project of state.sessions?.projects || []) ids.push(project.project_id);
  return [...new Set(ids.filter(Boolean))];
}

async function loadAll() {
  setStatus(localizedStatus("loading"), "neutral");
  const [healthResult, sessionsResult] = await Promise.allSettled([
    requestJson("/api/health"),
    requestJson("/api/sessions"),
  ]);
  state.health = settledPayload(healthResult);
  state.sessions = settledPayload(sessionsResult);
  const projectIds = availableProjectIds();
  if (!state.selectedProject && projectIds.length) {
    state.selectedProject = projectIds.includes("clutch") ? "clutch" : projectIds[0];
  }
  render();
  setStatus(localizedStatus("loading"), "neutral");
  const overviewResult = await Promise.allSettled([
    requestJson("/api/overview?runtime=false&workers=true&hardware=false"),
  ]);
  state.overview = settledPayload(overviewResult[0]);
  const updatedProjectIds = availableProjectIds();
  if (!state.selectedProject && updatedProjectIds.length) {
    state.selectedProject = updatedProjectIds.includes("clutch") ? "clutch" : updatedProjectIds[0];
  }
  render();
}

async function loadCollabMonitor({ silent = false } = {}) {
  if (!state.selectedProject) {
    state.collabMonitor = null;
    state.collabMonitorProject = "";
    state.collabMonitorError = "";
    renderMonitorView();
    return;
  }
  if (state.collabMonitorLoading && state.collabMonitorProject === state.selectedProject) return;
  state.collabMonitorLoading = true;
  state.collabMonitorProject = state.selectedProject;
  state.collabMonitorError = "";
  if (!silent) renderMonitorView();
  try {
    const payload = await requestJson(`/api/collab-monitor?project=${encodeURIComponent(state.selectedProject)}`);
    state.collabMonitor = payload;
    state.collabMonitorError = payload.ok === false ? payload.error || payload.status || "monitor fetch failed" : "";
  } catch (error) {
    state.collabMonitorError = error.stack || String(error);
    state.collabMonitor = {
      ok: false,
      operator_judgement: { label: state.collabMonitorError, status: "review", tone: "warn" },
      monitor_status: { ok: false, monitors: [], monitor_count: 0, running_count: 0, operator_visible_count: 0, missing_count: 0, hidden_count: 0 },
    };
  } finally {
    state.collabMonitorLoading = false;
    renderMonitorView();
  }
}

async function refreshConsole() {
  await loadAll();
  if (state.activeView === "monitor" && state.selectedProject) {
    await loadCollabMonitor({ silent: true });
  }
}

function setStatus(text, cls) {
  const node = $("statusBadge");
  node.textContent = text;
  node.className = `pill ${cls}`;
}

function setCommandState(text, cls = "neutral") {
  const node = $("commandState");
  node.textContent = text;
  node.className = `pill ${cls}`;
}

function commandResultJudgement(result) {
  const judgement = result?.operator_judgement;
  if (judgement && typeof judgement === "object") {
    const tone = summaryToneClass(judgement.tone);
    const fallbackLabel = judgement.status ? localizedStatus(judgement.status) : "";
    const label = localizedMeta(judgement.label, fallbackLabel);
    if (label) return { label, tone };
  }
  const blocks = Array.isArray(result?.summary_blocks) ? result.summary_blocks : [];
  const primaryTone = blocks.length ? summaryToneClass(blocks[0]?.tone) : "neutral";
  if (primaryTone === "error") return { label: localizedStatus("blocked"), tone: "error" };
  if (primaryTone === "warn") return { label: localizedStatus("review"), tone: "warn" };
  if (primaryTone === "info" && result?.ok) return { label: localizedStatus("observe"), tone: "info" };
  if (result?.ok) return { label: localizedStatus("complete"), tone: "ok" };
  return { label: localizedStatus("review"), tone: "warn" };
}

function render() {
  renderI18nText();
  const display = globalDisplayState();
  const overview = state.overview || {};
  setStatus(display.label, display.tone);
  $("sidebarMachine").textContent = overview.machine_id || state.health?.machine_id || "-";
  renderNav();
  renderProjectSelect();
  renderDashboard();
  renderAttentionWorkflow();
  renderProjects();
  renderWorkers();
  renderSessions();
  renderProjectDetail();
  renderBackupsView();
  renderMachinesView();
  renderMonitorView();
  renderDisplayAudit();
  renderCommandContext();
  renderCommandLog();
  syncMonitorPolling();
}

function renderNav() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    const active = button.dataset.view === state.activeView;
    button.classList.toggle("active", active);
  });
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.viewPanel === state.activeView);
  });
  const labels = {
    dashboard: t("nav.dashboard"),
    sessions: t("nav.sessions"),
    monitor: t("nav.monitor"),
    projects: t("nav.projects"),
    backups: t("nav.backups"),
    machines: t("nav.machines"),
    commands: t("nav.commands"),
    help: t("nav.help"),
  };
  $("pageTitle").textContent = labels[state.activeView] || t("nav.dashboard");
}

function renderProjectSelect() {
  const select = $("projectSelect");
  const ids = availableProjectIds();
  select.innerHTML = ids
    .map((id) => `<option value="${escapeHtml(id)}">${escapeHtml(id)}</option>`)
    .join("");
  if (ids.length && !ids.includes(state.selectedProject)) {
    state.selectedProject = ids[0];
  }
  select.value = state.selectedProject;
}

function renderDashboard() {
  const overview = state.overview || {};
  const projects = overview.projects || {};
  const workers = overview.workers || {};
  const counts = overview.attention_severity_counts || {};
  const projectItems = projects.items || [];
  const workerItems = workers.items || [];
  const projectStates = projectItems.map(projectDisplay);
  const projectReviewCount = projectStates.filter((item) => item.tone === "warn" || item.tone === "error").length;
  const projectObserveCount = projectStates.filter((item) => item.tone === "info").length;
  const workerReviewCount = workerItems.filter(
    (worker) => worker.activity !== "available" || worker.state_status !== "fresh" || worker.peer_status === "unknown",
  ).length;
  $("machineTitle").textContent = overview.machine_display_name
    ? `${overview.machine_display_name} / ${overview.machine_id || "-"}`
    : overview.machine_id || "-";
  $("threadTitle").textContent = `${t("field.thread")} ${overview.thread_id || "-"}`;
  $("projectSummary").textContent = `${projects.ok_count ?? 0}/${projects.project_count ?? 0}`;
  $("projectSummaryDetail").textContent = projectReviewCount
    ? (
      projectObserveCount
        ? (
          state.lang === "ko"
            ? `${projectReviewCount}개 확인 필요 / ${projectObserveCount}개 관찰`
            : `${projectReviewCount} need review / ${projectObserveCount} observe`
        )
        : (
          state.lang === "ko"
            ? `${projectReviewCount}개 프로젝트 확인 필요`
            : `${projectReviewCount} need review`
        )
    )
    : projectObserveCount
      ? (state.lang === "ko" ? `${projectObserveCount}개 프로젝트 관찰` : `${projectObserveCount} observe`)
      : (state.lang === "ko" ? "운영 가능한 프로젝트" : "operational projects");
  $("workerSummary").textContent = `${workers.available_count ?? 0}/${workers.worker_count ?? 0}`;
  $("workerSummaryDetail").textContent = workerReviewCount
    ? (state.lang === "ko" ? `${workerReviewCount}개 워커 확인 필요` : `${workerReviewCount} disabled, stale, or unknown`)
    : (state.lang === "ko" ? "사용 가능한 워커" : "available workers");
  $("attentionSummary").textContent = `${counts.total_count ?? overview.attention_count ?? 0}`;
  $("attentionSummaryDetail").textContent =
    state.lang === "ko"
      ? `경고 ${counts.warning_count ?? 0} / 정보 ${counts.info_count ?? 0} / 오류 ${counts.error_count ?? 0} / 승인 ${counts.needs_approval_count ?? 0}`
      : `warn ${counts.warning_count ?? 0} / info ${counts.info_count ?? 0} / error ${counts.error_count ?? 0} / approval ${counts.needs_approval_count ?? 0}`;
}

function collectAttentionItems() {
  const overview = state.overview || {};
  const byKey = new Map();
  const add = (item, projectId = "") => {
    if (!item || typeof item !== "object") return;
    const normalized = {
      ...item,
      project_id: item.project_id || projectId || "",
    };
    const key = [
      normalized.project_id,
      normalized.kind,
      normalized.repo_id,
      normalized.status,
      normalized.message,
    ].map((value) => String(value || "")).join("|");
    if (!byKey.has(key)) byKey.set(key, normalized);
  };
  if (Array.isArray(overview.attention_items)) {
    overview.attention_items.forEach((item) => add(item));
  }
  for (const project of overview.projects?.items || []) {
    if (Array.isArray(project.attention_items)) {
      project.attention_items.forEach((item) => add(item, project.project_id));
    }
  }
  return [...byKey.values()];
}

function attentionItemTone(item) {
  const severity = String(item?.severity || "").toLowerCase();
  if (severity === "error" || severity === "needs_approval" || severity === "blocked") return "error";
  if (severity === "warning" || severity === "warn") return "warn";
  if (severity === "info") return "info";
  return "neutral";
}

function attentionShortcutCommands(item) {
  const registry = state.health?.command_registry || {};
  const shortcutRegistry = state.health?.attention_shortcuts || {};
  const kindCommands = shortcutRegistry.kind_commands || {};
  const kind = String(item?.kind || "").toLowerCase();
  const projectId = String(item?.project_id || "");
  const maxPerItem = Number(shortcutRegistry.max_per_item || 3);
  const selected = [];
  const add = (commandKey) => {
    if (!commandKey || selected.includes(commandKey) || !registry[commandKey]) return;
    if (registry[commandKey].project_scoped && !projectId) return;
    selected.push(commandKey);
  };

  if (projectId) add(shortcutRegistry.fallback_command_key || "project-attention-resolution-plan");
  for (const commandKey of kindCommands[kind] || []) {
    add(commandKey);
  }
  return selected.slice(0, maxPerItem || 3);
}

function attentionNeedsMonitor(item) {
  const shortcutRegistry = state.health?.attention_shortcuts || {};
  const kindCommands = shortcutRegistry.kind_commands || {};
  const kind = String(item?.kind || "").toLowerCase();
  const commands = Array.isArray(kindCommands[kind]) ? kindCommands[kind] : [];
  if (commands.includes("collab-monitor-status")) return true;
  return new Set([
    "collab",
    "collab_readiness",
    "collab_monitor",
    "collab_binding",
    "binding_alignment",
    "monitor_visibility",
    "worker_link",
    "runtime",
  ]).has(kind);
}

function attentionItemSummary(item) {
  const kind = String(item?.kind || "").toLowerCase();
  const status = String(item?.status || "").toLowerCase();
  const operatorSummary = String(item?.operator_summary || "").trim();
  if (kind === "repo_sync" && status === "dirty_worktree") {
    return state.lang === "ko"
      ? "로컬 작업 중인 변경사항이 있어 pull/sync를 잠시 막았습니다. 작업을 커밋하거나 checkpoint로 보존하면 해제됩니다."
      : "Local WIP is blocking pull/sync for now. Commit it or preserve it in a checkpoint to clear this gate.";
  }
  if (kind === "versioning_readiness") {
    return state.lang === "ko"
      ? "현재 프로젝트 상태의 재현성 근거를 확인해야 합니다. 전체 새로고침 점검을 먼저 실행하세요."
      : "Project reproducibility evidence needs review. Run Refresh Check first.";
  }
  return operatorSummary || item?.message || item?.kind || "-";
}

function renderAttentionMonitorLink(item, projectId) {
  if (!projectId || !attentionNeedsMonitor(item)) return "";
  return `
    <a
      class="button mini shortcut"
      href="#monitor"
      data-monitor-project="${escapeHtml(projectId)}"
      data-monitor-shortcut="attention"
    >${escapeHtml(t("nav.monitor"))}</a>
  `;
}

function renderAttentionWorkflow() {
  const items = collectAttentionItems();
  const warningCount = items.filter((item) => attentionItemTone(item) === "warn").length;
  const errorCount = items.filter((item) => attentionItemTone(item) === "error").length;
  const badge = $("attentionWorkflowBadge");
  badge.textContent = state.lang === "ko"
    ? `총 ${items.length} / 확인 ${warningCount} / 차단 ${errorCount}`
    : `${items.length} total / ${warningCount} review / ${errorCount} blocked`;
  badge.className = `pill ${errorCount ? "error" : warningCount ? "warn" : items.length ? "info" : "ok"}`;
  $("attentionWorkflowList").innerHTML = items.length
    ? items.slice(0, 8).map(renderAttentionItem).join("")
    : emptyCard(t("empty.noAttention"));
}

function renderAttentionItem(item) {
  const tone = attentionItemTone(item);
  const projectId = String(item.project_id || "");
  const shortcuts = attentionShortcutCommands(item);
  const monitorLink = renderAttentionMonitorLink(item, projectId);
  const actions = [
    monitorLink,
    ...shortcuts.map((commandKey) => renderAttentionShortcutButton(commandKey, projectId)),
  ].filter(Boolean);
  return `
    <article class="attention-card ${tone}">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(projectId || t("label.system"))}</strong>
          <span class="subtle">${escapeHtml(attentionItemSummary(item))}</span>
        </div>
        ${pill(localizedStatus(item.severity || tone), tone)}
      </div>
      <div class="token-row">
        ${token(`${state.lang === "ko" ? "종류" : "kind"} ${item.kind || "-"}`)}
        ${item.repo_id ? token(`repo ${item.repo_id}`) : ""}
        ${item.status ? token(`${t("field.status")} ${localizedStatus(item.status)}`) : ""}
        ${item.dirty_summary ? token(item.dirty_summary) : ""}
      </div>
      ${
        actions.length
          ? `<div class="attention-actions">${actions.join("")}</div>`
          : `<span class="subtle">${escapeHtml(state.lang === "ko" ? "연결된 읽기 전용 workflow가 없습니다." : "No read-only workflow shortcut is linked yet.")}</span>`
      }
    </article>
  `;
}

function renderAttentionShortcutButton(commandKey, projectId) {
  const details = commandDetails(commandKey);
  return `
    <button
      class="button mini shortcut"
      type="button"
      data-command="${escapeHtml(commandKey)}"
      data-command-shortcut="attention"
      ${projectId ? `data-command-project="${escapeHtml(projectId)}"` : ""}
    >${escapeHtml(details.title)}</button>
  `;
}

function renderProjects() {
  const projects = state.overview?.projects?.items || [];
  $("projectsList").innerHTML = projects.map(renderProjectItem).join("") || emptyCard(t("empty.noProjects"));
}

function renderProjectItem(project) {
  const sync = project.sync_summary || {};
  const versioning = project.versioning_readiness || {};
  const freshness = project.project_snapshot_freshness || {};
  const session = sessionProject(project.project_id);
  const roleCounts = session?.machine_role_counts || project.bindings || {};
  const display = projectDisplay(project);
  const selected = project.project_id === state.selectedProject;
  return `
    <article class="item-card project-card ${selected ? "selected" : ""}">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(project.display_name || project.project_id)}</strong>
          <span class="subtle">${escapeHtml(project.workspace_path || "-")}</span>
        </div>
        <div class="item-actions">
          ${pill(display.label, display.tone)}
          <button class="button mini" type="button" data-select-project="${escapeHtml(project.project_id)}">${escapeHtml(t("action.open"))}</button>
        </div>
      </div>
      <div class="token-row">
        ${integrationToken(project)}
        ${token(`${t("label.sync")} ${sync.required_sync_ready_count ?? 0}/${sync.required_repo_count ?? 0}`)}
        ${token(`${localizedStatus("blocked")} ${sync.required_blocked_count ?? 0}`)}
        ${token(`${t("label.versioning")} ${versioning.routine_publish_ready ? localizedWord("ready") : localizedWord("review")}`)}
        ${token(`${t("label.localSnapshotFreshness")} ${localizedStatus(freshness.status || "-")}`)}
        ${token(`${t("label.promotedMetadata")} ${project.valid_snapshot_metadata_ref_count ?? 0}/${project.snapshot_metadata_ref_count ?? 0}`)}
        ${token(`${t("label.pcRoles")} ${roleCounts.main ?? roleCounts.main_count ?? 0}/${roleCounts.worker ?? roleCounts.worker_count ?? 0}/${roleCounts.observer ?? roleCounts.observer_count ?? 0}`)}
      </div>
    </article>
  `;
}

function renderWorkers() {
  const workers = state.overview?.workers?.items || [];
  $("workersList").innerHTML = workers.map(renderWorkerItem).join("") || emptyCard(t("empty.noWorkers"));
}

function renderWorkerItem(worker) {
  const tone = workerTone(worker);
  return `
    <article class="item-card">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(worker.display_name || worker.host || "-")}</strong>
          <span class="subtle">${escapeHtml(worker.host || "-")} -> ${escapeHtml(worker.peer_host || "-")}</span>
        </div>
        ${pill(localizedStatus(worker.activity || stateStatus || "unknown"), tone)}
      </div>
      <div class="token-row">
        ${token(`${state.lang === "ko" ? "역할" : "role"} ${roleValue(worker.role)}`)}
        ${token(`${state.lang === "ko" ? "상태" : "state"} ${localizedStatus(worker.state_status || "-")}`)}
        ${token(`${state.lang === "ko" ? "연결" : "link"} ${localizedStatus(worker.peer_status || "-")}`)}
        ${token(`${state.lang === "ko" ? "대기열" : "queue"} ${worker.queue_length ?? 0}`)}
      </div>
    </article>
  `;
}

function renderSessions() {
  const sessionProjects = state.sessions?.projects || [];
  const activeCount = state.sessions?.active_binding_count ?? state.sessions?.binding_count ?? 0;
  const inactiveCount = state.sessions?.inactive_binding_count ?? 0;
  $("bindingSummary").textContent = state.lang === "ko"
    ? `활성 ${activeCount} / 보관 ${inactiveCount}`
    : `${activeCount} active / ${inactiveCount} archived`;
  $("bindingSummary").className = "pill info";
  $("sessionsList").innerHTML = sessionProjects.map(renderSessionProject).join("") || emptyCard(t("empty.noSessions"));
}

function renderSessionProject(project) {
  const roles = project.role_counts || {};
  const configured = project.configured_machine_roles || {};
  const machines = project.machines || [];
  const collabLinks = project.collab_links || [];
  const tone = bindingTone(project);
  return `
    <article class="session-card">
      <div class="session-row">
        <div class="title-stack">
          <strong>${escapeHtml(project.project_id)}</strong>
          <span class="subtle">${escapeHtml(state.lang === "ko" ? "활성 상태이며 만료되지 않은 binding 기준 PC 역할 요약" : "PC role summary from active, unexpired bindings")}</span>
        </div>
        ${pill(localizedStatus(project.status || "-"), tone)}
      </div>
      <div class="token-row">
        ${token(`${roleLabel("main")} ${roles.main ?? 0}`)}
        ${token(`${roleLabel("worker")} ${roles.worker ?? 0}`)}
        ${token(`${roleLabel("observer")} ${roles.observer ?? 0}`)}
        ${token(`${state.lang === "ko" ? "설정" : "configured"} ${configuredRoleSummary(configured)}`)}
        ${token(`${state.lang === "ko" ? "활성 세션" : "active sessions"} ${project.binding_count ?? 0}`)}
      </div>
      ${renderSessionMonitorContext(project)}
      <div class="machine-groups">
        ${renderMachineGroups(machines)}
        ${renderCollabLinks(collabLinks)}
      </div>
    </article>
  `;
}

function renderSessionMonitorContext(project) {
  const context = project.monitor_context || {};
  const roles = project.role_counts || {};
  const collabLinks = project.collab_links || [];
  const hasCollabContext = collabLinks.length || Number(roles.worker || 0) > 0 || Number(roles.main || 0) > 0;
  if (!hasCollabContext || (!context.status_command && !context.web_monitor_url)) return "";
  const standard = context.standard === "main_and_sub_visible_monitors"
    ? (state.lang === "ko" ? "main/sub visible" : "main/sub visible")
    : context.standard || "-";
  const monitorUrl = String(context.web_monitor_url || "");
  const monitorTarget = monitorUrl ? monitorUrl.replace(/^https?:\/\/127\.0\.0\.1:\d+\/?/, "#") : "";
  return `
    <div class="session-monitor-context">
      <div class="token-row">
        ${token(`monitor ${standard}`)}
        ${monitorTarget ? token(monitorTarget) : ""}
      </div>
      <a href="#monitor" data-monitor-project="${escapeHtml(project.project_id || "")}">${escapeHtml(t("nav.monitor"))}</a>
      ${context.status_command ? `<code>${escapeHtml(context.status_command)}</code>` : ""}
    </div>
  `;
}

function configuredRoleSummary(roles) {
  if ((roles?.expectation_policy || roles?.machine_role_policy) === "none") {
    return state.lang === "ko" ? "없음" : "none";
  }
  const main = roles?.main_machine_ids || [];
  const worker = roles?.worker_machine_ids || roles?.sub_machine_ids || [];
  return `M ${main.length || 0} / W ${worker.length || 0}`;
}

function renderMachineGroups(machines) {
  if (!machines.length) {
    return `<span class="subtle">${escapeHtml(t("empty.noActivePcBindings"))}</span>`;
  }
  return ["main", "worker", "observer"]
    .map((role) => {
      const items = machines.filter((machine) => machine.primary_role === role);
      return `
        <section class="role-group">
          <div class="role-heading">
            <span>${escapeHtml(roleLabel(role))}</span>
            ${pill(String(items.length), items.length ? (role === "main" ? "ok" : "info") : "neutral")}
          </div>
          <div class="machine-list">
            ${items.map(renderMachine).join("") || `<span class="subtle">${escapeHtml(t("empty.none"))}</span>`}
          </div>
        </section>
      `;
    })
    .join("");
}

function renderMachine(machine) {
  const roles = machine.roles || [];
  const roleText = roles.map(roleValue).join(", ") || "-";
  const workspaces = machine.workspace_paths || [];
  return `
    <div class="machine-row">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(machine.machine_id || "-")}</strong>
          <span class="subtle">${escapeHtml(workspaces[0] || "-")}</span>
        </div>
        ${pill(roleLabel(machine.primary_role), machine.primary_role === "main" ? "ok" : "info")}
      </div>
      <div class="token-row">
        ${token(`${state.lang === "ko" ? "역할" : "roles"} ${roleText}`)}
        ${token(`${state.lang === "ko" ? "세션" : "sessions"} ${machine.binding_count ?? 0}`)}
        ${token(`${state.lang === "ko" ? "thread 수" : "threads"} ${machine.thread_count ?? 0}`)}
      </div>
    </div>
  `;
}

function renderCollabLinks(links) {
  if (!links.length) return "";
  return `
    <section class="role-group">
      <div class="role-heading">
        <span>${escapeHtml(state.lang === "ko" ? "Collab 전송" : "Collab Transport")}</span>
        ${pill(String(links.length), links.some((link) => link.status === "unbound" || link.status === "transport_role_differs") ? "warn" : "ok")}
      </div>
      <div class="machine-list">
        ${links.map(renderCollabLink).join("")}
      </div>
    </section>
  `;
}

function renderCollabLink(link) {
  const statusTone = link.status === "unbound" || link.status === "transport_role_differs"
    ? "warn"
    : link.status === "binding_role_only"
      ? "info"
      : "ok";
  const statusText = link.status === "bound"
    ? (state.lang === "ko" ? "binding 정렬됨" : "binding aligned")
    : link.status === "machine_role_bound"
      ? (state.lang === "ko" ? "machine-role 정렬됨" : "machine-role aligned")
      : link.status === "binding_role_only"
        ? (state.lang === "ko" ? "binding 역할 기준" : "binding role source")
        : link.status === "transport_role_differs"
          ? (state.lang === "ko" ? "transport 역할 확인" : "check transport role")
      : localizedStatus(link.status || "unknown");
  const bindingRole = link.peer_binding_role || "";
  const transportRole = link.peer_role || "";
  return `
    <div class="machine-row">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(link.peer_machine_id || link.peer_host || "-")}</strong>
          <span class="subtle">${escapeHtml(link.host || "-")} -> ${escapeHtml(link.peer_host || "-")}</span>
        </div>
        ${pill(statusText, statusTone)}
      </div>
      <div class="token-row">
        ${token(`${state.lang === "ko" ? "binding 역할" : "binding role"} ${bindingRole ? roleValue(bindingRole) : "-"}`)}
        ${token(`${state.lang === "ko" ? "transport 역할" : "transport role"} ${transportRole ? roleValue(transportRole) : roleValue("unassigned")}`)}
        ${token(`${state.lang === "ko" ? "역할 기준" : "role source"} ${localizedStatus(link.status || "-")}`)}
        ${token(`${state.lang === "ko" ? "연결" : "link"} ${localizedStatus(link.peer_status || "-")}`)}
        ${token(`${state.lang === "ko" ? "세션" : "session"} ${link.peer_session_id || "-"}`)}
        ${token(`${state.lang === "ko" ? "경과" : "age"} ${formatAge(link.peer_age_sec)}`)}
      </div>
    </div>
  `;
}

function versioningValue(versioning, key, fallback = undefined) {
  const summary = versioning?.summary || {};
  return versioning?.[key] ?? summary[key] ?? fallback;
}

function versioningDirtyCount(versioning) {
  const value = Number(versioningValue(versioning, "dirty_repo_count", 0));
  return Number.isFinite(value) ? value : 0;
}

function versioningBoolLabel(versioning, key) {
  const value = versioningValue(versioning, key, null);
  if (value === null || value === undefined || value === "") return "-";
  return value ? localizedWord("ready") : localizedWord("review");
}

function versioningRecoverySource(versioning) {
  const authority = versioning?.version_authority || {};
  return (
    versioningValue(versioning, "reproducibility_source", "") ||
    versioningValue(versioning, "version_authority_reproducibility_boundary", "") ||
    authority.reproducibility_boundary ||
    "-"
  );
}

function versioningPublicationGate(versioning) {
  const boundary = versioning?.version_authority?.publication_boundary || {};
  if (boundary.clean_publication_ready !== undefined) {
    return boundary.clean_publication_ready
      ? localizedStatus("clean_publication_ready")
      : localizedStatus(boundary.status || "publication_review_required");
  }
  const dirtyCount = versioningDirtyCount(versioning);
  return versioning?.routine_publish_ready && dirtyCount === 0
    ? localizedWord("ready")
    : localizedWord("review");
}

function renderProjectDetail() {
  const project = selectedProject();
  const session = sessionProject(state.selectedProject);
  const roleCounts = session?.machine_role_counts || {};
  const display = projectDisplay(project);
  $("selectedProjectTitle").textContent = project?.display_name || state.selectedProject || "-";
  $("selectedProjectBadge").textContent = display.label;
  $("selectedProjectBadge").className = `pill ${display.tone}`;
  if (!project) {
    $("projectDetail").innerHTML = emptyCard(t("empty.noProjectSelected"));
    return;
  }
  const sync = project.sync_summary || {};
  const versioning = project.versioning_readiness || {};
  const integration = integrationDisplay(project);
  const backup = project.online_backup || {};
  const cycles = project.away_cycles || {};
  const dataHandling = project.data_handling || {};
  const freshness = project.project_snapshot_freshness || {};
  const snapshotStorage = project.snapshot_storage || {};
  const authority = versioning.version_authority || {};
  $("projectDetail").innerHTML = [
    detailCard(t("label.integration"), [
      `${state.lang === "ko" ? "모드" : "mode"} ${integration.label}`,
      `${t("field.status")} ${integration.statusLabel || "-"}`,
      `${state.lang === "ko" ? "기준 머신" : "canonical"} ${integration.canonicalMachine || "-"}`,
    ]),
    detailCard(t("label.sync"), [
      `${state.lang === "ko" ? "필수 repo" : "required repos"} ${sync.required_sync_ready_count ?? 0}/${sync.required_repo_count ?? 0}`,
      `${localizedStatus("blocked")} ${sync.required_blocked_count ?? 0}`,
      `${localizedStatus("available")} ${sync.required_available_count ?? 0}`,
    ]),
    detailCard(t("label.versioning"), [
      `${state.lang === "ko" ? "publisher" : "publisher"} ${versioning.local_machine_is_online_publisher ? localizedWord("yes") : localizedWord("no")}`,
      `${t("label.publicationGate")} ${versioningPublicationGate(versioning)}`,
      `${state.lang === "ko" ? "일상 publish" : "routine"} ${versioning.routine_publish_ready ? localizedWord("ready") : localizedWord("review")}`,
      `${t("label.dirtyWip")} ${versioningDirtyCount(versioning)}`,
      `${state.lang === "ko" ? "재현성" : "repro"} ${versioning.reproducibility_ready ? localizedWord("ready") : localizedWord("review")}`,
      `${t("field.warnings")} ${versioning.warning_finding_count ?? 0}`,
    ]),
    detailCard(t("label.dataHandling"), [
      `${state.lang === "ko" ? "정책" : "policy"} ${dataHandling.artifact_pointer_policy_mode || "-"}`,
      `${state.lang === "ko" ? "상태" : "status"} ${localizedStatus(dataHandling.status || "-")}`,
      `${state.lang === "ko" ? "경계" : "boundary"} ${dataHandling.reproducibility_boundary || "-"}`,
      `${state.lang === "ko" ? "handoff" : "handoff"} ${dataHandling.requires_artifact_pointer_before_handoff ? localizedWord("review") : localizedWord("ready")}`,
      `${t("label.artifactPointers")} ${dataHandling.artifact_pointer_count ?? project.latest_artifact_pointer_count ?? 0}`,
      `${state.lang === "ko" ? "노트" : "note"} ${dataHandling.recommended_note_name || "-"}`,
    ]),
    renderDataLocationsCard(dataHandling),
    detailCard(t("label.recoveryEvidence"), [
      `${state.lang === "ko" ? "권위" : "authority"} ${localizedStatus(versioning.version_authority_status || authority.operator_status || "-")}`,
      `${state.lang === "ko" ? "복구 경계" : "restore boundary"} ${versioning.version_authority_reproducibility_boundary || authority.reproducibility_boundary || "-"}`,
      `${t("label.recoveryCoverage")} ${versioningBoolLabel(versioning, "reproducibility_ready")}`,
      `${t("label.localSnapshotCoverage")} ${versioningBoolLabel(versioning, "local_snapshot_reproducibility_ready")}`,
      `${t("label.metadataCoverage")} ${versioningBoolLabel(versioning, "metadata_reproducibility_ready")}`,
      `${t("label.localSnapshotFreshness")} ${localizedStatus(freshness.status || "-")}`,
      `${state.lang === "ko" ? "저장 상태" : "storage"} ${localizedStatus(snapshotStorage.status || "-")}`,
      `${t("label.promotedMetadata")} ${project.valid_snapshot_metadata_ref_count ?? 0}/${project.snapshot_metadata_ref_count ?? 0}`,
      `${t("label.artifactPointers")} ${project.latest_artifact_pointer_count ?? snapshotStorage.latest_artifact_pointer_count ?? 0}`,
    ]),
    renderMetadataRefsCard(project, versioning, snapshotStorage),
    detailCard(t("label.backups"), [
      `${state.lang === "ko" ? "활성" : "enabled"} ${backup.enabled_count ?? 0}/${backup.repo_count ?? 0}`,
      `${t("label.localSnapshotManifests")} ${project.project_snapshot_count ?? 0}`,
      `${t("label.promotedMetadata")} ${project.valid_snapshot_metadata_ref_count ?? 0}/${project.snapshot_metadata_ref_count ?? 0}`,
      `${t("label.artifactPointers")} ${project.latest_artifact_pointer_count ?? project.snapshot_storage?.latest_artifact_pointer_count ?? 0}`,
    ]),
    detailCard(t("label.away"), [
      `${state.lang === "ko" ? "계획" : "plan"} ${project.away_plan?.present ? t("word.present") : t("word.none")}`,
      `${t("field.cycles")} ${cycles.valid_cycle_count ?? 0}`,
      `soak ${cycles.soak_validation_level || "-"}`,
    ]),
    detailCard(t("label.pcRoles"), [
      `${roleLabel("main")} ${roleCounts.main ?? project.bindings?.main_count ?? 0}`,
      `${roleLabel("worker")} ${roleCounts.worker ?? project.bindings?.worker_count ?? 0}`,
      `${roleLabel("observer")} ${roleCounts.observer ?? project.bindings?.observer_count ?? 0}`,
      `${state.lang === "ko" ? "활성 세션" : "active sessions"} ${session?.binding_count ?? 0}`,
    ]),
    detailCard(t("label.latest"), [
      `${state.lang === "ko" ? "백업" : "backup"} ${project.latest_backup_snapshot || "-"}`,
      `${state.lang === "ko" ? "로컬 manifest" : "local manifest"} ${project.latest_project_snapshot || "-"}`,
      `${t("label.promotedMetadata")} ${project.latest_snapshot_metadata_ref?.commit_short || "-"}`,
    ]),
  ].join("");
}

function renderMetadataRefsCard(project, versioning, snapshotStorage) {
  const latest = project.latest_snapshot_metadata_ref || {};
  const valid = project.valid_snapshot_metadata_ref_count ?? snapshotStorage.valid_metadata_ref_count ?? 0;
  const total = project.snapshot_metadata_ref_count ?? snapshotStorage.metadata_ref_count ?? 0;
  return detailCard(t("label.metadataRefs"), [
    `${state.lang === "ko" ? "coverage" : "coverage"} ${valid}/${total}`,
    `${t("label.latestMetadata")} ${latest.commit_short || "-"}`,
    `${state.lang === "ko" ? "branch" : "branch"} ${latest.branch || "-"}`,
    `${t("field.status")} ${localizedStatus(latest.status || "-")}`,
    `${state.lang === "ko" ? "snapshot" : "snapshot"} ${latest.snapshot_id || "-"}`,
    `${state.lang === "ko" ? "복구 source" : "repro source"} ${versioningRecoverySource(versioning)}`,
    `${state.lang === "ko" ? "저장 상태" : "storage"} ${localizedStatus(snapshotStorage.status || "-")}`,
    `${state.lang === "ko" ? "local manifests" : "local manifests"} ${snapshotStorage.local_snapshot_count ?? project.project_snapshot_count ?? 0}`,
  ]);
}

function renderDataLocationsCard(dataHandling) {
  const pathValue = (path, exists) => ({
    path,
    status: exists === true ? "available" : exists === false ? "missing" : "",
  });
  const workspaceRecords = Array.isArray(dataHandling.local_workspace_records) && dataHandling.local_workspace_records.length
    ? dataHandling.local_workspace_records.map((item) => pathValue(item.path, item.exists))
    : (dataHandling.local_workspaces || []).map((path) => pathValue(path, undefined));
  const rows = [
    { label: t("label.dataNote"), values: [pathValue(dataHandling.recommended_note_path, dataHandling.recommended_note_exists)] },
    { label: t("label.artifactManifest"), values: [pathValue(dataHandling.recommended_artifact_manifest_path, dataHandling.recommended_artifact_manifest_exists)] },
    { label: t("label.localWorkspaces"), values: workspaceRecords },
  ]
    .map((row) => ({
      label: row.label,
      values: (row.values || []).filter((value) => {
        const path = typeof value === "object" ? value.path : value;
        return path !== null && path !== undefined && String(path).trim();
      }),
    }))
    .filter((row) => row.values.length);
  if (!rows.length) return "";
  return `
    <article class="detail-card detail-path-card">
      <div class="small-label">${escapeHtml(t("label.dataLocations"))}</div>
      <div class="path-list">
        ${rows.map((row) => `
          <div class="path-row">
            <span>${escapeHtml(row.label)}</span>
            ${row.values.map((value) => {
              const path = typeof value === "object" ? value.path : value;
              const status = typeof value === "object" ? value.status : "";
              return `
                <div class="path-entry">
                  <code>${escapeHtml(String(path))}</code>
                  ${status ? `<span class="path-status ${escapeHtml(status)}">${escapeHtml(localizedStatus(status))}</span>` : ""}
                </div>
              `;
            }).join("")}
          </div>
        `).join("")}
      </div>
    </article>
  `;
}

function renderBackupsView() {
  const projects = state.overview?.projects?.items || [];
  const freshCount = projects.filter(
    (project) => project.project_snapshot_freshness?.status === "fresh",
  ).length;
  $("backupsSummaryBadge").textContent = `${freshCount}/${projects.length} ${state.lang === "ko" ? "manifest fresh" : "manifest fresh"}`;
  $("backupsSummaryBadge").className = `pill ${freshCount === projects.length ? "ok" : "warn"}`;
  $("backupProjectList").innerHTML =
    projects.map(renderBackupProjectItem).join("") || emptyCard(t("empty.noProjects"));
}

function renderBackupProjectItem(project) {
  const backup = project.online_backup || {};
  const freshness = project.project_snapshot_freshness || {};
  const display = backupDisplay(project);
  return `
    <article class="item-card project-card ${project.project_id === state.selectedProject ? "selected" : ""}">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(project.display_name || project.project_id)}</strong>
          <span class="subtle">${escapeHtml(project.workspace_path || "-")}</span>
        </div>
        <div class="item-actions">
          ${pill(display.label, display.tone)}
          <button class="button mini" type="button" data-select-project="${escapeHtml(project.project_id)}">${escapeHtml(t("action.open"))}</button>
        </div>
      </div>
      <div class="token-row">
        ${integrationToken(project)}
        ${token(`online ${backup.enabled_count ?? 0}/${backup.repo_count ?? 0}`)}
        ${token(`${state.lang === "ko" ? "승인" : "approval"} ${backup.approval_required_count ?? 0}`)}
        ${token(`${t("label.localBackups")} ${project.backup_snapshot_count ?? 0}`)}
        ${token(`${t("label.localSnapshotManifests")} ${project.project_snapshot_count ?? 0}`)}
        ${token(`${t("label.promotedMetadata")} ${project.valid_snapshot_metadata_ref_count ?? 0}/${project.snapshot_metadata_ref_count ?? 0}`)}
        ${token(`${t("label.dataHandling")} ${localizedStatus(project.data_handling?.status || "-")}`)}
        ${token(`${t("label.artifactPointers")} ${project.latest_artifact_pointer_count ?? project.snapshot_storage?.latest_artifact_pointer_count ?? 0}`)}
        ${token(`${state.lang === "ko" ? "manifest 상태" : "manifest state"} ${localizedStatus(freshness.status || "-")}`)}
        ${token(`${state.lang === "ko" ? "manifest 경과" : "manifest age"} ${formatHours(freshness.latest_age_hours)}`)}
      </div>
      <div class="detail-strip">
        <div>
          <div class="small-label">${escapeHtml(t("label.latestBackup"))}</div>
          <div class="subtle">${escapeHtml(project.latest_backup_snapshot || "-")}</div>
        </div>
        <div>
          <div class="small-label">${escapeHtml(t("label.latestSnapshot"))}</div>
          <div class="subtle">${escapeHtml(project.latest_project_snapshot || "-")}</div>
        </div>
        <div>
          <div class="small-label">${escapeHtml(t("label.latestMetadata"))}</div>
          <div class="subtle">${escapeHtml(project.latest_snapshot_metadata_ref?.commit_short || "-")}</div>
        </div>
      </div>
      ${renderBackupRecoveryEvidence(project)}
    </article>
  `;
}

function renderBackupRecoveryEvidence(project) {
  const versioning = project.versioning_readiness || {};
  const authority = versioning.version_authority || {};
  const freshness = project.project_snapshot_freshness || {};
  const snapshotStorage = project.snapshot_storage || {};
  const dataHandling = project.data_handling || {};
  const fileStatus = (exists) => {
    if (exists === true) return localizedStatus("available");
    if (exists === false) return localizedStatus("missing");
    return "-";
  };
  const rows = [
    {
      label: state.lang === "ko" ? "권위" : "Authority",
      value: localizedStatus(versioning.version_authority_status || authority.operator_status || "-"),
    },
    {
      label: t("label.publicationGate"),
      value: versioningPublicationGate(versioning),
    },
    {
      label: t("label.dirtyWip"),
      value: String(versioningDirtyCount(versioning)),
    },
    {
      label: state.lang === "ko" ? "복구 경계" : "Restore boundary",
      value: versioning.version_authority_reproducibility_boundary || authority.reproducibility_boundary || "-",
    },
    {
      label: t("label.recoveryCoverage"),
      value: versioningBoolLabel(versioning, "reproducibility_ready"),
    },
    {
      label: t("label.localSnapshotFreshness"),
      value: localizedStatus(freshness.status || "-"),
    },
    {
      label: state.lang === "ko" ? "저장 상태" : "Storage",
      value: localizedStatus(snapshotStorage.status || "-"),
    },
    {
      label: t("label.dataNote"),
      value: fileStatus(dataHandling.recommended_note_exists),
    },
    {
      label: t("label.artifactManifest"),
      value: fileStatus(dataHandling.recommended_artifact_manifest_exists),
    },
  ];
  return `
    <div class="backup-evidence" aria-label="${escapeHtml(t("label.recoveryEvidence"))}">
      ${rows.map((row) => `
        <div class="backup-evidence-item">
          <span>${escapeHtml(row.label)}</span>
          <strong>${escapeHtml(row.value)}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function backupDisplay(project) {
  const backup = project.online_backup || {};
  const freshness = project.project_snapshot_freshness || {};
  const metadataCount = Number(project.snapshot_metadata_ref_count || 0);
  const validMetadataCount = Number(project.valid_snapshot_metadata_ref_count || 0);
  if (Number(backup.approval_required_count || 0) > 0) {
    return { label: localizedStatus("approval"), tone: "warn" };
  }
  if (Number(backup.enabled_count || 0) < Number(backup.repo_count || 0)) {
    return { label: localizedStatus("review"), tone: "warn" };
  }
  if (metadataCount > 0 && validMetadataCount < metadataCount) {
    return { label: localizedStatus("metadata"), tone: "warn" };
  }
  if ((project.snapshot_storage?.status || "") === "metadata_only") {
    return { label: localizedStatus("metadata_only"), tone: "info" };
  }
  if (freshness.status && freshness.status !== "fresh") {
    return { label: localizedStatus(freshness.status), tone: "warn" };
  }
  return { label: localizedStatus("fresh"), tone: "ok" };
}

function formatHours(hours) {
  if (hours === null || hours === undefined || Number.isNaN(Number(hours))) return "-";
  const value = Number(hours);
  if (value < 1) return `${Math.round(value * 60)}m`;
  if (value < 24) return `${Math.round(value)}h`;
  return `${Math.round(value / 24)}d`;
}

function renderMachinesView() {
  const overview = state.overview || {};
  const lifecycle = overview.machine_lifecycle || {};
  const workers = overview.workers || {};
  const workerItems = workers.items || [];
  const repos = Object.entries(lifecycle.repos || {});
  const lifecycleDisplay = lifecycleState(lifecycle);
  const availableWorkers = Number(workers.available_count || 0);
  const workerCount = Number(workers.worker_count || workerItems.length || 0);
  const healthyRepos = repos.filter(([, repo]) => repoDisplay(repo).key === "ready").length;

  $("machineViewTitle").textContent = overview.machine_display_name
    ? `${overview.machine_display_name} / ${overview.machine_id || "-"}`
    : overview.machine_id || "-";
  $("machineViewBadge").textContent = lifecycleDisplay.label;
  $("machineViewBadge").className = `pill ${lifecycleDisplay.tone}`;

  $("machineLifecycleGrid").innerHTML = [
    detailCard(t("label.currentMachine"), [
      `id ${overview.machine_id || "-"}`,
      `${t("field.thread")} ${overview.thread_id || "-"}`,
      `runtime ${lifecycle.runtime_ready ? localizedWord("ready") : localizedWord("review")}`,
    ]),
    detailCard(t("label.lifecycle"), [
      `install ${lifecycle.install_ready ? localizedWord("ready") : localizedWord("review")}`,
      `session entry ${lifecycle.session_entry_ready ? localizedWord("ready") : localizedWord("review")}`,
      `reconnect ${lifecycle.reconnect_ready ? localizedWord("ready") : localizedWord("review")}`,
    ]),
    detailCard(t("label.onlineSync"), [
      `${state.lang === "ko" ? "준비" : "ready"} ${boolText(lifecycle.online_sync_ready)}`,
      `${state.lang === "ko" ? "오류" : "errors"} ${lifecycle.error_count ?? 0}`,
      `${t("field.warnings")} ${lifecycle.warning_count ?? 0}`,
    ]),
    detailCard(t("label.agentEntry"), [
      `scope ${localizedStatus(lifecycle.agent_guidance_scope?.status || "-")}`,
      `managed ${boolText(lifecycle.agent_guidance_scope?.managed_block_present)}`,
      `hook ${lifecycle.agent_guidance_scope?.session_entry_present ? "ok" : "no"}`,
    ]),
  ].join("");

  $("machineWorkersBadge").textContent = `${availableWorkers}/${workerCount} ${localizedStatus("available")}`;
  $("machineWorkersBadge").className = `pill ${availableWorkers === workerCount ? "ok" : "warn"}`;
  $("machineWorkersList").innerHTML =
    workerItems.map(renderMachineWorkerItem).join("") || emptyCard(t("empty.noWorkers"));

  $("machineReposBadge").textContent = `${healthyRepos}/${repos.length} ${localizedStatus("ready")}`;
  $("machineReposBadge").className = `pill ${healthyRepos === repos.length ? "ok" : "warn"}`;
  $("machineRepoList").innerHTML = repos.map(renderRepoItem).join("") || emptyCard(t("empty.noRepos"));
}

function lifecycleState(lifecycle) {
  if (!lifecycle || !lifecycle.ok || Number(lifecycle.error_count || 0) > 0) {
    return { key: "review", label: localizedStatus("review"), tone: "warn" };
  }
  if (
    !lifecycle.install_ready ||
    !lifecycle.runtime_ready ||
    !lifecycle.session_entry_ready ||
    !lifecycle.online_sync_ready ||
    !lifecycle.reconnect_ready ||
    Number(lifecycle.warning_count || 0) > 0
  ) {
    return { key: "review", label: localizedStatus("review"), tone: "warn" };
  }
  return { key: "ready", label: localizedStatus("ready"), tone: "ok" };
}

function repoDisplay(repo) {
  if (!repo?.ok) return { key: "review", label: localizedStatus("review"), tone: "warn" };
  if (repo.dirty || repo.clean === false) return { key: "dirty", label: localizedStatus("dirty"), tone: "warn" };
  if (repo.remote_head_matches_local === false) return { key: "review", label: localizedStatus("review"), tone: "warn" };
  return { key: "ready", label: localizedStatus("ready"), tone: "ok" };
}

function renderRepoItem([repoName, repo]) {
  const display = repoDisplay(repo);
  return `
    <article class="item-card">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(repoName)}</strong>
          <span class="subtle">${escapeHtml(repo.sync_source || "-")}</span>
        </div>
        ${pill(display.label, display.tone)}
      </div>
      <div class="token-row">
        ${token(`head ${repo.head_short || "-"}`)}
        ${token(`remote ${repo.remote_head_short || "-"}`)}
        ${token(`${state.lang === "ko" ? "clean" : "clean"} ${boolText(repo.clean)}`)}
        ${token(`${state.lang === "ko" ? "remote 일치" : "remote match"} ${boolText(repo.remote_head_matches_local)}`)}
        ${token(`LAN mirror ${repo.lan_mirror_matches_local ? t("word.match") : t("word.warning")}`)}
      </div>
    </article>
  `;
}

function renderMachineWorkerItem(worker, monitorContext = null) {
  const tone = workerTone(worker);
  const result = worker.last_peer_result || {};
  const peer = worker.peer || {};
  const health = worker.health || {};
  const peerHost = worker.peer_host || peer.host || health.peer_host || "-";
  const stateStatus = worker.state_status || health.state_status || "-";
  const peerStatus = worker.peer_status || health.peer_status || "-";
  const stateAge = worker.state_age_sec ?? health.state_age_sec;
  const peerAge = worker.peer_age_sec ?? health.peer_age_sec;
  const projectRole = monitorContext?.binding_role || worker.binding_role || "";
  const runtimeRole = monitorContext?.transport_role || worker.role || "";
  const roleAlignment = monitorContext?.role_alignment || worker.role_alignment || "";
  const roleTokens = monitorContext
    ? [
      token(`${state.lang === "ko" ? "프로젝트 역할" : "project role"} ${roleValue(projectRole)}`),
      token(`${state.lang === "ko" ? "runtime 역할" : "runtime role"} ${roleValue(runtimeRole)}`),
      token(`${state.lang === "ko" ? "역할 기준" : "role source"} ${localizedStatus(roleAlignment || "-")}`),
    ].join("")
    : token(`${state.lang === "ko" ? "역할" : "role"} ${roleValue(worker.role)}`);
  return `
    <article class="item-card">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(worker.display_name || worker.host || "-")}</strong>
          <span class="subtle">${escapeHtml(worker.host || "-")} -> ${escapeHtml(peerHost)}</span>
        </div>
        ${pill(localizedStatus(worker.activity || worker.state_status || "unknown"), tone)}
      </div>
      <div class="token-row">
        ${roleTokens}
        ${token(`${state.lang === "ko" ? "상태" : "state"} ${localizedStatus(stateStatus)}`)}
        ${token(`${state.lang === "ko" ? "연결" : "link"} ${localizedStatus(peerStatus)}`)}
        ${token(`${state.lang === "ko" ? "대기열" : "queue"} ${worker.queue_length ?? 0}`)}
        ${token(`${state.lang === "ko" ? "상태 경과" : "state age"} ${formatAge(stateAge)}`)}
        ${token(`${state.lang === "ko" ? "연결 경과" : "link age"} ${formatAge(peerAge)}`)}
        ${token(`${state.lang === "ko" ? "마지막" : "last"} ${localizedStatus(result.result_status || "-")}`)}
      </div>
    </article>
  `;
}

function monitorStatusPayload() {
  return state.collabMonitor?.monitor_status || {};
}

function monitorOverallTone(payload) {
  if (Number(payload?.missing_count || 0) > 0) return "error";
  if (
    Number(payload?.hidden_count || 0) > 0 ||
    Number(payload?.transport_role_differs_count || 0) > 0 ||
    payload?.ok === false ||
    state.collabMonitorError
  ) return "warn";
  if (payload?.ok) return "ok";
  return "neutral";
}

function monitorVisibility(item) {
  const running = Boolean(item?.running) || item?.tmux_status === "running";
  const visible = Boolean(item?.operator_visible);
  if (!running) return { label: t("monitor.missing"), tone: "error", visible: false, running: false };
  if (visible) return { label: t("monitor.visible"), tone: "ok", visible: true, running: true };
  return { label: t("monitor.hidden"), tone: "warn", visible: false, running: true };
}

function monitorProjectLabel(payload) {
  return payload?.project_id || state.selectedProject || "-";
}

function monitorRoleSourceStatus(payload) {
  const explicit = payload?.role_context_status;
  if (explicit && explicit !== "-") return explicit;
  if (Number(payload?.transport_role_differs_count || 0) > 0) return "transport_role_differs";
  if (Number(payload?.binding_role_only_count || 0) > 0) return "binding_role_only";
  if (Number(payload?.monitor_count || 0) > 0) return "aligned";
  return "unknown";
}

function monitorRoleSourceTone(status) {
  if (status === "transport_role_differs") return "warn";
  if (status === "binding_role_only") return "info";
  if (status === "aligned" || status === "bound") return "ok";
  return "neutral";
}

function monitorRoleSourceDetail(status) {
  if (status === "transport_role_differs") return t("monitor.roleSource.differsDetail");
  if (status === "binding_role_only") return t("monitor.roleSource.bindingOnlyDetail");
  if (status === "aligned" || status === "bound") return t("monitor.roleSource.alignedDetail");
  return t("monitor.roleSource.unknownDetail");
}

function formatTimestampNs(ns) {
  if (ns === null || ns === undefined || Number.isNaN(Number(ns))) return "-";
  return new Date(Number(ns) / 1000000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function monitorSummaryCard(label, value, detail, tone = "neutral") {
  return `
    <article class="monitor-summary-card ${summaryToneClass(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(valueText(value))}</strong>
      <small>${escapeHtml(detail || "")}</small>
    </article>
  `;
}

function monitorHasTaskContext(item) {
  return Boolean(
    item?.current_task_active ||
    item?.last_request_id ||
    item?.last_result_status ||
    item?.last_result_summary ||
    Number(item?.queue_length || 0) > 0
  );
}

function monitorTaskIsPrimaryContext(item) {
  const taskStatus = item?.recent_task_status || "none";
  const taskScope = item?.recent_task_project_scope || "none";
  const active = Boolean(item?.current_task_active) || taskStatus === "active" || Number(item?.queue_length || 0) > 0;
  if (active) return true;
  if (taskScope === "selected_project") return true;
  if (taskStatus === "recent_history" || taskStatus === "history_unknown_age") return true;
  return false;
}

function renderMonitorView() {
  const badge = $("monitorBadge");
  if (!badge) return;
  const payload = monitorStatusPayload();
  const monitors = Array.isArray(payload.monitors) ? payload.monitors : [];
  const workerPayload = payload.worker_status || {};
  const workers = Array.isArray(workerPayload.workers) ? workerPayload.workers : [];
  const hasPayload = Boolean(state.collabMonitor);
  const tone = monitorOverallTone(payload);
  const judgement = state.collabMonitor?.operator_judgement || {};
  const label = hasPayload
    ? localizedMeta(judgement.label, localizedStatus(judgement.status || (payload.ok ? "complete" : "review")))
    : state.collabMonitorLoading
      ? localizedStatus("loading")
      : localizedStatus("idle");

  badge.textContent = label || "-";
  badge.className = `pill ${state.collabMonitorLoading && !hasPayload ? "neutral" : tone}`;

  if (!hasPayload) {
    $("monitorSummary").innerHTML = emptyCard(state.collabMonitorLoading ? t("monitor.loading") : t("monitor.empty"));
    $("monitorGuidanceBadge").textContent = "-";
    $("monitorGuidanceBadge").className = "pill neutral";
    $("monitorGuidanceList").innerHTML = emptyCard(t("monitor.noGuidance"));
    $("monitorHostBadge").textContent = "-";
    $("monitorHostBadge").className = "pill neutral";
    $("monitorHostList").innerHTML = emptyCard(t("monitor.empty"));
    $("monitorTaskBadge").textContent = "-";
    $("monitorTaskBadge").className = "pill neutral";
    $("monitorTaskList").innerHTML = emptyCard(t("monitor.noTasks"));
    $("monitorWorkerBadge").textContent = "-";
    $("monitorWorkerBadge").className = "pill neutral";
    $("monitorWorkerList").innerHTML = emptyCard(t("empty.noWorkers"));
    return;
  }

  const monitorCount = Number(payload.monitor_count ?? monitors.length ?? 0);
  const visibleCount = Number(payload.operator_visible_count ?? 0);
  const runningCount = Number(payload.running_count ?? 0);
  const hiddenCount = Number(payload.hidden_count ?? 0);
  const missingCount = Number(payload.missing_count ?? 0);
  const roleMismatchCount = Number(payload.transport_role_differs_count ?? 0);
  const roleSourceStatus = monitorRoleSourceStatus(payload);
  const refreshSec = Number(state.collabMonitor?.refresh_interval_sec || MONITOR_REFRESH_MS / 1000);
  const reviewCount = hiddenCount + missingCount + roleMismatchCount;
  const reviewDetail = [
    `${t("monitor.hidden")} ${hiddenCount}`,
    `${t("monitor.missing")} ${missingCount}`,
    roleMismatchCount ? `${t("monitor.roleMismatch")} ${roleMismatchCount}` : "",
  ].filter(Boolean).join(" / ");
  $("monitorSummary").innerHTML = [
    monitorSummaryCard(t("label.project"), monitorProjectLabel(payload), state.lang === "ko" ? "선택된 project 기준" : "selected project scope", "info"),
    monitorSummaryCard(t("label.visibility"), `${visibleCount}/${monitorCount}`, `${t("status.running")} ${runningCount}/${monitorCount}`, tone),
    monitorSummaryCard(localizedStatus("review"), reviewCount, reviewDetail, reviewCount ? "warn" : "ok"),
    monitorSummaryCard(state.lang === "ko" ? "역할 기준" : "Role Source", localizedStatus(roleSourceStatus), monitorRoleSourceDetail(roleSourceStatus), monitorRoleSourceTone(roleSourceStatus)),
    monitorSummaryCard(t("monitor.lastUpdated"), formatTimestampNs(state.collabMonitor.generated_at_ns), `${t("monitor.auto")} ${refreshSec}s`, "neutral"),
  ].join("");

  renderMonitorGuidance();

  const monitorByHost = new Map(monitors.map((item) => [item.host || "", item]));
  $("monitorHostBadge").textContent = `${visibleCount}/${monitorCount} ${t("monitor.visible")}`;
  $("monitorHostBadge").className = `pill ${tone}`;
  $("monitorHostList").innerHTML = monitors.length
    ? monitors.map((item) => renderMonitorHostCard(item, monitorByHost.get(item.peer_host || ""))).join("")
    : emptyCard(t("monitor.empty"));

  const taskContextMonitors = monitors.filter(monitorHasTaskContext);
  const taskMonitors = taskContextMonitors.filter(monitorTaskIsPrimaryContext);
  const activeTaskCount = Number(payload.active_task_count ?? taskContextMonitors.filter((item) => item.recent_task_status === "active" || item.current_task_active || Number(item.queue_length || 0) > 0).length);
  const taskHistoryCount = Number(payload.task_history_count ?? Math.max(taskContextMonitors.length - activeTaskCount, 0));
  const selectedTaskCount = Number(payload.selected_project_task_count ?? taskContextMonitors.filter((item) => item.recent_task_project_scope === "selected_project").length);
  const otherHistoryCount = Number(payload.other_project_history_count ?? taskContextMonitors.filter((item) => item.recent_task_project_scope === "different_project").length);
  const staleTaskCount = Number(payload.stale_task_history_count ?? taskContextMonitors.filter((item) => item.recent_task_status === "stale_history").length);
  const taskBadgeDetail = activeTaskCount
    ? `${t("monitor.taskActive")} ${activeTaskCount} / ${t("monitor.taskHistory")} ${taskHistoryCount}${staleTaskCount ? ` / ${t("monitor.taskStale")} ${staleTaskCount}` : ""}`
    : selectedTaskCount
      ? `${t("monitor.taskSelected")} ${selectedTaskCount} / ${t("monitor.taskHistory")} ${taskHistoryCount}${staleTaskCount ? ` / ${t("monitor.taskStale")} ${staleTaskCount}` : ""}`
      : otherHistoryCount
        ? `${t("monitor.taskScope.different")} ${otherHistoryCount}${staleTaskCount ? ` / ${t("monitor.taskStale")} ${staleTaskCount}` : ""}`
        : `${t("monitor.taskHistory")} ${taskHistoryCount}${staleTaskCount ? ` / ${t("monitor.taskStale")} ${staleTaskCount}` : ""}`;
  $("monitorTaskBadge").textContent = taskMonitors.length
    ? taskBadgeDetail
    : "0";
  $("monitorTaskBadge").className = `pill ${activeTaskCount ? "info" : selectedTaskCount ? "info" : otherHistoryCount ? "neutral" : "neutral"}`;
  $("monitorTaskList").innerHTML = taskMonitors.length
    ? taskMonitors.map(renderMonitorTaskCard).join("")
    : emptyCard(otherHistoryCount ? t("monitor.taskOnlyOtherHistory") : t("monitor.noTasks"));

  const available = Number(workerPayload.available_count ?? workers.filter((worker) => worker.activity === "available").length);
  const workerCount = Number(workerPayload.worker_count ?? workers.length);
  $("monitorWorkerBadge").textContent = `${available}/${workerCount} ${localizedStatus("available")}`;
  $("monitorWorkerBadge").className = `pill ${workerCount && available === workerCount ? "ok" : workers.length ? "warn" : "neutral"}`;
  $("monitorWorkerList").innerHTML =
    workers.map((worker) => renderMachineWorkerItem(worker, monitorByHost.get(worker.host || ""))).join("")
    || emptyCard(t("empty.noWorkers"));
}

function monitorGuidanceBlocks() {
  const blocks = Array.isArray(state.collabMonitor?.summary_blocks) ? state.collabMonitor.summary_blocks : [];
  return blocks.filter((block) => block?.kind === "next_actions");
}

function renderMonitorGuidance() {
  const blocks = monitorGuidanceBlocks();
  const actions = blocks.flatMap((block) => Array.isArray(block.actions) ? block.actions : []);
  const warningCount = actions.filter((action) => summaryToneClass(action?.tone) === "warn").length;
  const errorCount = actions.filter((action) => summaryToneClass(action?.tone) === "error").length;
  $("monitorGuidanceBadge").textContent = state.lang === "ko"
    ? `${actions.length}개 안내`
    : `${actions.length} guidance`;
  $("monitorGuidanceBadge").className = `pill ${errorCount ? "error" : warningCount ? "warn" : actions.length ? "ok" : "neutral"}`;
  $("monitorGuidanceList").innerHTML = blocks.length
    ? blocks.map(renderMonitorGuidanceBlock).join("")
    : emptyCard(t("monitor.noGuidance"));
}

function renderMonitorGuidanceBlock(block) {
  const actions = Array.isArray(block.actions) ? block.actions : [];
  const tone = summaryToneClass(block.tone);
  const summary = uiText(block.summary);
  return `
    <article class="monitor-guidance-card ${tone}">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(uiText(block.title) || t("heading.monitorGuidance"))}</strong>
          ${summary ? `<span class="subtle">${escapeHtml(summary)}</span>` : ""}
        </div>
        ${pill(localizedStatus(tone === "ok" ? "complete" : tone === "error" ? "blocked" : tone === "warn" ? "review" : "observe"), tone)}
      </div>
      <div class="monitor-guidance-actions">
        ${actions.length ? actions.map(renderMonitorGuidanceAction).join("") : `<span class="subtle">${escapeHtml(t("monitor.noGuidance"))}</span>`}
      </div>
    </article>
  `;
}

function renderMonitorGuidanceAction(action) {
  const tone = summaryToneClass(action?.tone || "info");
  const title = uiText(action?.title) || "-";
  const detail = uiText(action?.detail);
  const meta = Array.isArray(action?.meta) ? action.meta.filter(Boolean) : [];
  const commandLike = detail && (
    meta.includes("operator step") ||
    detail.startsWith("tmux ") ||
    detail.startsWith("ssh ") ||
    detail.startsWith("bash ") ||
    detail.startsWith("python3 ")
  );
  return `
    <div class="monitor-guidance-action ${tone}">
      <strong>${escapeHtml(title)}</strong>
      ${detail ? (
        commandLike
          ? `<code>${escapeHtml(detail)}</code>`
          : `<span class="subtle">${escapeHtml(detail)}</span>`
      ) : ""}
      ${meta.length ? `<div class="token-row">${meta.map(token).join("")}</div>` : ""}
    </div>
  `;
}

function renderMonitorHostCard(item, peerContext = null) {
  const visibility = monitorVisibility(item);
  const command = visibility.visible
    ? ""
    : visibility.running
      ? item.attach_command || ""
      : item.start_visible_command || "";
  const bindingRole = item.binding_role || "-";
  const transportRole = item.transport_role || item.role || "-";
  const peerProjectRole = peerContext?.binding_role || item.peer_binding_role || item.peer_role || "-";
  const peerRuntimeRole = peerContext?.transport_role || item.peer_role || "";
  const hostSources = Array.isArray(item.host_sources) ? item.host_sources.filter(Boolean).join(", ") : "";
  return `
    <article class="item-card monitor-card ${visibility.tone}">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(item.display_name || item.host || "-")}</strong>
          <span class="subtle">${escapeHtml(item.host || "-")} / ${escapeHtml(roleValue(bindingRole))} -> ${escapeHtml(item.peer_host || "-")} / ${escapeHtml(roleValue(peerProjectRole))}</span>
        </div>
        ${pill(visibility.label, visibility.tone)}
      </div>
      <div class="token-row">
        ${token(`${state.lang === "ko" ? "binding" : "binding"} ${roleValue(bindingRole)}`)}
        ${token(`${state.lang === "ko" ? "transport" : "transport"} ${roleValue(transportRole)}`)}
        ${peerRuntimeRole && peerRuntimeRole !== peerProjectRole ? token(`${state.lang === "ko" ? "peer transport" : "peer transport"} ${roleValue(peerRuntimeRole)}`) : ""}
        ${token(`${state.lang === "ko" ? "역할 기준" : "role source"} ${localizedStatus(item.role_alignment || "-")}`)}
        ${hostSources ? token(`${state.lang === "ko" ? "대상 근거" : "target source"} ${hostSources}`) : ""}
        ${token(`${state.lang === "ko" ? "세션" : "session"} ${item.session_name || "-"}`)}
        ${token(`tmux ${item.tmux_status || "-"}`)}
        ${token(`${state.lang === "ko" ? "clients" : "clients"} ${item.attached_client_count ?? 0}`)}
        ${token(`${state.lang === "ko" ? "heartbeat" : "heartbeat"} ${localizedStatus(item.heartbeat_status || "-")}`)}
        ${token(`${state.lang === "ko" ? "연결" : "peer"} ${localizedStatus(item.peer_status || "-")}`)}
        ${token(`${state.lang === "ko" ? "대기열" : "queue"} ${item.queue_length ?? 0}`)}
      </div>
      ${renderMonitorHostNote(item, visibility, command)}
    </article>
  `;
}

function renderMonitorHostNote(item, visibility, command) {
  if (command) {
    return renderMonitorCommandHint(command);
  }
  if (visibility.visible && item.role_alignment === "binding_role_only") {
    return `<span class="subtle">${escapeHtml(t("monitor.bindingRoleSource"))}</span>`;
  }
  return `<span class="subtle">${escapeHtml(t("monitor.noRepair"))}</span>`;
}

function monitorTaskPresentation(item) {
  const taskStatus = item?.recent_task_status || "none";
  const taskScope = item?.recent_task_project_scope || "none";
  const active = Boolean(item?.current_task_active) || taskStatus === "active" || Number(item?.queue_length || 0) > 0;
  if (active) {
    return { tone: "info", label: localizedStatus("running"), note: t("monitor.taskNote.active") };
  }
  if (taskScope === "different_project" && taskStatus === "stale_history") {
    return { tone: "neutral", label: t("monitor.taskStatus.stale_history"), note: t("monitor.taskNote.staleOtherProject") };
  }
  if (taskScope === "different_project") {
    return { tone: "neutral", label: t("monitor.taskScope.different"), note: t("monitor.taskNote.otherProjectHistory") };
  }
  if (taskStatus === "stale_history") {
    return { tone: "neutral", label: t("monitor.taskStatus.stale_history"), note: t("monitor.taskNote.staleHistory") };
  }
  if (taskScope === "selected_project") {
    return { tone: "info", label: t("monitor.taskScope.selected"), note: t("monitor.taskNote.selectedHistory") };
  }
  if (taskStatus === "recent_history" || item?.last_result_status || item?.last_result_summary) {
    return { tone: "neutral", label: t("monitor.taskStatus.recent_history"), note: t("monitor.taskNote.recentHistory") };
  }
  return { tone: "neutral", label: localizedStatus("idle"), note: "" };
}

function renderMonitorTaskCard(item) {
  const projectCandidates = Array.isArray(item.project_candidates) ? item.project_candidates.filter(Boolean) : [];
  const recentProject = item.recent_task_project_id || "";
  const bindingRole = item.binding_role || "-";
  const transportRole = item.transport_role || item.role || "-";
  const taskPresentation = monitorTaskPresentation(item);
  const taskScope = item.recent_task_project_scope || "none";
  const taskScopeLabel = taskScope === "different_project"
    ? t("monitor.taskScope.different")
    : taskScope === "selected_project"
      ? t("monitor.taskScope.selected")
      : t("monitor.taskScope.none");
  const taskStatus = item.recent_task_status || "none";
  const taskStatusLabel = t(`monitor.taskStatus.${taskStatus}`) || taskStatus;
  const taskAge = item.recent_task_age_sec === null || item.recent_task_age_sec === undefined
    ? ""
    : `${state.lang === "ko" ? "나이" : "age"} ${Number(item.recent_task_age_sec)}s`;
  return `
    <article class="item-card monitor-card ${taskPresentation.tone}">
      <div class="item-row">
        <div class="title-stack">
          <strong>${escapeHtml(item.display_name || item.host || "-")}</strong>
          <span class="subtle">${escapeHtml(item.last_result_summary || item.last_request_id || "-")}</span>
          ${taskPresentation.note ? `<span class="subtle">${escapeHtml(taskPresentation.note)}</span>` : ""}
        </div>
        ${pill(taskPresentation.label, taskPresentation.tone)}
      </div>
      <div class="token-row">
        ${token(`${state.lang === "ko" ? "요청" : "request"} ${item.last_request_id || "-"}`)}
        ${token(`${t("field.result")} ${localizedStatus(item.last_result_status || "-")}`)}
        ${token(`${t("field.project")} ${recentProject || projectCandidates.join(", ") || item.project_id || "-"}`)}
        ${token(taskScopeLabel)}
        ${token(`${state.lang === "ko" ? "작업 상태" : "task status"} ${taskStatusLabel}`)}
        ${taskAge ? token(taskAge) : ""}
        ${token(`${state.lang === "ko" ? "프로젝트 역할" : "project role"} ${roleValue(bindingRole)}`)}
        ${token(`${state.lang === "ko" ? "runtime 역할" : "runtime role"} ${roleValue(transportRole)}`)}
      </div>
    </article>
  `;
}

function renderMonitorCommandHint(command) {
  return `
    <div class="monitor-command-hint">
      <span>${escapeHtml(state.lang === "ko" ? "사용자가 볼 수 있게 열려면" : "To make this visible")}</span>
      <code>${escapeHtml(command)}</code>
    </div>
  `;
}

function syncMonitorPolling() {
  if (state.activeView !== "monitor") {
    if (monitorRefreshTimer) {
      window.clearInterval(monitorRefreshTimer);
      monitorRefreshTimer = null;
    }
    return;
  }
  if (!monitorRefreshTimer) {
    monitorRefreshTimer = window.setInterval(() => {
      if (state.activeView === "monitor") {
        loadCollabMonitor({ silent: true }).catch(showError);
      }
    }, MONITOR_REFRESH_MS);
  }
  if (
    !state.collabMonitorLoading &&
    state.selectedProject &&
    state.collabMonitorProject !== state.selectedProject
  ) {
    loadCollabMonitor({ silent: true }).catch(showError);
  }
}

function formatAge(seconds) {
  if (seconds === null || seconds === undefined || Number.isNaN(Number(seconds))) return "-";
  const value = Number(seconds);
  if (value < 60) return `${Math.round(value)}s`;
  if (value < 3600) return `${Math.round(value / 60)}m`;
  if (value < 86400) return `${Math.round(value / 3600)}h`;
  return `${Math.round(value / 86400)}d`;
}

function selectedProject() {
  return (state.overview?.projects?.items || []).find(
    (project) => project.project_id === state.selectedProject,
  );
}

function sessionProject(projectId) {
  return (state.sessions?.projects || []).find((project) => project.project_id === projectId);
}

function detailCard(title, lines) {
  return `
    <article class="detail-card">
      <div class="small-label">${escapeHtml(title)}</div>
      <div class="token-row">
        ${lines.map(token).join("")}
      </div>
    </article>
  `;
}

function emptyCard(text) {
  return `<article class="item-card"><span class="subtle">${escapeHtml(text)}</span></article>`;
}

function renderDisplayAudit() {
  const items = buildDisplayAuditItems();
  const severe = items.filter((item) => item.severity === "error").length;
  const warnings = items.filter((item) => item.severity === "warn").length;
  const info = items.filter((item) => item.severity === "info").length;
  const summary = $("auditSummary");
  if (severe) {
    summary.textContent = state.lang === "ko"
      ? `${severe}개 차단${warnings ? ` / ${warnings}개 확인` : ""}`
      : `${severe} blocker${warnings ? ` / ${warnings} review` : ""}`;
    summary.className = "pill error";
  } else if (warnings) {
    summary.textContent = state.lang === "ko"
      ? `${warnings}개 확인${info ? ` / ${info}개 관찰` : ""}`
      : `${warnings} review${info ? ` / ${info} observe` : ""}`;
    summary.className = "pill warn";
  } else if (info) {
    summary.textContent = state.lang === "ko" ? `${info}개 관찰` : `${info} observe`;
    summary.className = "pill info";
  } else {
    summary.textContent = localizedStatus("clean");
    summary.className = "pill ok";
  }
  $("auditList").innerHTML = items.map(renderAuditItem).join("") || `
    <article class="audit-item">
      ${pill(localizedStatus("clean"), "ok")}
      <div class="title-stack">
        <strong>${escapeHtml(t("audit.cleanTitle"))}</strong>
        <span class="subtle">${escapeHtml(t("audit.cleanDetail"))}</span>
      </div>
    </article>
  `;
}

function renderAuditItem(item) {
  return `
    <article class="audit-item">
      ${pill(localizedStatus(item.label), item.severity)}
      <div class="title-stack">
        <strong>${escapeHtml(item.title)}</strong>
        <span class="subtle">${escapeHtml(item.detail)}</span>
      </div>
    </article>
  `;
}

function buildDisplayAuditItems() {
  const items = [];
  const health = state.health || {};
  const overview = state.overview || {};
  const sessions = state.sessions || {};
  const overviewProjects = overview.projects?.items || [];
  const sessionProjects = sessions.projects || [];

  const add = (severity, label, title, detail) => {
    items.push({ severity, label, title, detail });
  };

  const healthIds = new Set(health.project_ids || []);
  const overviewIds = new Set(overviewProjects.map((project) => project.project_id));
  const sessionIds = new Set(sessionProjects.map((project) => project.project_id));
  const missingFromOverview = [...healthIds].filter((id) => !overviewIds.has(id));
  const missingFromSessions = [...healthIds].filter((id) => !sessionIds.has(id));
  if (missingFromOverview.length) {
    add("error", "mismatch", t("audit.projectListMismatch"), state.lang === "ko" ? `overview에 없음: ${missingFromOverview.join(", ")}` : `Missing from overview: ${missingFromOverview.join(", ")}`);
  }
  if (missingFromSessions.length) {
    add("error", "mismatch", t("audit.sessionProjectMismatch"), state.lang === "ko" ? `sessions에 없음: ${missingFromSessions.join(", ")}` : `Missing from sessions: ${missingFromSessions.join(", ")}`);
  }

  const sessionBindingTotal = sessionProjects.reduce(
    (sum, project) => sum + Number(project.binding_count || 0),
    0,
  );
  const activeBindingCount = Number(sessions.active_binding_count ?? sessions.binding_count ?? 0);
  if (activeBindingCount !== sessionBindingTotal) {
    add(
      "error",
      "mismatch",
      t("audit.activeBindingMismatch"),
      state.lang === "ko"
        ? `Session 합계는 ${activeBindingCount}, 프로젝트 row 합계는 ${sessionBindingTotal}입니다.`
        : `Session total is ${activeBindingCount}, project rows sum to ${sessionBindingTotal}.`,
    );
  }
  if (
    health.active_binding_count !== undefined &&
    Number(health.active_binding_count || 0) !== activeBindingCount
  ) {
    add(
      "error",
      "mismatch",
      t("audit.healthSessionMismatch"),
      state.lang === "ko"
        ? `Health는 ${health.active_binding_count}, sessions는 ${activeBindingCount}로 보고합니다.`
        : `Health reports ${health.active_binding_count}, sessions report ${activeBindingCount}.`,
    );
  }
  for (const project of overviewProjects) {
    const session = sessionProjects.find((item) => item.project_id === project.project_id);
    if (!session || Number(session.binding_count || 0) === 0) continue;
    const display = projectDisplay(project);
    if (display.key !== "ready") {
      const counts = project.attention_severity_counts || {};
      add(
        display.tone,
        display.key,
        state.lang === "ko"
          ? `${project.display_name || project.project_id} 상태 확인 필요`
          : `${project.display_name || project.project_id} needs ${display.key}`,
        state.lang === "ko"
          ? `주의 항목 총 ${counts.total_count || 0}, 경고 ${counts.warning_count || 0}, 정보 ${counts.info_count || 0}, 오류 ${counts.error_count || 0}.`
          : `attention total ${counts.total_count || 0}, warn ${counts.warning_count || 0}, info ${counts.info_count || 0}, error ${counts.error_count || 0}.`,
      );
    }
  }

  for (const project of sessionProjects) {
    if (project.status === "multiple_main") {
      add("error", "conflict", state.lang === "ko" ? `${project.project_id}에 main PC가 여러 개입니다.` : `${project.project_id} has multiple main PCs`, t("audit.multipleMainDetail"));
    } else if (project.status === "no_main" && Number(project.binding_count || 0) > 0) {
      add("info", "observe", state.lang === "ko" ? `${project.project_id}에 활성 세션은 있지만 main PC가 없습니다.` : `${project.project_id} has active sessions but no main PC`, t("audit.noMainDetail"));
    }
  }

  for (const worker of state.overview?.workers?.items || []) {
    if (worker.activity !== "available" || worker.state_status !== "fresh" || worker.peer_status === "unknown") {
      add(
        worker.activity === "disabled" ? "info" : "warn",
        worker.activity || "worker",
        state.lang === "ko"
          ? `${worker.display_name || worker.host || "Worker"} 완전 사용 가능 상태가 아닙니다.`
          : `${worker.display_name || worker.host || "Worker"} is not fully available`,
        state.lang === "ko"
          ? `활동 ${localizedStatus(worker.activity || "-")}, 상태 ${localizedStatus(worker.state_status || "-")}, 연결 ${localizedStatus(worker.peer_status || "-")}.`
          : `activity ${worker.activity || "-"}, state ${worker.state_status || "-"}, link ${worker.peer_status || "-"}.`,
      );
    }
  }

  return items;
}

async function runCommand(commandKey) {
  const payload = { command_key: commandKey };
  if (commandRequiresProject(commandKey)) {
    if (!state.selectedProject) {
      setCommandState(t("label.selectedProject"), "warn");
      $("commandMeta").textContent = t("command.meta.projectRequired");
      $("commandLog").innerHTML = `<div class="command-empty">${escapeHtml(t("command.empty.projectRequired"))}</div>`;
      return;
    }
    payload.project = state.selectedProject;
  }
  if (commandKey === "machine-collab-guide") {
    payload.new_machine_id = $("newMachineInput")?.value?.trim() || "future-pc-01";
    payload.connection_mode = $("connectionModeSelect")?.value || "auto";
  }
  const details = commandDetails(commandKey);
  if (commandRequiresConfirmationClient(commandKey)) {
    const message = `${t("command.confirmStateChange")}\n\n${details.title} / ${payload.project || "-"}`;
    if (!window.confirm(message)) return;
    payload.confirm = true;
  }
  setCommandState(localizedStatus("running"), "info");
  $("commandMeta").textContent = details.title;
  $("commandScope").textContent = payload.project ? `${details.scope} / ${payload.project}` : details.scope;
  $("commandScope").className = "pill info";
  $("commandLog").innerHTML = `<div class="command-empty">${escapeHtml(t("command.runningPrefix"))} ${escapeHtml(details.title)}...</div>`;
  const result = await requestJson("/api/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  state.commandResult = result;
  const judgement = commandResultJudgement(result);
  setCommandState(judgement.label, judgement.tone);
  renderCommandLog();
}

function renderCommandLog() {
  const result = state.commandResult;
  if (!result) {
    setCommandState(localizedStatus("idle"), "neutral");
    $("commandMeta").textContent = t("command.meta.none");
    $("commandScope").textContent = "-";
    $("commandScope").className = "pill neutral";
    $("commandLog").innerHTML = `
      <div class="command-empty">${escapeHtml(t("command.empty.initial"))}</div>
    `;
    return;
  }
  const details = commandDetails(result.command_key);
  const judgement = commandResultJudgement(result);
  setCommandState(judgement.label, judgement.tone);
  $("commandMeta").textContent = `${details.title} / ${t("word.return")} ${result.returncode} / ${result.duration_sec}s`;
  $("commandScope").textContent = result.project ? `${details.scope} / ${result.project}` : details.scope;
  $("commandScope").className = `pill ${judgement.tone}`;
  $("commandLog").innerHTML = renderCommandReadableResult(result, details);
}

function valueText(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return boolText(value);
  if (Array.isArray(value)) return value.length ? value.join(", ") : "-";
  if (typeof value === "object") return uiText(value) || JSON.stringify(value);
  return String(value);
}

function uiText(value) {
  if (value === null || value === undefined || value === "") return "";
  if (typeof value === "object" && !Array.isArray(value)) {
    const lang = displayLang();
    return value[lang] || value.en || value.ko || JSON.stringify(value);
  }
  return String(value);
}

function summaryToneClass(tone) {
  const value = String(tone || "neutral");
  return ["ok", "warn", "error", "info", "neutral"].includes(value) ? value : "neutral";
}

function normalizeSummaryMetric(item) {
  if (Array.isArray(item)) {
    return {
      label: item[0],
      value: item[1],
      tone: "neutral",
    };
  }
  if (item && typeof item === "object") {
    return {
      label: item.label,
      value: item.value,
      tone: summaryToneClass(item.tone),
    };
  }
  return {
    label: "",
    value: item,
    tone: "neutral",
  };
}

function summaryItem(label, value, tone = "neutral") {
  const toneClass = summaryToneClass(tone);
  return `
    <div class="command-summary-item ${toneClass}">
      <span>${escapeHtml(uiText(label))}</span>
      <strong>${escapeHtml(valueText(value))}</strong>
    </div>
  `;
}

function summaryGrid(items) {
  return `
    <div class="command-summary-grid">
      ${items.map((item) => {
        const metric = normalizeSummaryMetric(item);
        return summaryItem(metric.label, metric.value, metric.tone);
      }).join("")}
    </div>
  `;
}

function commandSection(title, body, options = {}) {
  const tone = ["ok", "warn", "error", "info", "neutral"].includes(options.tone) ? options.tone : "";
  const kind = options.kind ? String(options.kind) : "";
  const toneClass = tone ? ` ${tone}` : "";
  return `
    <section class="command-section${toneClass}"${kind ? ` data-kind="${escapeHtml(kind)}"` : ""}>
      <h3>${escapeHtml(uiText(title))}</h3>
      ${body}
    </section>
  `;
}

function commandRows(rows) {
  if (!rows.length) return `<div class="subtle">${escapeHtml(t("command.noItems"))}</div>`;
  return `
    <div class="command-list">
      ${rows.map((row) => `
        <div class="command-row ${row.tone || ""}">
          <strong>${escapeHtml(uiText(row.title) || "-")}</strong>
          ${uiText(row.detail) ? `<span class="subtle">${escapeHtml(uiText(row.detail))}</span>` : ""}
          ${row.meta?.length ? `<div class="token-row">${row.meta.map(token).join("")}</div>` : ""}
        </div>
      `).join("")}
    </div>
  `;
}

function renderCommandReadableResult(result, details) {
  const payload = result.stdout_json ?? {};
  const raw = JSON.stringify(payload || result, null, 2);
  const runSummary = [
    [t("field.command"), details.title],
    [t("field.scope"), result.project ? `${details.scope} / ${result.project}` : details.scope],
    [t("field.result"), commandResultJudgement(result).label],
    [t("field.duration"), `${result.duration_sec}s`],
  ];
  if (result.new_machine_id) runSummary.push([t("label.newMachine"), result.new_machine_id]);
  if (result.connection_mode && result.command_key === "machine-collab-guide") {
    runSummary.push([t("label.connectionMode"), result.connection_mode]);
  }
  runSummary.push([t("field.confirmationRequired"), boolText(result.confirmation_required)]);
  if (result.confirmation_required || result.confirmed) {
    runSummary.push([t("field.confirmed"), boolText(result.confirmed)]);
  }
  const executionMeta = [
    `${t("word.return")} ${result.returncode}`,
    result.read_only ? t("word.readOnly") : t("word.mutating"),
  ];
  if (result.confirmation_required) {
    executionMeta.push(result.confirmed ? t("field.confirmed") : t("field.confirmationRequired"));
  }
  const evidence = `
    <div class="command-evidence">
      <div class="command-evidence-group">
        <div class="small-label">${escapeHtml(t("command.section.runSummary"))}</div>
        ${summaryGrid(runSummary)}
      </div>
      <div class="command-evidence-group">
        <div class="small-label">${escapeHtml(t("command.section.executed"))}</div>
        ${commandRows([
      {
        title: result.command || result.command_key || "-",
        detail: details.detail || t("command.readOnlyDiagnostic"),
        meta: executionMeta,
      },
    ])}
      </div>
    </div>
  `;
  const sections = [
    renderCommandSummary(result, payload),
    commandSection(t("command.section.executionEvidence"), evidence, { kind: "evidence", tone: "neutral" }),
    `
      <details class="raw-output">
        <summary>${escapeHtml(t("command.section.rawJson"))}</summary>
        <pre>${escapeHtml(raw)}</pre>
      </details>
    `,
  ];
  return `<div class="command-human">${sections.join("")}</div>`;
}

function renderCommandSummary(result, payload) {
  const blocks = Array.isArray(result.summary_blocks) ? result.summary_blocks : [];
  if (!blocks.length) return renderCommandPayloadSummary(result.command_key, payload);
  return blocks.map(renderCommandSummaryBlock).join("");
}

function renderCommandSummaryBlock(block) {
  const metrics = Array.isArray(block.metrics) ? block.metrics : [];
  const rows = Array.isArray(block.rows) ? block.rows : [];
  const actions = Array.isArray(block.actions) ? block.actions : [];
  const body = [
    uiText(block.summary)
      ? `<p class="command-block-summary">${escapeHtml(uiText(block.summary))}</p>`
      : "",
    metrics.length ? summaryGrid(metrics) : "",
    rows.length
      ? commandRows(rows.map((row) => ({
        title: row.title,
        detail: row.detail,
        tone: row.tone,
        meta: row.meta || [],
      })))
      : "",
    actions.length
      ? `
        <div class="command-actions">
          <div class="small-label">${escapeHtml(state.lang === "ko" ? "권장 다음 확인" : "Suggested next checks")}</div>
          ${commandRows(actions.map((row) => ({
            title: row.title,
            detail: row.detail,
            tone: row.tone || "info",
            meta: row.meta || [],
          })))}
        </div>
      `
      : "",
  ].join("");
  return commandSection(block.title, body, { kind: block.kind, tone: block.tone });
}

function renderCommandPayloadSummary(commandKey, payload) {
  if (Array.isArray(payload)) {
    return commandSection(t("command.section.bindingRecords"), commandRows(payload.slice(0, 30).map((item) => ({
      title: `${item.project_id || "-"} / ${item.role || "-"} / ${item.machine_id || "-"}`,
      detail: item.workspace_path || item.binding_id || "",
      meta: [
        `${t("field.status")} ${localizedStatus(item.status || "-")}`,
        `${t("field.thread")} ${item.thread_id || "-"}`,
      ],
    }))));
  }

  const schema = String(payload?.schema || "");
  if (schema.includes("collab_binding_align")) return renderCollabAlignSummary(payload);
  if (schema.includes("worker_status")) return renderWorkerStatusSummary(payload);
  if (schema.includes("overview")) return renderOverviewSummary(payload);
  if (schema.includes("project_status")) return renderProjectStatusSummary(payload);
  if (schema.includes("project_versioning_readiness")) return renderVersioningSummary(payload);
  if (schema.includes("project_sync")) return renderProjectSyncSummary(payload);
  if (schema.includes("project_snapshots")) return renderSnapshotsSummary(payload);
  if (schema.includes("project_away_report")) return renderAwayReportSummary(payload);

  return renderGenericPayloadSummary(commandKey, payload);
}

function renderCollabAlignSummary(payload) {
  const items = payload.items || [];
  return commandSection(t("command.section.collabAlignment"), `
    ${summaryGrid([
      [t("field.aligned"), payload.aligned_count ?? 0],
      [t("field.created"), payload.created_count ?? 0],
      [t("field.warnings"), payload.warning_count ?? 0],
      [t("field.dryRun"), payload.dry_run],
    ])}
    ${commandRows(items.map((item) => ({
      title: `${item.peer_machine_id || item.peer_host || "-"} / ${roleValue(item.peer_role)}`,
      detail: item.message || "",
      meta: [
        `${t("field.project")} ${item.project_id || "-"}`,
        `${t("field.status")} ${localizedStatus(item.status || "-")}`,
        `${state.lang === "ko" ? "연결" : "link"} ${localizedStatus(item.peer_status || "-")}`,
        `${state.lang === "ko" ? "세션" : "session"} ${item.peer_session_id || "-"}`,
      ],
    })))}
  `);
}

function renderWorkerStatusSummary(payload) {
  const workers = payload.workers || [];
  return commandSection(t("command.section.workerStatus"), `
    ${summaryGrid([
      [t("field.workers"), payload.worker_count ?? workers.length],
      [t("field.available"), payload.available_count ?? 0],
      [t("field.busy"), payload.busy_count ?? 0],
      [t("field.stale"), payload.stale_count ?? 0],
    ])}
    ${commandRows(workers.map((worker) => {
      const health = worker.health || {};
      const peer = worker.peer || {};
      return {
        title: worker.display_name || worker.host || "-",
        detail: `${worker.host || "-"} -> ${peer.host || health.peer_host || "-"}`,
        meta: [
          `${state.lang === "ko" ? "역할" : "role"} ${roleValue(worker.role)}`,
          `${state.lang === "ko" ? "활동" : "activity"} ${localizedStatus(worker.activity || "-")}`,
          `${state.lang === "ko" ? "상태" : "state"} ${localizedStatus(health.state_status || "-")}`,
          `${state.lang === "ko" ? "연결" : "link"} ${localizedStatus(health.peer_status || "-")}`,
        ],
      };
    }))}
  `);
}

function renderOverviewSummary(payload) {
  const projects = payload.projects || {};
  const workers = payload.workers || {};
  const attention = payload.attention_severity_counts || {};
  return commandSection(t("command.section.overview"), summaryGrid([
    [t("field.machine"), payload.machine_id || "-"],
    [t("label.projects"), `${projects.ok_count ?? 0}/${projects.project_count ?? 0}`],
    [t("field.workers"), `${workers.available_count ?? 0}/${workers.worker_count ?? 0}`],
    [t("field.attention"), attention.total_count ?? payload.attention_count ?? 0],
  ]));
}

function renderProjectStatusSummary(payload) {
  const sync = payload.sync_summary || {};
  const bindings = payload.bindings || {};
  const backup = payload.online_backup || {};
  const integration = payload.integration_profile || {};
  const versioning = payload.versioning_readiness || {};
  const publisher = versioning.publisher_context || {};
  const dataHandling = payload.data_handling || {};
  return commandSection(t("command.section.projectStatus"), summaryGrid([
    [t("field.project"), payload.project_id || "-"],
    [t("field.workspace"), payload.workspace_path || "-"],
    [t("label.integration"), integration.mode ? `${localizedStatus(integration.mode)} / ${localizedStatus(integration.status || "-")}` : "-"],
    [state.lang === "ko" ? "publisher" : "publisher", publisher.is_online_publisher === undefined ? "-" : boolText(publisher.is_online_publisher)],
    [t("label.dataHandling"), localizedStatus(dataHandling.status || "-")],
    [t("label.artifactPointers"), dataHandling.artifact_pointer_count ?? "-"],
    [t("field.syncReady"), `${sync.required_sync_ready_count ?? 0}/${sync.required_repo_count ?? 0}`],
    [t("field.mainSub"), `${bindings.project_main_count ?? bindings.main_count ?? 0}/${bindings.project_worker_count ?? bindings.worker_count ?? 0}`],
    [t("field.onlineBackup"), `${backup.enabled_count ?? 0}/${backup.repo_count ?? 0}`],
    [t("field.attention"), payload.attention_count ?? 0],
  ]));
}

function renderVersioningSummary(payload) {
  const findings = payload.findings || payload.items || [];
  const integration = payload.integration_profile || {};
  const publisher = payload.publisher_context || {};
  return commandSection(t("command.section.versioningReadiness"), `
    ${summaryGrid([
      [t("field.project"), payload.project_id || "-"],
      [t("label.integration"), integration.mode ? `${localizedStatus(integration.mode)} / ${localizedStatus(integration.status || "-")}` : "-"],
      [state.lang === "ko" ? "publisher" : "publisher", publisher.is_online_publisher === undefined ? "-" : boolText(publisher.is_online_publisher)],
      [t("field.ok"), payload.ok],
      [t("label.publicationGate"), versioningPublicationGate(payload)],
      [t("field.routinePublish"), payload.routine_publish_ready],
      [t("label.dirtyWip"), versioningDirtyCount(payload)],
      [t("field.reproducibility"), payload.reproducibility_ready],
      [state.lang === "ko" ? "복구 source" : "repro source", versioningRecoverySource(payload)],
      [t("label.localSnapshotCoverage"), versioningBoolLabel(payload, "local_snapshot_reproducibility_ready")],
      [t("label.metadataCoverage"), versioningBoolLabel(payload, "metadata_reproducibility_ready")],
      [t("field.warnings"), payload.warning_finding_count ?? 0],
      [t("field.blockers"), payload.blocking_finding_count ?? 0],
    ])}
    ${commandRows(findings.slice(0, 12).map((item) => ({
      title: item.title || item.kind || item.name || (state.lang === "ko" ? "점검 항목" : "Finding"),
      detail: item.message || item.details || "",
      meta: [item.severity || item.status || ""].filter(Boolean),
    })))}
  `);
}

function renderProjectSyncSummary(payload) {
  const repos = payload.repos || payload.repo_results || [];
  const rows = Array.isArray(repos)
    ? repos.map((repo) => ({
      title: repo.repo_id || repo.display_name || repo.path || "Repo",
      detail: repo.path || repo.workspace_path || repo.message || "",
      meta: [
        `${t("field.status")} ${localizedStatus(repo.status || repo.sync_status || "-")}`,
        `${localizedStatus("ready")} ${valueText(repo.sync_ready ?? repo.required_sync_ready)}`,
      ],
    }))
    : Object.entries(repos).map(([name, repo]) => ({
      title: name,
      detail: repo.path || repo.workspace_path || "",
      meta: [`${t("field.status")} ${localizedStatus(repo.status || "-")}`],
    }));
  return commandSection(t("command.section.syncPreview"), `
    ${summaryGrid([
      [t("field.project"), payload.project_id || "-"],
      [t("field.dryRun"), payload.dry_run],
      [t("field.required"), payload.required_repo_count ?? rows.length],
      [localizedStatus("ready"), payload.required_sync_ready_count ?? "-"],
    ])}
    ${commandRows(rows)}
  `);
}

function renderSnapshotsSummary(payload) {
  const snapshots = payload.snapshots || payload.items || [];
  return commandSection(t("command.section.snapshots"), `
    ${summaryGrid([
      [t("field.project"), payload.project_id || "-"],
      [t("label.localSnapshotManifests"), payload.snapshot_count ?? snapshots.length],
      [t("label.latestSnapshot"), payload.latest_snapshot || payload.latest_project_snapshot || "-"],
      [t("field.limit"), payload.limit ?? "-"],
    ])}
    ${commandRows(snapshots.slice(0, 12).map((item) => ({
      title: item.snapshot_id || item.name || item.created_at_local || "Manifest",
      detail: item.manifest_path || item.path || item.commit || item.summary || "",
      meta: [
        item.created_at_local || "",
        item.status ? localizedStatus(item.status) : "",
      ].filter(Boolean),
    })))}
  `);
}

function renderAwayReportSummary(payload) {
  return commandSection(t("command.section.awayReport"), summaryGrid([
    [t("field.project"), payload.project_id || "-"],
    [t("field.planPresent"), payload.plan_present ?? payload.present],
    [t("field.status"), localizedStatus(payload.status || "-")],
    [t("field.decision"), payload.latest_decision || "-"],
    [t("field.cycles"), payload.valid_cycle_count ?? "-"],
    [t("field.attention"), payload.attention_count ?? 0],
  ]));
}

function renderGenericPayloadSummary(commandKey, payload) {
  const keys = [
    "schema",
    "ok",
    "status",
    "project_id",
    "machine_id",
    "active_binding_count",
    "warning_count",
    "error_count",
    "attention_count",
  ];
  const present = keys
    .filter((key) => payload && Object.prototype.hasOwnProperty.call(payload, key))
    .map((key) => [genericFieldLabel(key), payload[key]]);
  return commandSection(
    t("command.section.readableSummary"),
    present.length
      ? summaryGrid(present)
      : commandRows([{ title: commandKey || "Command", detail: t("command.noCompactSummary") }]),
  );
}

function genericFieldLabel(key) {
  const labels = {
    ok: "field.ok",
    status: "field.status",
    project_id: "field.project",
    machine_id: "field.machine",
    warning_count: "field.warnings",
    attention_count: "field.attention",
  };
  return labels[key] ? t(labels[key]) : key.replaceAll("_", " ");
}

function renderCommandContext() {
  const project = selectedProject();
  const display = projectDisplay(project);
  $("commandProjectName").textContent = project?.display_name || state.selectedProject || "-";
  $("commandProjectMeta").textContent = state.selectedProject
    ? `${t("command.meta.projectTarget")} ${state.selectedProject}`
    : t("command.meta.projectSelect");
  $("commandProjectBadge").textContent = display.label;
  $("commandProjectBadge").className = `pill ${display.tone}`;
  $("commandRegistryMeta").textContent = commandRegistryMetaText();
}

function selectProject(projectId, view = "") {
  if (!projectId) return;
  state.selectedProject = projectId;
  if (view) {
    state.activeView = view;
    window.location.hash = view;
  }
  render();
}

function bindEvents() {
  $("refreshButton").addEventListener("click", () => refreshConsole().catch(showError));
  $("projectSelect").addEventListener("change", (event) => {
    state.selectedProject = event.target.value;
    render();
    if (state.activeView === "monitor") loadCollabMonitor({ silent: true }).catch(showError);
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeView = button.dataset.view;
      window.location.hash = state.activeView;
      render();
      if (state.activeView === "monitor") loadCollabMonitor({ silent: true }).catch(showError);
    });
  });
  window.addEventListener("hashchange", () => {
    state.activeView = initialView();
    render();
    if (state.activeView === "monitor") loadCollabMonitor({ silent: true }).catch(showError);
  });
  document.addEventListener("click", (event) => {
    const monitorLink = event.target.closest("[data-monitor-project]");
    if (monitorLink) {
      event.preventDefault();
      selectProject(monitorLink.dataset.monitorProject, "monitor");
      loadCollabMonitor({ silent: true }).catch(showError);
      return;
    }
    const button = event.target.closest("[data-command]");
    if (!button) return;
    if (button.dataset.commandProject) {
      state.selectedProject = button.dataset.commandProject;
    }
    if (button.dataset.commandShortcut) {
      state.activeView = "commands";
      window.location.hash = state.activeView;
      render();
    }
    runCommand(button.dataset.command).catch(showError);
  });
  document.querySelectorAll("[data-lang]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!SUPPORTED_LANGS.has(button.dataset.lang)) return;
      state.lang = button.dataset.lang;
      window.localStorage.setItem(LANG_STORAGE_KEY, state.lang);
      render();
    });
  });
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-select-project]");
    if (!button) return;
    selectProject(button.dataset.selectProject, "projects");
  });
}

function showError(error) {
  setStatus(localizedStatus("error"), "error");
  setCommandState(localizedStatus("error"), "error");
  $("commandMeta").textContent = localizedStatus("error");
  $("commandLog").innerHTML = `
    <div class="command-human">
      ${commandSection(localizedStatus("error"), commandRows([{ title: t("command.failed"), detail: error.stack || String(error) }]))}
    </div>
  `;
}

bindEvents();
renderI18nText();
setStatus(localizedStatus("loading"), "neutral");
renderCommandLog();
loadAll().catch(showError);
