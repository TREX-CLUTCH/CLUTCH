# CLUTCH Collab Transport

CLUTCH collab transport is the project-local communication layer for two or
more Codex machines. It is intentionally separate from project source code: a
transport can carry requests, notes, results, and monitor evidence without
becoming the authority for the project's implementation.

The public distribution ships a safe file-based transport helper. It does not
contain preset hostnames, IP addresses, SSH aliases, accounts, or lab-specific
machine ids.

## Recommended Shape

1. Install CLUTCH on each PC.
2. Run the first-run wizard on each PC.
3. Pick one shared folder for collab messages. A directly wired LAN share is
   the simplest reliable option for lab machines.
4. Use the same project id on every PC.
5. Start one machine as `main` and the other as `worker`.
6. Keep the Web Monitor tab or terminal monitor visible while work is active.

The shared folder can be provided by NFS, SMB, SSHFS, Syncthing, rsync, or any
other user-controlled transport. CLUTCH does not ship with peer addresses. The
operator chooses the transport and records it in local machine config.

## File Transport Smoke

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /tmp/clutch-collab \
  --project-id demo-project \
  --machine-id main-laptop \
  --role main

python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /tmp/clutch-collab \
  --project-id demo-project \
  --machine-id gpu-worker \
  --role worker

python3 collab_transport/scripts/clutch_collab_file_transport.py request \
  --shared-root /tmp/clutch-collab \
  --project-id demo-project \
  --from-machine main-laptop \
  --to-machine gpu-worker \
  --kind inspect \
  --summary "Check the training logs" \
  --body "Report loss trend and OOM risk."

python3 collab_transport/scripts/clutch_collab_file_transport.py monitor \
  --shared-root /tmp/clutch-collab \
  --project-id demo-project \
  --once
```

## Safety Boundary

Collab transport moves text instructions and status evidence. It does not
authorize hardware motion, sudo actions, network reconfiguration, credential
changes, or destructive restore work.
