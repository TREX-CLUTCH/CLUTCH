# First-Run Wizard Contract

The public CLUTCH installer should create only generic local state. Any
machine-specific or account-specific values must come from the installing user.

## Required Questions

1. CLUTCH home directory.
2. Project workspace root directory.
3. Local artifact store directory.
4. Machine display name.
5. Machine id generation: auto-generate by default, allow manual override.
6. Session attach default: `prompt` by default.
7. Online sync mode: `off`, `best_effort`, or `required`.
8. GitHub setup: skip, use existing local `git`, or guide through `gh auth`.
9. Admin guard token: interactive input or stdin.
10. Web console behavior: start on `session-entry` by default and open a
    browser only when the local environment is safe for it.

## Optional Collaboration Questions

1. Enable multi-PC collaboration now?
2. If yes, show a pairing guide rather than prefilled peer addresses.
3. Let each PC confirm the same project id and pairing code.
4. Save peer configuration only in machine-local config.

## Generated Local State

The wizard may write:

- local machine profile;
- machine settings;
- local CLUTCH project-memory root config under `CLUTCH_HOME/local/projects`;
- user workspace root pointer for ordinary project folders;
- artifact store pointer;
- admin guard hash;
- optional collab pairing config.
- Web console auto-start preference.

The wizard must not write public distribution templates with the user's private
answers.

The user-facing project root and CLUTCH's machine-local metadata root are
separate on purpose. A project workspace should stay a normal git repository;
CLUTCH memory, snapshot metadata, and restore evidence should live under the
CLUTCH home directory.

## Draft Command

The public distribution includes a draft non-interactive wizard command for
clean-home smoke tests and scripted installs:

```bash
printf '%s\n' '<local-admin-token>' \
  | python3 installer/clutch_first_run_wizard.py \
      --non-interactive \
      --admin-token-stdin \
      --clutch-home "$HOME/.clutch" \
      --projects-root "$HOME/clutch-projects" \
      --artifact-store "$HOME/clutch-artifacts" \
      --machine-display-name "My CLUTCH Workstation" \
      --online-sync-mode off \
      --github-setup skip \
      --write
```

The token is read from stdin or an interactive prompt and is stored only as a
local PBKDF2 hash. GitHub remotes and peer addresses remain empty until the user
configures them on that machine.

After setup, `session-entry` should start the Web console automatically. Browser
opening is safe-mode only: local desktop sessions may open the browser; SSH,
headless, and server-like contexts should receive a URL fallback.
