#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import socket
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


CLUTCH_HOME = Path.home() / ".clutch"
CONFIG_PATH = CLUTCH_HOME / "config" / "notify.json"
STATE_PATH = CLUTCH_HOME / "runtime" / "notify_state.json"
ALLOWED_THRESHOLD_MINUTES = (5, 10, 30, 60)


def default_config() -> dict[str, Any]:
    machine_label = socket.gethostname()
    return {
        "enabled": True,
        "server_url": "https://ntfy.sh",
        "topic": "",
        "machine_label": machine_label,
        "default_session_mode": "long_only",
        "default_session_threshold_minutes": 5,
        "collab_completed_threshold_minutes": 0,
        "title": f"{machine_label} 작업 완료",
        "message_template": f"{machine_label}의 {{session_label}} 세션 Codex가 작동 완료",
        "summary_max_chars": 180,
        "session_root_globs": [
            str(Path.home() / ".cache" / "JetBrains" / "*" / "aia" / "codex" / "sessions"),
            str(Path.home() / ".codex" / "sessions"),
        ],
        "poll_seconds": 2.0,
        "dedupe_limit": 256,
    }


def default_state() -> dict[str, Any]:
    return {
        "file_offsets": {},
        "session_meta": {},
        "session_prefs": {},
        "notified_task_keys": [],
        "suppress_next_task_complete_threads": [],
    }


def load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return json.loads(json.dumps(fallback))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(fallback))
    if not isinstance(data, dict):
        return json.loads(json.dumps(fallback))
    merged = json.loads(json.dumps(fallback))
    merged.update(data)
    return merged


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=path.name + ".",
        delete=False,
    ) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        tmp_path = Path(handle.name)
    os.replace(tmp_path, path)


def load_config(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or CONFIG_PATH, default_config())


def load_state(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or STATE_PATH, default_state())


def save_state(data: dict[str, Any], path: Path | None = None) -> None:
    save_json(path or STATE_PATH, data)


def save_config(data: dict[str, Any], path: Path | None = None) -> None:
    save_json(path or CONFIG_PATH, data)


def current_thread_id(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    env_value = os.environ.get("CODEX_THREAD_ID", "").strip()
    return env_value or None


def normalize_threshold_minutes(value: Any, fallback: int = 10) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    if parsed in ALLOWED_THRESHOLD_MINUTES:
        return parsed
    return fallback


def normalize_session_pref(pref: Any, config: dict[str, Any]) -> dict[str, Any]:
    default_mode = str(config.get("default_session_mode", "off")).strip() or "off"
    default_threshold = normalize_threshold_minutes(config.get("default_session_threshold_minutes", 10))

    if isinstance(pref, bool):
        return {"mode": "on" if pref else "off", "threshold_minutes": default_threshold}

    if not isinstance(pref, dict):
        return {"mode": default_mode, "threshold_minutes": default_threshold}

    mode = str(pref.get("mode", default_mode)).strip() or default_mode
    if mode not in {"off", "on", "long_only"}:
        mode = default_mode
    threshold_minutes = normalize_threshold_minutes(pref.get("threshold_minutes", default_threshold), default_threshold)
    return {"mode": mode, "threshold_minutes": threshold_minutes}


def get_session_pref(config: dict[str, Any], state: dict[str, Any], thread_id: str | None) -> dict[str, Any]:
    if not thread_id:
        return {
            "mode": str(config.get("default_session_mode", "off")),
            "threshold_minutes": normalize_threshold_minutes(config.get("default_session_threshold_minutes", 10)),
        }
    prefs = state.get("session_prefs", {})
    pref = prefs.get(thread_id)
    return normalize_session_pref(pref, config)


def set_session_pref(state: dict[str, Any], thread_id: str, *, mode: str, threshold_minutes: int | None = None) -> None:
    prefs = state.setdefault("session_prefs", {})
    payload: dict[str, Any] = {"mode": mode}
    if mode == "long_only":
        payload["threshold_minutes"] = normalize_threshold_minutes(threshold_minutes, 10)
    prefs[thread_id] = payload


def session_label(cwd: str | None, thread_id: str | None) -> str:
    if cwd:
        name = Path(cwd).name.strip()
        if name:
            return name
    del thread_id
    return "current"


def collapse_whitespace(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()


def contains_hangul(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text))


def normalize_summary_candidate(text: str) -> str:
    value = collapse_whitespace(text)
    if not value:
        return ""
    prefix_pattern = re.compile(
        r"^(completed|done|finished|summary|result|update|note|notes|status)\s*:\s*",
        flags=re.I,
    )
    value = prefix_pattern.sub("", value).strip()
    return value


def trim_summary_text(value: str, *, limit: int) -> str:
    text = collapse_whitespace(value)
    if not text:
        return ""
    if limit > 0 and len(text) > limit:
        return text[: max(limit - 1, 0)].rstrip() + "…"
    return text


def summarize_agent_message(value: Any, *, limit: int = 180) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    text = re.sub(r"```.*?```", " ", value, flags=re.S)
    heading_only = {"핵심 결론", "결론", "요약", "summary", "conclusion"}
    candidates: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = line.replace("**", "").replace("__", "").replace("`", "")
        line = re.sub(r"^[-*+#>\d\.\)\(\s]+", "", line).strip()
        line = normalize_summary_candidate(line)
        if not line:
            continue
        lowered = line.lower().rstrip(":")
        if lowered in heading_only:
            continue
        candidates.append(line)
    if not candidates:
        return ""
    first = trim_summary_text(candidates[0], limit=limit)
    if contains_hangul(first) and summary_is_notification_friendly(first):
        return first
    return ""


def summary_is_notification_friendly(text: str) -> bool:
    lowered = text.lower()
    noisy_tokens = (
        "returncode",
        "response_path",
        "exec_jsonl_path",
        "loadstate=",
        "unitfilestate=",
        "activestate=",
        "substate=",
        "result=",
        "git_head",
    )
    if any(token in lowered for token in noisy_tokens):
        return False
    if text.count("/") >= 2 or text.count("`") >= 2:
        return False
    if sum(1 for char in text if char in "/\\`[]{}_=<>") >= 8:
        return False
    return True


def format_duration_text(duration_ms: Any) -> str:
    try:
        duration_value = int(duration_ms)
    except (TypeError, ValueError):
        return ""
    if duration_value < 60_000:
        seconds = max(duration_value / 1000.0, 0.0)
        return f"{seconds:.0f}초"
    if duration_value < 3_600_000:
        return f"{duration_value / 60_000:.1f}분"
    return f"{duration_value / 3_600_000:.1f}시간"


def build_task_complete_notification(
    config: dict[str, Any],
    *,
    session_name: str,
    cwd: str | None,
    duration_ms: Any,
    last_agent_message: Any,
) -> tuple[str, str]:
    machine_label = str(config.get("machine_label", "CLUTCH")).strip() or "CLUTCH"
    configured_title = str(config.get("title", "")).strip()
    if not configured_title or configured_title.lower().endswith("codex complete"):
        title = f"{machine_label} 작업 완료"
    else:
        title = configured_title
    try:
        summary_limit = int(config.get("summary_max_chars", 180))
    except (TypeError, ValueError):
        summary_limit = 180
    summary = summarize_agent_message(last_agent_message, limit=max(summary_limit, 40))
    duration_text = format_duration_text(duration_ms)

    lines = [f"세션: {session_name}"]
    if cwd:
        lines.append(f"경로: {cwd}")
    if duration_text:
        lines.append(f"소요: {duration_text}")
    if summary:
        lines.append(f"요약: {summary}")
    else:
        lines.append("요약: 방금 요청한 작업이 완료되었습니다.")
    return title, "\n".join(lines)


def suppress_next_task_complete(state: dict[str, Any], thread_id: str) -> None:
    suppressed = state.setdefault("suppress_next_task_complete_threads", [])
    if thread_id in suppressed:
        return
    suppressed.append(thread_id)


def consume_suppressed_task_complete(state: dict[str, Any], thread_id: str) -> bool:
    suppressed = state.setdefault("suppress_next_task_complete_threads", [])
    if thread_id not in suppressed:
        return False
    suppressed.remove(thread_id)
    return True


def should_notify_for_task_complete(
    config: dict[str, Any],
    state: dict[str, Any],
    *,
    thread_id: str | None,
    duration_ms: Any,
) -> bool:
    pref = get_session_pref(config, state, thread_id)
    mode = pref["mode"]
    if mode == "off":
        return False
    if mode == "on":
        return True
    if mode != "long_only":
        return False
    try:
        duration_value = int(duration_ms)
    except (TypeError, ValueError):
        return False
    threshold_ms = int(pref["threshold_minutes"]) * 60 * 1000
    return duration_value >= threshold_ms


def send_ntfy_notification(
    config: dict[str, Any],
    *,
    title: str,
    message: str,
    priority: str = "default",
) -> tuple[int, str]:
    if not config.get("enabled", True):
        raise RuntimeError("Notifications are disabled in config.json")
    topic = str(config.get("topic", "")).strip()
    if not topic:
        raise RuntimeError("ntfy topic is empty in config.json")
    server_url = str(config.get("server_url", "https://ntfy.sh")).rstrip("/")
    url = f"{server_url}/{topic}"
    request = urllib.request.Request(
        url=url,
        data=message.encode("utf-8"),
        method="POST",
        headers={
            "Title": latin1_safe_header(title, fallback="CLUTCH Codex done"),
            "Priority": priority,
            "Tags": "computer",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ntfy HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ntfy request failed: {exc}") from exc


def latin1_safe_header(value: str, *, fallback: str) -> str:
    try:
        value.encode("latin-1")
    except UnicodeEncodeError:
        return fallback
    return value
