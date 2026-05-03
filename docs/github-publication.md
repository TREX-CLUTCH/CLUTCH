# GitHub Publication Guide

This guide is for the final operator review before the private staging
repository becomes a public CLUTCH release. It does not authorize the visibility
change by itself.

## Repository Metadata

Use public-safe metadata only:

- repository name: `CLUTCH`;
- description: `Local-first multi-PC Codex orchestration for AI and robotics labs`;
- homepage URL:
  `https://trex-clutch.github.io/CLUTCH/`;
- suggested topics: `codex`, `multi-pc`, `robotics`, `ai-agents`,
  `orchestration`, `backup`, `snapshots`, `collaboration`.

Do not put private hostnames, LAN IPs, SSH aliases, lab names, hardware serials,
account names, or internal project names in repository metadata.

## First Screen Review

Before changing repository visibility, the GitHub repository first screen
should show:

- the CLUTCH brand image from `assets/clutch.png`;
- the official landing page link near the top of `README.md`;
- a concise explanation of CLUTCH as a local-first Codex orchestration layer;
- the multi-PC collab, visible monitor, large-project recovery, Web console,
  and away-development advantages;
- a quick install path that starts from a release zip and user-owned
  `CLUTCH_HOME`;
- `make verify` as the main public validation command;
- the Trust And Verification section for user-run smoke checks;
- `make collab-smoke` as the local proof that the packaged file transport can
  create main/worker/request/result monitor evidence;
- the final visibility gate language that says public conversion requires
  explicit operator approval.

## Pre-Public Validation

Run these commands from a freshly exported or cloned staging tree:

```bash
make verify
make visibility-review
make landing-smoke
make web-smoke
make collab-smoke
python3 tools/clutch_public_visibility_review.py --root . --json
python3 tools/clutch_public_release_gate.py --root . --json
python3 tools/clutch_distribution_scan.py . --json
```

Required results:

- scanner `finding_count=0`;
- public release gate `status=ready_for_operator_review`;
- visibility review `status=ready_for_manual_visibility_review` and
  `remote_visibility_change_performed=false`;
- landing smoke `status=passed`;
- Web smoke `status=passed`;
- collab smoke `status=passed`;
- combined verify `status=passed` with scanner, release gate, visibility
  review, landing smoke, Web smoke, collab transport smoke, and
  install/first-project smoke steps.

## Release Artifacts

Before a GitHub release is published, keep these files together:

- `clutch-public-<version>.zip`;
- `clutch-public-<version>.sha256`;
- `clutch-public-<version>-manifest.json`;
- `clutch-public-<version>-release-notes.md`.

Use `docs/release-artifacts.md` to verify checksums and artifact names.

## Visibility Change

The staging repository must stay private until the operator explicitly approves
the public switch after reviewing:

- private-data scanner output;
- public release gate output;
- read-only visibility review output;
- clean install and first-project smoke;
- collab smoke;
- landing page smoke and official Pages URL;
- generated release notes;
- release zip checksums;
- GitHub first screen and repository metadata.

After the repository becomes public, clone it in a fresh directory and rerun
`make verify`. If GitHub Pages will move from the separate landing preview repo
to the public distribution repo, enable Pages only after the public switch. The
public repo ships `.github/workflows/pages.yml`, which publishes the `site/`
landing page and linked public docs to `https://trex-clutch.github.io/CLUTCH/`.
Verify that URL with the same visual and HTTP checks.
