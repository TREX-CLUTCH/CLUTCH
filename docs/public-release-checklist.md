# Public Release Checklist

Use this checklist before changing a private CLUTCH public-staging repository
to public visibility. Passing this checklist does not publish anything by
itself. The final visibility change must be an explicit operator action.

## 1. Source Boundary

- The release source is a clean CLUTCH public export, not a copy of a private
  lab workspace.
- The export contains no private machine ids, hostnames, home paths, LAN IPs,
  SSH aliases, GitHub remotes, tokens, hardware profiles, runtime bindings,
  backup bundles, snapshots, collab queues, or project histories.
- Default registries are empty or example-only.
- The release image and docs are intentionally public assets.

## 2. Scanner Gates

Run the generic scanner against the exported tree:

```bash
python3 tools/clutch_distribution_scan.py .
```

For a private staging process, also run the same scanner with a non-exported
denylist file that contains local lab names, peer aliases, private remotes, and
other strings that must never ship:

```bash
python3 tools/clutch_distribution_scan.py . --private-denylist /path/to/private-denylist.txt
```

Required result:

```text
finding_count=0
```

For routine local verification, run the combined public check:

```bash
make verify
```

Equivalent direct command:

```bash
python3 tools/clutch_public_verify.py --root . --json
```

Then run the read-only public release gate from the exported tree:

```bash
python3 tools/clutch_public_release_gate.py --root . --json
```

Required result:

```text
status=ready_for_operator_review
finding_count=0
```

The release gate also checks the public landing page source for required
positioning copy, local CSS/image references, missing local assets, and script
tags.

Then run the read-only final visibility review:

```bash
make visibility-review
python3 tools/clutch_public_visibility_review.py --root . --json
```

Required result:

```text
status=ready_for_manual_visibility_review
remote_visibility_change_performed=false
public_visibility_requires_operator_approval=true
```

This review does not publish the repository. It only checks that scanner,
public release gate, release docs, privacy docs, and final visibility-gate text
are present before a manual operator action.

The exported GitHub Actions workflow runs the same scanner, public release
gate, visibility review, landing smoke, Web smoke, collab smoke, and install
smoke on public pushes and pull requests. It is supporting evidence, not a
replacement for this checklist.

Confirm the exported issue templates, pull request template, and
`CONTRIBUTING.md` ask users to remove private machine data and preserve
operator-approval boundaries before they report problems.

Review `docs/github-publication.md` before changing repository visibility. It
records the public-safe repository metadata, first-screen review, release
artifact set, and final visibility gate.

Use `docs/verification-matrix.md` to confirm that every core feature has a
matching command, smoke path, or manual evidence item before public release.

## 3. Landing Page Smoke

Inspect the public landing page before a release body or GitHub Pages rollout:

```bash
make landing-smoke
```

For manual visual review, run:

```bash
python3 -m http.server 8899 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8899/site/index.html
```

Expected result:

- CLUTCH's multi-PC Codex, collab monitor, backup/recovery, away-development,
  Web UI, and privacy-first setup advantages are visible;
- the first hero headline is a 2-4 word hook title, not a long explanatory
  sentence or a sparse brand-only label;
- only the landing page hero H1 uses the sans-serif face; all other landing
  page copy, headings, controls, captions, and descriptions use the serif face;
- the guided first-run tutorial, multi-PC topology, and safety boundary are
  visible;
- the CLUTCH image renders;
- example prompts are readable;
- `docs/prompt-cookbook.md` gives practical prompts for first install, first
  project, multi-PC collab, backup/artifacts, away development, Web UI, public
  release review, and safety boundaries;
- the GitHub call-to-action points to the intended public repository;
- `tools/clutch_public_landing_smoke.py --root . --json` reports
  `status=passed` and fetches the linked Prompt Cookbook, First-Use Acceptance
  Runbook, Verification Matrix, and FAQ;
- the repository homepage points to the official landing page;
- no public hosting or GitHub Pages setting is enabled until the operator
  explicitly approves it.

## 4. Clean Install Smoke

Test the release zip in a fresh temporary directory or clean machine profile.
Do not test only from the development checkout.

Preferred self-test from the extracted release tree:

```bash
python3 tools/clutch_public_install_smoke.py --root . --json
```

```bash
unzip clutch-public-*.zip
cd clutch-public-*
export CLUTCH_HOME="$(mktemp -d)/.clutch"
bash installer/install.sh --prefix "$CLUTCH_HOME"
cd "$CLUTCH_HOME/foundation/current"
python3 installer/clutch_first_run_wizard.py --plan-only
python3 installer/clutch_doctor.py
python3 scripts/clutch_ctl.py session-entry
```

Expected result:

- install does not require sudo;
- wizard plan does not contain private defaults;
- doctor is read-only and reports actionable next steps;
- session-entry can start the Web console or print a local URL.

## 5. First Project Smoke

Register one throwaway git project, attach as `main`, and create a local backup
and snapshot.

The preferred clean install self-test already runs this first-project path:

```bash
python3 tools/clutch_public_install_smoke.py --root . --json
```

```bash
python3 scripts/clutch_ctl.py project-create --help
python3 scripts/clutch_ctl.py session-attach --project <project_id> --bind-role main --yes
python3 scripts/clutch_ctl.py project-backup --project <project_id>
python3 scripts/clutch_ctl.py project-snapshot --project <project_id> --write
python3 scripts/clutch_ctl.py project-refresh --project <project_id> --dry-run
```

Expected result:

- project metadata is stored under `CLUTCH_HOME`, not inside the project git
  workspace;
- local backup and snapshot commands complete;
- refresh explains missing optional online setup without treating it as a
  fatal first-use failure.

## 6. Web Console Smoke

Start the Web console and verify the Dashboard, Monitor, Commands, Backups, and
Help tabs. Prefer the packaged smoke first because it checks first-run Web
auto-start, backend health, assets, and cleanup in a temporary install.

```bash
make web-smoke
python3 tools/clutch_public_web_smoke.py --root . --json
python3 scripts/clutch_ctl.py web-console-start --host 127.0.0.1 --port 8765 --replace-stale
python3 scripts/clutch_ctl.py web-console-status
```

Expected result:

- `clutch_public_web_smoke.py` reports `status=passed`;
- backend version matches the current checkout;
- command registry, command surface, and render readiness are ok;
- Help explains CLUTCH's operating protocol in public-facing language;
- Commands remain small and preview-first rather than a large action launcher.

## 7. Multi-PC Collab Smoke

First run the packaged single-machine collab transport smoke. It creates a
temporary shared root, registers a public main and worker, sends a request,
records a result, and verifies the status monitor payload.

```bash
make collab-smoke
python3 tools/clutch_public_collab_smoke.py --root . --json
```

Expected result:

- `status=passed`;
- `machine_count=2`;
- `open_request_count=0`;
- request id `req-public-smoke` is completed;
- recent events include `machine_init`, `request_opened`, and
  `request_result`.

For a real two-machine smoke, use a shared folder that both test machines can
access. A direct wired LAN is recommended when practical, but CLUTCH must not
ship with a preset peer address.

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /path/to/shared-clutch-collab \
  --project-id demo \
  --machine-id main-machine \
  --role main

python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /path/to/shared-clutch-collab \
  --project-id demo \
  --machine-id worker-machine \
  --role worker
```

Expected result:

- both machines can create heartbeat or monitor evidence;
- main and worker roles are visible;
- request, acknowledgement, and result records remain project-scoped;
- peer addresses and credentials stay in the user's local setup only.

## 8. Documentation Review

Read these files in the exported tree:

- `README.md`
- `site/index.html`
- `docs/launch-readiness-brief.md`
- `docs/getting-started.md`
- `docs/first-use-acceptance.md`
- `docs/codex-session-entry.md`
- `docs/multi-pc-collab.md`
- `docs/two-pc-lab-tutorial.md`
- `docs/backup-and-restore.md`
- `docs/away-development.md`
- `docs/troubleshooting.md`
- `docs/verification-matrix.md`
- `docs/prompt-cookbook.md`
- `SECURITY.md`

Required result:

- install instructions start from a release zip and the user's own
  `CLUTCH_HOME`;
- GitHub setup tells users to connect their own account and remotes;
- collab docs recommend a direct wired LAN when useful but never embed a real
  IP, SSH alias, or credential;
- backup docs explain code, local backup, snapshot metadata, and artifact
  pointers without promising that large datasets or model caches are uploaded
  to git;
- Help and README describe CLUTCH as a local-first multi-PC Codex orchestration
  layer for AI and robotics labs.

## 9. Release Notes

Release notes should be understandable to a new user. Include:

- what CLUTCH is;
- who the release is for;
- install command summary;
- core features: Web console, project re-entry, multi-PC collab, collab
  monitor, backups/snapshots, artifact pointers, away-development plans, and
  notifications;
- 10-minute first-use path;
- public landing page with hook hero, guided tutorial, topology, and safety
  boundary;
- explicit security boundary;
- checksum for the release zip;
- SHA256 values for the checksum file, release notes, and release manifest;
- known limitations and approval-required actions.

Do not include private commit evidence ids, internal machine names, lab paths,
or private GitHub references.

Use `docs/release-notes-template.md` as the starting point for the GitHub
release body.
Use `docs/release-artifacts.md` to verify the zip, checksum file, release
manifest, and generated release notes stay together as one artifact set.

## 10. Release Zip Package

From the CLUTCH foundation source checkout, build the public release zip with
the local packaging helper:

```bash
python3 scripts/clutch_public_release_package.py \
  --output-dir /path/to/release-output \
  --version <version> \
  --clean \
  --json
```

Required result:

```text
status=ready_for_private_release_upload
gate.status=ready_for_operator_review
gate.finding_count=0
```

The command creates:

- `clutch-public-<version>.zip`
- `clutch-public-<version>.sha256`
- `clutch-public-<version>.manifest.json`
- `clutch-public-<version>.release-notes.md`

This command does not upload to GitHub and does not change repository
visibility. Treat the zip and checksum as private staging artifacts until the
operator approves publication.

Use the generated `release-notes.md` as a draft GitHub Release body, then review
it manually before upload.

## 11. Final Visibility Gate

Before changing repository visibility, treat the private staging repository as
review evidence only. The official landing page proves visual readiness; it is
not approval to publish the repo or upload a release.

- scanner result is `finding_count=0`;
- public release gate result is `ready_for_operator_review`;
- visibility review result is `ready_for_manual_visibility_review`;
- `remote_visibility_change_performed=false` in the visibility review JSON;
- clean install smoke passed;
- landing page smoke passed;
- first project smoke passed;
- Web smoke passed;
- collab smoke passed;
- release zip checksum is recorded;
- release package manifest is retained with the release evidence;
- generated release notes are reviewed and attached or copied into the GitHub
  release body;
- release notes are public-facing and contain no private machine, path, commit
  evidence, lab machine name, IP address, SSH alias, credential, or private
  GitHub reference;
- the private staging repository is still private;
- the operator explicitly approves the visibility change.
- the final repository visibility switch is a manual operator action.

If any item is unclear, keep the repository private and fix the issue first.
