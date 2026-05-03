# Away Development

Away development lets an operator approve a bounded work window before leaving
Codex to continue. It is useful for long test runs, documentation cleanup,
release preparation, and low-risk stabilization.

An away plan should contain:

- objective;
- allowed scope;
- forbidden actions;
- stop conditions;
- verification requirements;
- checkpoint cadence;
- expiry time.

## Good Away Plan

```text
Objective: polish the public README and installer docs.
Allowed: distribution docs, installer smoke tests, scanner tests.
Forbidden: changing hardware, credentials, network settings, sudo, public repo visibility.
Stop if: scanner finds private data, install smoke fails, or requested work touches private state.
Verify: unit tests, distribution scan, clean-home first-run smoke.
Expires: tonight at 08:00 local time.
```

## Poor Away Plan

```text
Keep improving everything.
```

That is too broad. CLUTCH should treat broad or expired plans as inactive and
ask for a fresh operator decision.

## Public Safety Rule

Away plans do not authorize:

- live robot movement;
- hardware recovery;
- sudo or system service changes;
- credential changes;
- network reconfiguration;
- destructive restore;
- making a private repo public.
