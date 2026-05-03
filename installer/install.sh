#!/usr/bin/env bash
set -eu

usage() {
  cat <<'EOF'
Usage: installer/install.sh [--prefix PATH] [--force]

Installs this CLUTCH distribution into:
  $CLUTCH_HOME/foundation/current

Default CLUTCH_HOME is "$HOME/.clutch".

This installer does not use sudo, does not configure GitHub credentials, and
does not create peer network links. Run the first-run wizard after installation.
EOF
}

PREFIX="${CLUTCH_HOME:-$HOME/.clutch}"
FORCE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --prefix)
      shift
      [ "$#" -gt 0 ] || { echo "--prefix requires a path" >&2; exit 2; }
      PREFIX="$1"
      ;;
    --force)
      FORCE=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TARGET_DIR="$PREFIX/foundation/current"

if [ -e "$TARGET_DIR" ] && [ "$FORCE" -ne 1 ]; then
  echo "Refusing to overwrite existing install: $TARGET_DIR" >&2
  echo "Use --force only after backing up local CLUTCH state." >&2
  exit 1
fi

mkdir -p "$(dirname -- "$TARGET_DIR")"
if [ -e "$TARGET_DIR" ]; then
  rm -rf "$TARGET_DIR"
fi

mkdir -p "$TARGET_DIR"
tar \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='.mypy_cache' \
  --exclude='.ruff_cache' \
  --exclude='node_modules' \
  --exclude='.coverage' \
  --exclude='htmlcov' \
  --exclude='build' \
  --exclude='dist' \
  --exclude='*.egg-info' \
  --exclude='releases' \
  --exclude='restore-smoke' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='.DS_Store' \
  --exclude='*.log' \
  --exclude='*.tmp' \
  -C "$SOURCE_DIR" -cf - . \
  | tar -C "$TARGET_DIR" -xf -

chmod +x "$TARGET_DIR/installer/install.sh" 2>/dev/null || true
chmod +x "$TARGET_DIR/installer/clutch_first_run_wizard.py" 2>/dev/null || true
chmod +x "$TARGET_DIR/installer/clutch_doctor.py" 2>/dev/null || true
chmod +x "$TARGET_DIR/scripts/clutch_ctl.py" 2>/dev/null || true
chmod +x "$TARGET_DIR/scripts/clutch_web.py" 2>/dev/null || true

cat <<EOF
CLUTCH installed at:
  $TARGET_DIR

Next:
EOF
printf '  export CLUTCH_HOME=%q\n' "$PREFIX"
cat <<'EOF'
  cd "$CLUTCH_HOME/foundation/current"
  python3 installer/clutch_first_run_wizard.py
  python3 installer/clutch_doctor.py
  python3 scripts/clutch_ctl.py session-entry
EOF
