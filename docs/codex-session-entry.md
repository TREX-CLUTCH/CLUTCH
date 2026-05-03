# Codex Session Entry

CLUTCH is most useful when every new Codex session enters through CLUTCH before
starting project work. Session entry gives Codex the active project, role,
project docs, local memory, Web console URL, and collab monitor guidance.

## Manual Entry

After first-run setup, run this at the start of a Codex session:

```bash
export CLUTCH_HOME="${CLUTCH_HOME:-$HOME/.clutch}"
cd "$CLUTCH_HOME/foundation/current"
python3 scripts/clutch_ctl.py session-entry
```

`session-entry` is local-first. It reads your local CLUTCH profile, starts the
Web console when your first-run settings allow it, and prints the browser URL
when it cannot safely open a browser.

## Recommended AGENTS.md Entry

For routine Codex use, copy the template below into the relevant `AGENTS.md`
file for your user or project:

```text
templates/AGENTS.clutch.example.md
```

That template tells Codex to run `session-entry` first when CLUTCH is installed.
It supports the default `$HOME/.clutch` install and custom installs that export
`CLUTCH_HOME`.

Keep the entry generic. Do not put GitHub tokens, private SSH aliases, LAN IPs,
machine passwords, artifact-store secrets, or project-specific hardware details
into `AGENTS.md`.

## Custom Install Prefix

If you installed CLUTCH somewhere other than `$HOME/.clutch`, make the prefix
available before starting Codex:

```bash
export CLUTCH_HOME="$HOME/dev/.clutch"
```

The installer prints this reminder after a custom-prefix install. Add the same
export to your shell profile only if that location should be the normal CLUTCH
home for future sessions.

## What Entry Provides

When CLUTCH can identify a project, `session-entry` prints:

- the active project and resolved workspace;
- whether the current session is attached as `main`, `worker`, or `observer`;
- project start docs and durable memory docs;
- project refresh, sync, backup, and history commands;
- Web console and collab monitor URLs;
- away-plan and operator-intent status when present.

If CLUTCH cannot identify the project yet, register a project with
`project-create`, then attach the session with `session-attach`.

