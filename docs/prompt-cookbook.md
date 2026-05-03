# Prompt Cookbook

CLUTCH keeps natural-language Codex control at the center. Use these prompts
as starting points, then replace project names, paths, and machine ids with
your own local setup.

The public distribution does not include private peer addresses, SSH aliases,
GitHub accounts, artifact roots, hardware profiles, or lab-specific defaults.
If a prompt would require those details, ask CLUTCH to guide the setup instead
of hard-coding them into the release tree.

## First Install

```text
Walk me through first-run setup for this machine. Use only local folders I
choose, explain each write before doing it, and do not configure online remotes
unless I explicitly approve them.
```

```text
Run the public doctor and summarize only the blockers, optional setup steps,
and the exact command I should run next.
```

```text
Open or print the Web console URL after session-entry, then show me which Help
sections explain the CLUTCH operating protocol.
```

## First Project

```text
Register this git workspace as a CLUTCH project, attach this Codex session as
main, and keep CLUTCH metadata under my CLUTCH_HOME rather than inside the
project repository.
```

```text
Before I start work, run a preview-first project refresh and tell me whether
the project is ready for backups, snapshots, optional online sync, and artifact
pointers.
```

```text
Create a local backup with project-backup and a local snapshot with
project-snapshot for this project, then explain what can be restored from git,
what can be restored from local backup, and what still needs artifact pointers.
```

## Multi-PC Collab

```text
Help me set up a two-PC CLUTCH collaboration using a user-owned shared folder.
Prefer a direct wired LAN if practical, but do not assume any peer IP address
or SSH alias. Ask me for the shared path and machine ids.
```

```text
Attach this machine as main and prepare instructions for the worker machine to
join the same project through collab transport. Keep all peer credentials and
addresses outside the project repository.
```

```text
Ask the worker session to inspect the failing test logs and return only the
probable cause, affected files, and the smallest safe fix. Keep the collab
monitor visible while it works.
```

```text
Check collab monitor status. Tell me whether the worker link is fresh, which
request is active, whether any acknowledgement is missing, and what evidence
was returned most recently.
```

## Backup And Artifacts

```text
Before this refactor, run project-backup and project-snapshot for this project.
Do not upload large datasets, model weights, logs, media, or caches to git;
record them as artifact pointers instead.
```

```text
Review the artifact pointer status for this project. List missing hashes or
paths, but do not move or delete any large files without explicit approval.
```

```text
After this change, verify that source heads, snapshot metadata, backup
evidence, and artifact pointers describe a reproducible state.
```

## Away Development

```text
Prepare an away-development plan for documentation and test hardening only.
Set a clear expiry, allowed files, stop conditions, and verification commands.
Stop before publishing, touching hardware, changing credentials, deleting user
work, or changing network settings.
```

```text
Continue the active away plan. Work only inside the approved scope, send short
progress updates, run the required validation, and stop if a new approval
boundary appears.
```

```text
Close this away-development slice with a summary, tests run, unresolved risks,
private-publication boundary status, backup id, snapshot id, and next safe
task.
```

## Web UI And Help

```text
Start the local Web console, verify backend health, and show me the Dashboard,
Monitor, Commands, Backups, and Help areas I should inspect first.
```

```text
Use the Web Help content to explain CLUTCH to a new lab member. Emphasize
multi-PC Codex work, visible collab monitor, backups and snapshots, artifact
pointers, and bounded away development.
```

```text
Use command previews only. Do not run write actions from the Web command
surface until I explicitly approve the exact action.
```

## Public Release Review

```text
Run make verify from the public release root and summarize scanner, release
gate, visibility review, landing smoke, Web smoke, collab smoke, install smoke,
and first-project smoke status.
```

```text
Run tools/clutch_public_visibility_review.py --root . --json. Confirm that
remote_visibility_change_performed is false, public visibility still requires
operator approval, and the staging repository remains private.
```

```text
Review README, the landing page, the prompt cookbook, verification matrix,
privacy guide, release checklist, and release notes as if this were a first
public GitHub visitor. List any confusing setup instructions or missing safety
boundaries.
```

## Safety Prompts

```text
Stop and ask me before any hardware motion, sudo, service, kernel, udev,
network, credential, destructive restore, remote publication, or public
visibility action.
```

```text
Scan this change for private machine ids, hostnames, home paths, LAN IPs, SSH
aliases, GitHub tokens, private remotes, runtime state, backups, snapshots, and
project histories before it enters the public distribution.
```

```text
If a command would change files, credentials, hardware, network settings, or
repository visibility, show the preview and wait for explicit approval.
```
