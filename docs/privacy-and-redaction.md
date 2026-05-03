# Privacy And Redaction

This guide defines the public CLUTCH privacy boundary. Use it before staging a
release, before writing release notes, and before changing a repository from
private to public.

## Scanner-Covered Risks

The public scanner is a first line of defense. It checks exported text files for
patterns such as:

- private key material;
- GitHub and API token formats;
- real user home paths;
- private network address patterns;
- concrete SSH account endpoints;
- operator-maintained private denylist entries.

Run it from the public release root:

```bash
python3 tools/clutch_distribution_scan.py . --json
```

For private staging, also run a denylist that is stored outside the exported
tree:

```bash
python3 tools/clutch_distribution_scan.py . --private-denylist <private-denylist.txt> --json
```

The private denylist should include local lab names, real machine nicknames,
private remotes, SSH aliases, private artifact roots, project names that should
not appear publicly, and any phrase that would identify the source lab.

## Manual Review Risks

Scanner success is necessary but not sufficient. Some risks require human
review because they can be written in ordinary language:

- screenshots that reveal account names, browser profiles, private tabs, or
  filesystem paths;
- docs that mention a real lab topology, hardware serial, project sponsor, or
  unpublished dataset;
- release notes that include internal commit evidence, private machine names,
  or local backup ids;
- examples that are technically fake but look like real credentials or real
  peer addresses;
- generated media that accidentally shows private operator context.

Treat these as release blockers until rewritten.

## Private Machine Identity

Do not publish real machine ids, hostnames, workstation labels, usernames, or
operator names. Public examples should use placeholders such as:

- `main-laptop`;
- `gpu-worker`;
- `lab-demo`;
- `my-project`;
- `/path/to/shared-clutch-collab`.

The first-run wizard should ask each user to choose their own machine identity.
The release tree must not pre-fill a lab-specific identity.

## Network And Transport

The public docs may recommend a direct wired LAN as a reliable topology. They
must not embed a real LAN address, real SSH alias, private DNS name, or
organization-specific mount path.

Acceptable public examples:

- `/path/to/shared-clutch-collab`;
- `<main-machine-id>`;
- `<worker-machine-id>`;
- `main-laptop`;
- `gpu-worker`.

Do Not Publish:

- real peer addresses;
- real SSH config host aliases;
- real usernames paired with remote hosts;
- robot controller addresses;
- private VPN, NAS, or shared-drive paths.

## GitHub And Credentials

The public package must not ship a GitHub token, private remote, credential
helper output, private deploy key, or organization-specific account setup.

The correct public flow is:

1. The user installs CLUTCH locally.
2. The first-run wizard asks for GitHub preference.
3. The user connects their own account and remotes later if they choose.
4. Public repository visibility changes remain blocked until explicit operator
   approval.

## Artifacts And Large Files

Large files should not be included just because they helped develop the
release. Keep these out of the public tree unless they are intentionally small,
public, and documented:

- datasets;
- model weights;
- generated checkpoints;
- robot bags;
- media captures;
- logs;
- caches;
- local backups;
- restore workspaces.

When an artifact matters for reproducibility, publish a pointer policy or
example path format, not the private artifact itself.

## Release Notes Review

Before uploading release notes, check that they do not include:

- private machine, path, backup, or snapshot ids;
- private commit evidence from non-public repositories;
- unpublished project names;
- internal operator notes;
- private staging temp directories;
- private issue or pull request links.

Release notes should describe user-facing behavior, verification commands,
known limitations, and approval boundaries.

## Final Public Review

Before changing public repository visibility, verify:

- `make verify` passes from a clean clone or extracted zip;
- `tools/clutch_public_visibility_review.py --root . --json` reports
  `status=ready_for_manual_visibility_review` and
  `remote_visibility_change_performed=false`;
- scanner finding count is zero;
- release gate status is `ready_for_operator_review`;
- private denylist scan finding count is zero;
- README first screen, landing page, FAQ, command cheat sheet, and demo script
  all describe the same public setup;
- no screenshots or assets reveal private state;
- generated release notes are public-facing;
- the operator gives explicit operator approval for the visibility change.

If any item is unclear, keep the repository private.
