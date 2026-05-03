# Landing Page Deployment

CLUTCH ships a static landing page under `site/index.html`. It is designed to
explain the system before installation: multi-PC collab, visible monitoring,
backup and reproducibility, away development, artifact hygiene, and the
private-first publication boundary.

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

The page must load `site/styles.css` and `assets/clutch.png` from the same
release tree. It must not depend on external scripts, private lab URLs, private
machine names, private IP addresses, or credentials.

The visual policy is intentionally strict: the hero H1 is the only landing page
text that uses the sans-serif face. Every other heading, control, caption, and
descriptive line inherits the serif face so the page keeps the restrained
research-lab tone requested for public launch.

## GitHub Pages

After the repository is ready to become public, GitHub Pages can serve the same
static files. Use the repository root as the Pages source and set the public
landing URL to:

```text
https://<github-owner>.github.io/<repo-name>/site/
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
- confirm `assets/clutch.png` is present and visually appropriate;
- confirm only the hero H1 uses the sans-serif face, while all other text uses
  the serif face;
- confirm the page explains clean install smoke, artifact hygiene, and
  private-first publication;
- keep the release zip, checksum file, manifest, and release notes together.

The landing page is marketing-facing, but it is also release evidence. If it
claims a CLUTCH capability, the README and Help flow should explain how a user
can actually reach that capability after first-run setup.
