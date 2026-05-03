#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any


def _nonempty_paths(values: Any) -> list[Path]:
    if not isinstance(values, list):
        return []
    result: list[Path] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            result.append(Path(text))
    return result


def _infer_home_root(paths: list[Path]) -> Path | None:
    for path in paths:
        if not path.is_absolute():
            continue
        parts = path.parts
        if len(parts) >= 3:
            return Path(*parts[:3])
    return None


def _best_matching_root(path: Path, roots: list[Path]) -> Path | None:
    best: Path | None = None
    best_len = -1
    for root in roots:
        if not root.is_absolute():
            continue
        try:
            path.relative_to(root)
        except ValueError:
            continue
        root_len = len(str(root))
        if root_len > best_len:
            best = root
            best_len = root_len
    return best


def _machine_workspace_sets(project: dict[str, Any]) -> list[list[Path]]:
    workspace_map = project.get("machine_workspaces", {})
    if not isinstance(workspace_map, dict):
        return []
    result: list[list[Path]] = []
    for values in workspace_map.values():
        paths = _nonempty_paths(values)
        if paths:
            result.append(paths)
    return result


def _source_roots_for_path(project: dict[str, Any], path: Path) -> list[Path]:
    root_sets: list[list[Path]] = []
    primary_repos = _nonempty_paths(project.get("primary_repos", []))
    if primary_repos:
        root_sets.append(primary_repos)
    root_sets.extend(_machine_workspace_sets(project))

    best_roots: list[Path] = []
    best_len = -1
    for roots in root_sets:
        matched = _best_matching_root(path, roots)
        if matched is None:
            continue
        matched_len = len(str(matched))
        if matched_len > best_len:
            best_roots = roots
            best_len = matched_len
    return best_roots or primary_repos


def _translate_path(
    path_text: Any,
    source_roots: list[Path],
    target_roots: list[Path],
    target_home: Path | None,
) -> str:
    text = str(path_text or "").strip()
    if not text:
        return text
    path = Path(text)
    if not path.is_absolute():
        return text

    pairs = [
        (source_root, target_roots[index])
        for index, source_root in enumerate(source_roots)
        if index < len(target_roots)
    ]
    pairs.sort(key=lambda pair: len(str(pair[0])), reverse=True)
    for source_root, target_root in pairs:
        try:
            relative = path.relative_to(source_root)
        except ValueError:
            continue
        if str(relative) == ".":
            return str(target_root)
        return str(target_root / relative)

    source_home = _infer_home_root(source_roots)
    if source_home is None or target_home is None:
        return text
    try:
        relative = path.relative_to(source_home)
    except ValueError:
        return text
    if str(relative) == ".":
        return str(target_home)
    return str(target_home / relative)


def find_project_for_path(projects: list[dict[str, Any]], path_text: Any) -> dict[str, Any] | None:
    text = str(path_text or "").strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = path.resolve()

    best_project: dict[str, Any] | None = None
    best_len = -1
    for project in projects:
        root_sets: list[list[Path]] = []
        primary_repos = _nonempty_paths(project.get("primary_repos", []))
        if primary_repos:
            root_sets.append(primary_repos)
        root_sets.extend(_machine_workspace_sets(project))
        for roots in root_sets:
            matched = _best_matching_root(path, roots)
            if matched is None:
                continue
            matched_len = len(str(matched))
            if matched_len > best_len:
                best_project = project
                best_len = matched_len
    return best_project


def resolve_workspace_for_machine(
    project: dict[str, Any],
    path_text: Any,
    machine_id: str | None,
    *,
    fallback_home: Path | None = None,
) -> str:
    text = str(path_text or "").strip()
    if not text:
        return text
    path = Path(text).expanduser()
    if not path.is_absolute():
        return text

    source_roots = _source_roots_for_path(project, path)
    machine_workspaces_map = project.get("machine_workspaces", {})
    if not isinstance(machine_workspaces_map, dict) or not machine_id:
        return text
    target_roots = _nonempty_paths(machine_workspaces_map.get(machine_id, []))
    target_home = _infer_home_root(target_roots) or fallback_home
    return _translate_path(text, source_roots, target_roots, target_home)


def resolve_project_payload(
    project: dict[str, Any],
    machine_id: str | None,
    *,
    fallback_home: Path | None = None,
) -> dict[str, Any]:
    source_roots = _nonempty_paths(project.get("primary_repos", []))
    machine_workspaces_map = project.get("machine_workspaces", {})

    if machine_id:
        target_roots = _nonempty_paths(machine_workspaces_map.get(machine_id, []))
        machine_workspaces: Any = [str(path) for path in target_roots]
    else:
        target_roots = []
        machine_workspaces = machine_workspaces_map

    target_home = _infer_home_root(target_roots) or fallback_home
    if machine_id:
        start_docs = [
            _translate_path(path, source_roots, target_roots, target_home)
            for path in project.get("start_docs", [])
        ]
        reentry_order = [
            _translate_path(path, source_roots, target_roots, target_home)
            for path in project.get("reentry_order", [])
        ]
        memory_docs = [
            _translate_path(path, source_roots, target_roots, target_home)
            for path in project.get("memory_docs", [])
        ]
        backup_paths = [
            _translate_path(path, source_roots, target_roots, target_home)
            for path in project.get("backup_paths", [])
        ]
    else:
        start_docs = project.get("start_docs", [])
        reentry_order = project.get("reentry_order", [])
        memory_docs = project.get("memory_docs", [])
        backup_paths = project.get("backup_paths", [])

    return {
        "project_id": project.get("project_id"),
        "display_name": project.get("display_name"),
        "participant_machine_ids": project.get("participant_machine_ids", []),
        "preferred_main_machine_ids": project.get("preferred_main_machine_ids", []),
        "machine_roles": project.get("machine_roles", {}),
        "main_machine_ids": project.get("main_machine_ids", []),
        "worker_machine_ids": project.get("worker_machine_ids", []),
        "observer_machine_ids": project.get("observer_machine_ids", []),
        "start_docs": start_docs,
        "reentry_order": reentry_order,
        "memory_docs": memory_docs,
        "backup_paths": backup_paths,
        "hardware_ids": project.get("hardware_ids", []),
        "machine_id": machine_id,
        "machine_workspaces": machine_workspaces,
    }
