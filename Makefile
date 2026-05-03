PYTHON ?= python3
ROOT ?= .
PORT ?= 8899

.PHONY: help verify scan gate visibility-review landing-smoke web-smoke collab-smoke install-smoke serve-landing

help:
	@printf '%s\n' "CLUTCH public targets:"
	@printf '%s\n' "  make verify         Run scanner, release gate, visibility review, and smoke tests."
	@printf '%s\n' "  make scan           Run private-data scanner only."
	@printf '%s\n' "  make gate           Run public release gate only."
	@printf '%s\n' "  make visibility-review  Run read-only final public visibility review."
	@printf '%s\n' "  make landing-smoke  Serve and fetch the landing page, CSS, and image."
	@printf '%s\n' "  make web-smoke      Run clean first-run Web console smoke."
	@printf '%s\n' "  make collab-smoke   Run file-based multi-PC collab transport smoke."
	@printf '%s\n' "  make install-smoke  Run clean install and first-project smoke."
	@printf '%s\n' "  make serve-landing  Serve site/index.html on 127.0.0.1:$(PORT)."

verify:
	@$(PYTHON) tools/clutch_public_verify.py --root $(ROOT) --json

scan:
	@$(PYTHON) tools/clutch_distribution_scan.py $(ROOT) --json

gate:
	@$(PYTHON) tools/clutch_public_release_gate.py --root $(ROOT) --json

visibility-review:
	@$(PYTHON) tools/clutch_public_visibility_review.py --root $(ROOT) --json

landing-smoke:
	@$(PYTHON) tools/clutch_public_landing_smoke.py --root $(ROOT) --json

web-smoke:
	@$(PYTHON) tools/clutch_public_web_smoke.py --root $(ROOT) --json

collab-smoke:
	@$(PYTHON) tools/clutch_public_collab_smoke.py --root $(ROOT) --json

install-smoke:
	@$(PYTHON) tools/clutch_public_install_smoke.py --root $(ROOT) --json

serve-landing:
	@$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1
