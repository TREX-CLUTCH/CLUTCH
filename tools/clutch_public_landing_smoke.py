#!/usr/bin/env python3
"""Smoke-test the exported CLUTCH static landing page over local HTTP."""

from __future__ import annotations

import argparse
import json
import mimetypes
import socket
import threading
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


PNG_HEADER = b"\x89PNG\r\n\x1a\n"
SVG_MARKER = b"<svg"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch(url: str, timeout: float) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
            return {
                "ok": 200 <= int(response.status) < 300,
                "status": int(response.status),
                "url": url,
                "content_type": response.headers.get("content-type", ""),
                "body": body,
                "byte_count": len(body),
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status": int(exc.code),
            "url": url,
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "body": exc.read() if exc.fp else b"",
            "byte_count": 0,
            "error": str(exc),
        }
    except OSError as exc:
        return {
            "ok": False,
            "status": 0,
            "url": url,
            "content_type": "",
            "body": b"",
            "byte_count": 0,
            "error": str(exc),
        }


def add_finding(findings: list[dict[str, str]], kind: str, path: str, message: str) -> None:
    findings.append({"kind": kind, "path": path, "message": message})


def check_text(
    *,
    findings: list[dict[str, str]],
    path: str,
    text: str,
    needles: tuple[str, ...],
) -> None:
    for needle in needles:
        if needle not in text:
            add_finding(findings, "missing_required_text", path, f"missing required text: {needle}")


def landing_smoke(*, root: Path, timeout: float) -> dict[str, Any]:
    root = root.expanduser().resolve()
    findings: list[dict[str, str]] = []
    if not root.exists():
        add_finding(findings, "missing_root", str(root), "release root does not exist")
        return build_payload(root, findings, [], "")

    port = free_port()
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    urls = {
        "site/index.html": f"{base_url}/site/",
        "site/styles.css": f"{base_url}/site/styles.css",
        "assets/clutch.png": f"{base_url}/assets/clutch.png",
        "assets/clutchmainimage.png": f"{base_url}/assets/clutchmainimage.png",
        "assets/clutch-ecosystem-architecture.svg": f"{base_url}/assets/clutch-ecosystem-architecture.svg",
        "docs/prompt-cookbook.md": f"{base_url}/docs/prompt-cookbook.md",
        "docs/first-use-acceptance.md": f"{base_url}/docs/first-use-acceptance.md",
        "docs/verification-matrix.md": f"{base_url}/docs/verification-matrix.md",
        "docs/faq.md": f"{base_url}/docs/faq.md",
    }
    markdown_needles = {
        "docs/prompt-cookbook.md": ("Prompt Cookbook", "First Install", "Multi-PC Collab"),
        "docs/first-use-acceptance.md": ("First-Use Acceptance Runbook", "session_entry_repeat"),
        "docs/verification-matrix.md": ("Verification Matrix", "First Install Gates"),
        "docs/faq.md": ("Frequently Asked Questions", "public repository visibility"),
    }
    fetch_results: list[dict[str, Any]] = []
    try:
        for path, url in urls.items():
            result = fetch(url, timeout)
            fetch_results.append(
                {
                    "path": path,
                    "url": url,
                    "ok": bool(result["ok"]),
                    "status": result["status"],
                    "content_type": result["content_type"],
                    "byte_count": result["byte_count"],
                    "error": result.get("error", ""),
                }
            )
            if not result["ok"]:
                add_finding(
                    findings,
                    "http_fetch_failed",
                    path,
                    f"expected HTTP 2xx from {url}, got {result['status']}",
                )
                continue

            body = result["body"]
            if path.endswith(".html"):
                text = body.decode("utf-8", errors="replace")
                check_text(
                    findings=findings,
                    path=path,
                    text=text,
                    needles=(
                        "<h1>CLUTCH for Research Agents</h1>",
                        "View on GitHub",
                        "https://github.com/TREX-CLUTCH/CLUTCH",
                        "styles.css",
                        "../assets/clutch.png",
                        "../assets/clutch-ecosystem-architecture.svg",
                        "Projects enter CLUTCH before they reach agent PCs.",
                        "CLUTCH top-down ecosystem architecture",
                        "Inspect CLUTCH before you depend on it.",
                    ),
                )
            elif path.endswith(".css"):
                text = body.decode("utf-8", errors="replace")
                check_text(
                    findings=findings,
                    path=path,
                    text=text,
                    needles=(
                        "font-family: var(--font-serif)",
                        ".hero h1",
                        "font-family: var(--font-sans)",
                        ".architecture-figure",
                    ),
                )
            elif path.endswith(".png"):
                expected_type = mimetypes.guess_type(path)[0] or "image/png"
                if not body.startswith(PNG_HEADER):
                    add_finding(findings, "invalid_png_asset", path, "clutch.png did not return a PNG header")
                if result["byte_count"] < 1_000_000:
                    add_finding(findings, "small_brand_asset", path, "clutch.png is unexpectedly small")
                if expected_type not in result["content_type"]:
                    add_finding(
                        findings,
                        "unexpected_content_type",
                        path,
                        f"expected {expected_type}, got {result['content_type']}",
                    )
            elif path.endswith(".svg"):
                text = body.decode("utf-8", errors="replace")
                if SVG_MARKER not in body[:200]:
                    add_finding(findings, "invalid_svg_asset", path, "architecture SVG did not start with an SVG marker")
                check_text(
                    findings=findings,
                    path=path,
                    text=text,
                    needles=(
                        "CLUTCH top-down ecosystem architecture",
                        "data:image/png;base64,",
                        "Collab Transport",
                        "Agent PC 1",
                    ),
                )
                if 'href="clutchmainimage.png"' in text:
                    add_finding(
                        findings,
                        "external_nested_logo_reference",
                        path,
                        "architecture SVG must embed the center logo so it renders when loaded through an HTML img tag",
                    )
            elif path.endswith(".md"):
                text = body.decode("utf-8", errors="replace")
                check_text(
                    findings=findings,
                    path=path,
                    text=text,
                    needles=markdown_needles[path],
                )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=timeout)

    return build_payload(root, findings, fetch_results, base_url)


def build_payload(
    root: Path,
    findings: list[dict[str, str]],
    fetch_results: list[dict[str, Any]],
    base_url: str,
) -> dict[str, Any]:
    ok = len(findings) == 0
    return {
        "schema": "clutch.public_landing_smoke.v1",
        "ok": ok,
        "status": "passed" if ok else "failed",
        "root": str(root),
        "base_url": base_url,
        "fetch_results": fetch_results,
        "finding_count": len(findings),
        "findings": findings,
        "next_actions": []
        if ok
        else ["fix landing page HTTP, CSS, image, or GitHub CTA findings before public release"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Exported CLUTCH release root.")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP request timeout in seconds.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = landing_smoke(root=args.root, timeout=args.timeout)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"clutch_public_landing_smoke status={payload['status']} finding_count={payload['finding_count']}")
        for finding in payload["findings"]:
            print(f"{finding['path']}: {finding['kind']}: {finding['message']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
