# Release Artifacts

CLUTCH public releases are distributed as a small artifact set, not just a zip
file. Keep these files together when reviewing or archiving a release candidate.

## Files

- `clutch-public-<version>.zip`: installable public distribution.
- `clutch-public-<version>.sha256`: checksum for the release zip.
- `clutch-public-<version>.manifest.json`: machine-readable release evidence.
- `clutch-public-<version>.release-notes.md`: human-readable GitHub release
  body draft.

## Verify The Zip

From the folder that contains the release artifacts:

```bash
sha256sum -c clutch-public-<version>.sha256
```

The command should report `OK`. If it does not, do not install or publish that
artifact set.

## Read The Manifest

The manifest records:

- release zip file name and SHA256;
- checksum file name;
- release notes file name;
- export finding count;
- public release gate status;
- visibility review status and
  `remote_visibility_change_performed=false`;
- scanner finding count;
- publication boundary.

The package command JSON also reports `manifest_sha256`. The manifest cannot
contain its own final hash without changing itself, so keep the package command
JSON or your release-build log when you need a complete audit trail.

## Publication Boundary

`ready_for_private_release_upload` does not mean ready for public visibility.
Before changing a repository from private to public, run the public release
checklist, confirm scanner and gate findings are zero, complete install and Web
console smokes, review release notes for private data, and get explicit operator approval.
