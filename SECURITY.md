# Security Boundary

CLUTCH public distribution artifacts must not include private state from the
environment where they were built.

## Never Include

- real usernames, machine ids, hostnames, user home paths, or workstation names;
- private network addresses, SSH endpoints, pairing namespaces, or local peer
  paths;
- tokens, passwords, cookies, private keys, credential helper output, or admin
  guard secrets;
- hardware registry entries copied from a real lab;
- runtime state, backups, snapshots, restore workspaces, local profiles, active
  bindings, or collab queues;
- project histories that describe private work.

## First-Run Security Model

The installer should default to token-based admin guard setup. The token is a
local operator secret. It must be entered interactively or through stdin and
stored only as a local salted hash.

Online GitHub use must be configured by the installing user. The distribution
must not ship with an account, token, or remote URL that grants access to a
private organization.

## Scanner Gate

Run the scanner before packaging:

```bash
python3 tools/clutch_distribution_scan.py .
```

For private release staging, also supply a non-exported denylist file maintained
outside the public distribution tree:

```bash
python3 tools/clutch_distribution_scan.py . --private-denylist <private-denylist.txt>
```

For what the scanner does and does not prove, use
[Privacy And Redaction](docs/privacy-and-redaction.md) before public review.

## Public Visibility Gate

Keep the public-staging repository private until the release candidate passes
the full [Public Release Checklist](docs/public-release-checklist.md) and the
operator explicitly approves the repository visibility change.
