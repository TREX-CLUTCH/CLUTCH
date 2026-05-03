# Doctor And Troubleshooting

Start with the read-only doctor:

```bash
python3 installer/clutch_doctor.py
```

For JSON output:

```bash
python3 installer/clutch_doctor.py --json
```

## First-Run Config Missing

Run:

```bash
python3 installer/clutch_first_run_wizard.py
```

The interactive wizard writes the local first-run config by default. If you only
want to inspect what it would write, add `--plan-only`.

This creates machine-local config under your CLUTCH home. It does not modify
the public distribution templates.

## GitHub Sync Is Not Configured

This is normal for a fresh local-first install. Use your own GitHub account and
remotes when you decide to enable online sync.

The public distribution intentionally ships with empty remote URLs.

## Web Console Does Not Open

After first-run setup, `session-entry` can start the backend automatically:

```bash
python3 scripts/clutch_ctl.py session-entry
```

On SSH or headless machines, CLUTCH should print the URL instead of forcing a
browser. If you want to bypass auto-start for one entry:

```bash
python3 scripts/clutch_ctl.py session-entry --skip-web-console
```

To start the backend manually:

```bash
python3 scripts/clutch_ctl.py web-console-start --host 127.0.0.1 --port 8765
```

Then open:

```text
http://127.0.0.1:8765
```

Run doctor with a Web health check:

```bash
python3 installer/clutch_doctor.py --web-url http://127.0.0.1:8765/api/health
```

## Collab Peer Is Missing

Check:

- both PCs installed CLUTCH;
- both PCs used the same project id;
- the shared collab folder is visible on both PCs;
- each PC has a unique machine id;
- one PC is `main` and the other is `worker`;
- the monitor is looking at the same shared root.

## Backup Warning Appears

Run a read-only refresh first:

```bash
python3 scripts/clutch_ctl.py project-refresh --project my-project --dry-run
```

If the warning says metadata or local backup is missing, decide whether to
create a backup, fetch metadata, or record artifact pointers. Do not silence
backup warnings by deleting evidence.

## Project Not Found

The public distribution starts with no private project registry. Register your
workspace before running project-specific commands:

```bash
python3 scripts/clutch_ctl.py project-create --help
```

The normal flow is:

```bash
python3 scripts/clutch_ctl.py project-create ...
python3 scripts/clutch_ctl.py session-attach --project my-project --bind-role main --cwd /path/to/my-project --yes
python3 scripts/clutch_ctl.py project-backup --project my-project
python3 scripts/clutch_ctl.py project-snapshot --project my-project --write
```

If `project-snapshot` creates a `machines/` folder inside your project
workspace, your first-run config is stale. Re-run the first-run wizard with the
current release or edit the local machine setting so
`local_customization.projects_root` points to `$CLUTCH_HOME/local/projects`, not
your workspace root.
