# Backup And Restore

CLUTCH separates source control, local backups, snapshot metadata, and large
artifact storage. This is important for model training, robotics logs, media,
datasets, and hardware experiments.

## What Goes Where

Source repository:

- code;
- small configs;
- runbooks;
- compact result tables;
- project history;
- reproducibility notes.

Local backup:

- recoverable working tree state;
- machine-local files that should not be lost;
- compact snapshots before risky work.

Snapshot metadata:

- repository heads;
- machine id;
- created time;
- project id;
- backup evidence;
- restore-smoke evidence;
- artifact pointers.

Artifact store:

- model weights;
- datasets;
- media captures;
- robot bags;
- caches;
- generated checkpoints too large for git.

## Typical Workflow

If this is a fresh public install, register a project with `project-create`
before using these commands. See [Getting Started](getting-started.md) for the
first project flow.

Before risky work:

```bash
python3 scripts/clutch_ctl.py project-refresh --project my-project --dry-run
python3 scripts/clutch_ctl.py project-backup --project my-project
python3 scripts/clutch_ctl.py project-snapshot --project my-project --write
```

After a meaningful change:

```bash
python3 scripts/clutch_ctl.py project-status --project my-project
python3 scripts/clutch_ctl.py project-versioning-readiness --project my-project
```

When large artifacts are involved, record their location and hashes in the
project's data-handling or artifact pointer document. Do not commit large
private data by accident.

CLUTCH stores its own machine-local memory, metadata, and restore evidence under
`$CLUTCH_HOME/local/projects`. Your actual project workspace remains a normal
git repository.

## Reproducibility Meaning

When CLUTCH says a project is reproducible, it should mean:

- approved online source heads exist or local source has been explicitly
  preserved;
- fresh metadata covers the current state;
- local backups or restore evidence exist where required;
- large assets are referenced by durable pointers;
- the operator can explain how to recover the state later.

It does not mean CLUTCH copied every byte of every model cache or dataset.
