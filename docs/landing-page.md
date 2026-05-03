# Landing Page Deployment

CLUTCH ships a static landing page under `site/index.html`. It is designed to
explain the system before installation: top-down project routing, multi-PC
collab, visible monitoring, backup and reproducibility, away development,
artifact boundaries, and the first-use verification path.

## Local Preview

Preview the page from an exported release tree:

```bash
cd clutch-public-<version>
make landing-smoke
python3 -m http.server 8080 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8080/site/
```

The page must load `site/styles.css`, `assets/clutch.png`,
`assets/clutchmainimage.png`, and
`assets/clutch-ecosystem-architecture.svg` from the same release tree. The
architecture graphic should show project binding, session entry, collab
transport, local snapshots, backups, task alarms, away development, agent PCs,
and local AI/robot/sensor resources without private lab details. The SVG must
embed the center logo image directly as a `data:image/png;base64,` URI instead
of referencing `clutchmainimage.png` as a nested external image; otherwise some
browsers render the center as a blank white circle when the SVG is loaded
through an HTML `<img>` tag. The smoke also fetches the key linked public docs
from the page: Prompt Cookbook, First-Use Acceptance Runbook, Verification
Matrix, and FAQ. It must not depend on external scripts, private lab URLs,
private machine names, private IP addresses, or credentials.

The visual policy is intentionally strict: the hero H1 is the only landing page
text that uses the sans-serif face. Every other heading, control, caption, and
descriptive line inherits the serif face so the page keeps the restrained
research-lab tone requested for public launch.

## GitHub Pages

After the repository is ready to become public, GitHub Pages serves the same
static files through `.github/workflows/pages.yml`. The workflow builds a Pages
artifact from `site/index.html`, `site/styles.css`, `assets/`, and the linked
public docs, then publishes it at the repository Pages root:

```text
https://<github-owner>.github.io/<repo-name>/
```

Keep the repository private until the operator explicitly approves changing
repository visibility. Publishing the landing page before that approval is not
part of the CLUTCH public release process.

## Release Checks

Before treating the page as publishable:

- run `tools/clutch_public_landing_smoke.py --root . --json`;
- run `tools/clutch_public_release_gate.py --root . --json`;
- run `tools/clutch_distribution_scan.py . --json`;
- confirm `site/index.html` links to the intended public GitHub repository;
- confirm the landing smoke fetches the key linked public docs;
- confirm `assets/clutch.png` is present and visually appropriate;
- confirm `assets/clutchmainimage.png` is present and embedded inside
  `assets/clutch-ecosystem-architecture.svg` as a `data:image/png;base64,`
  center logo, not referenced as a nested external image;
- confirm only the hero H1 uses the sans-serif face, while all other text uses
  the serif face;
- confirm the page explains clean first run, local smoke checks, and artifact
  boundaries from a user perspective;
- confirm the Pages workflow deploys the `site/` landing page to the official
  root URL after the repository becomes public;
- keep the release zip, checksum file, manifest, and release notes together.

The landing page is marketing-facing, but it is also release evidence. If it
claims a CLUTCH capability, the README and Help flow should explain how a user
can actually reach that capability after first-run setup.
