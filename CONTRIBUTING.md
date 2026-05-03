# Contributing To CLUTCH

CLUTCH is a local-first Codex orchestration layer for multi-PC research and
robotics workflows. Contributions should preserve the public distribution boundary:
no private machines, credentials, addresses, lab paths, hardware
profiles, runtime state, backups, snapshots, or project histories may be added
to this repository.

## Before Opening A Pull Request

Run the public validation path from the repository root:

```bash
make verify
```

Equivalent direct command:

```bash
python3 tools/clutch_public_verify.py --root . --json
```

For final public-visibility readiness review, run:

```bash
make visibility-review
python3 tools/clutch_public_visibility_review.py --root . --json
```

For landing-page-only changes, also run:

```bash
make landing-smoke
```

For Web console or Help changes, also run:

```bash
make web-smoke
```

For collab transport changes, also run:

```bash
make collab-smoke
```

The wrapper executes `clutch_distribution_scan.py`,
`clutch_public_release_gate.py`, `clutch_public_visibility_review.py`,
`clutch_public_landing_smoke.py`, `clutch_public_web_smoke.py`,
`clutch_public_collab_smoke.py`, and `clutch_public_install_smoke.py`.

Expected result:

- scanner reports `finding_count=0`;
- release gate reports `status=ready_for_operator_review`;
- visibility review reports `status=ready_for_manual_visibility_review`;
- landing smoke reports `status=passed`;
- Web smoke reports `status=passed`;
- collab smoke reports `status=passed`;
- install smoke reports `status=passed`.

## Contribution Scope

Good public contributions improve:

- first-run setup on ordinary Linux workstations;
- Web console clarity and read-only status surfaces;
- multi-PC collab transport setup that uses user-owned addresses and remotes;
- backup, snapshot, restore-readiness, and artifact-pointer workflows;
- docs that explain CLUTCH without assuming a private lab configuration.

Do not include:

- real SSH targets, LAN IPs, hostnames, usernames, or home directories;
- GitHub tokens, PATs, cookies, private keys, or credential helper output;
- robot hardware commands, recovery procedures, or driver changes presented as
  safe to run without fresh operator approval;
- large local artifacts, model weights, datasets, logs, media dumps, cache
  folders, or generated release bundles.

## Pull Request Checklist

- I ran the scanner, release gate, landing smoke, Web smoke, collab smoke, and
  public install smoke.
- I did not add private credentials, machine identifiers, paths, or network
  endpoints.
- I kept destructive, hardware, sudo, network, and credential-changing actions
  behind explicit operator approval.
- I updated user-facing docs when behavior changed.
- I added focused tests for new release-gate, installer, Web, or collab
  behavior.

## Security Reports

Do not open a public issue with a secret, private endpoint, credential, or
exploit detail. Follow [SECURITY.md](SECURITY.md) and share only sanitized
reproduction steps in public.
