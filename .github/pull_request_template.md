## Summary

Describe the CLUTCH behavior, docs, or release surface changed by this pull
request.

## Validation

- [ ] `python3 tools/clutch_distribution_scan.py . --json`
- [ ] `python3 tools/clutch_public_release_gate.py --root . --json`
- [ ] `python3 tools/clutch_public_visibility_review.py --root . --json`
- [ ] `python3 tools/clutch_public_landing_smoke.py --root . --json`
- [ ] `python3 tools/clutch_public_collab_smoke.py --root . --json`
- [ ] `python3 tools/clutch_public_install_smoke.py --root . --json`
- [ ] `make verify`
- [ ] `python3 tools/clutch_public_verify.py --root . --json`

## Public Boundary

- [ ] No private machine ids, hostnames, usernames, home paths, LAN IPs, SSH
      aliases, GitHub tokens, private remotes, hardware profiles, runtime state,
      backups, snapshots, or project histories are included.
- [ ] Hardware, sudo, network, credential, destructive-restore, and public
      publication actions still require explicit operator approval.

## Notes

Mention any test gaps or follow-up work that reviewers should understand.
