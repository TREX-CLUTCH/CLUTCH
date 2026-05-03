#!/usr/bin/env python3
"""Scan a CLUTCH distribution tree for secrets and private environment data."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "releases",
    "restore-smoke",
}

MAX_TEXT_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    column: int
    kind: str
    match: str
    message: str


PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "private_key",
        re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |)?PRIVATE KEY-----"),
        "private key material must never be distributed",
    ),
    (
        "github_token",
        re.compile(r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[opsu]_[A-Za-z0-9_]{20,})\b"),
        "GitHub tokens must never be distributed",
    ),
    (
        "api_secret",
        re.compile(r"\b(?:sk-[A-Za-z0-9][A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{20,})\b"),
        "API credentials must never be distributed",
    ),
    (
        "absolute_user_path",
        re.compile(r"(?<![\w.-])(?:/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/|[A-Za-z]:\\\\Users\\\\[A-Za-z0-9._-]+\\\\)"),
        "distribution files must not contain real user home paths",
    ),
    (
        "private_ip_address",
        re.compile(
            r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})\b"
        ),
        "distribution files must not contain real private network addresses",
    ),
    (
        "ssh_endpoint",
        re.compile(r"\b(?:ssh://)?[A-Za-z0-9._%+-]+@[A-Za-z0-9._-]+(?::|/)"),
        "distribution files must not contain concrete SSH account endpoints",
    ),
)


def is_binary(data: bytes) -> bool:
    if b"\0" in data:
        return True
    sample = data[:4096]
    if not sample:
        return False
    textish = sum(byte in b"\n\r\t\f\b" or 32 <= byte <= 126 for byte in sample)
    return textish / len(sample) < 0.75


def iter_files(root: Path, excluded_dirs: set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in excluded_dirs for part in path.relative_to(root).parts[:-1]):
            continue
        yield path


def line_column(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    last_newline = text.rfind("\n", 0, index)
    column = index + 1 if last_newline == -1 else index - last_newline
    return line, column


def redacted(value: str) -> str:
    value = value.strip()
    if len(value) <= 8:
        return "<redacted>"
    return f"{value[:4]}...{value[-4:]}"


def load_private_denylist(path: Path | None) -> list[str]:
    if path is None:
        return []
    entries: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(stripped)
    return entries


def scan_text(relative_path: Path, text: str, denylist: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for kind, pattern, message in PATTERNS:
        for match in pattern.finditer(text):
            line, column = line_column(text, match.start())
            findings.append(
                Finding(
                    path=str(relative_path),
                    line=line,
                    column=column,
                    kind=kind,
                    match=redacted(match.group(0)),
                    message=message,
                )
            )
    for entry in denylist:
        start = 0
        while True:
            index = text.find(entry, start)
            if index < 0:
                break
            line, column = line_column(text, index)
            findings.append(
                Finding(
                    path=str(relative_path),
                    line=line,
                    column=column,
                    kind="private_denylist",
                    match=redacted(entry),
                    message="distribution file contains a private denylist entry",
                )
            )
            start = index + len(entry)
    return findings


def scan_root(root: Path, denylist_path: Path | None = None, excluded_dirs: set[str] | None = None) -> list[Finding]:
    root = root.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    excluded = set(DEFAULT_EXCLUDED_DIRS if excluded_dirs is None else excluded_dirs)
    denylist = load_private_denylist(denylist_path.expanduser().resolve() if denylist_path else None)
    findings: list[Finding] = []
    for path in iter_files(root, excluded):
        try:
            data = path.read_bytes()
        except OSError as exc:
            findings.append(
                Finding(
                    path=str(path.relative_to(root)),
                    line=0,
                    column=0,
                    kind="read_error",
                    match="",
                    message=str(exc),
                )
            )
            continue
        if len(data) > MAX_TEXT_BYTES or is_binary(data):
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(path.relative_to(root), text, denylist))
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Distribution root to scan.")
    parser.add_argument(
        "--private-denylist",
        type=Path,
        default=None,
        help="Optional non-exported newline-delimited private string denylist.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = scan_root(args.root, args.private_denylist)
    payload = {
        "schema": "clutch.distribution_scan.v1",
        "root": str(args.root.expanduser().resolve()),
        "ok": len(findings) == 0,
        "finding_count": len(findings),
        "findings": [asdict(item) for item in findings],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        status = "ok" if payload["ok"] else "failed"
        print(f"distribution_scan status={status} finding_count={payload['finding_count']}")
        for item in findings:
            print(f"{item.path}:{item.line}:{item.column}: {item.kind}: {item.message} ({item.match})")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
