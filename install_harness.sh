#!/bin/bash
# install_harness.sh — convert a toolkit and install its bundle into a target project.
#
# Full pipeline: convert -> install -> verify.
#
# Usage: install_harness.sh <toolkit_dir> <target_dir> [rules_definitions.json] [--link]
#
# - Converts <toolkit_dir> via harness-converter into <toolkit_dir>/copy-content-to-prj-directory
#   (using the given rules_definitions.json, or the toolkit's default).
# - Installs the bundle into <target_dir>: by default COPIES it; with --link,
#   SYMLINKS each top-level bundle entry into the target instead (so the harness
#   always reflects the live toolkit without reinstall). Symlinks are
#   machine-local and should be gitignored in the target repo (see
#   software-developers-onboarding/docs/ai_harness_setup.md).
# - Force-replaces the generated harness dirs in <target_dir> (these are generated
#   files, never hand-edited). Merges .github/instructions/ into an existing
#   .github/ rather than clobbering other .github content.
# - Verifies every referenced path in the installed AGENTS.md resolves.
#
# Designed to be non-interactive and idempotent.
#
# Role: this is the high-level "do everything" entry point (convert + install +
# verify). For installing an already-built bundle only — with a choice of symlink
# vs copy and interactive conflict prompts — use the companion
# install_rules_in_project.sh instead.
#
# Portability: this script locates the harness-converter source relative to its
# own location (no hardcoded paths). Python is resolved as follows:
#   1. <repo>/venv/bin/python   (if a local venv exists)
#   2. python3 on PATH, with PYTHONPATH=<repo>/src
set -euo pipefail

# Resolve the directory containing this script (the repo root).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONVERTER_DIR="$SCRIPT_DIR"

# Resolve a working Python interpreter + converter invocation.
# Prefer a local venv; fall back to system python3 with PYTHONPATH pointing at src.
# PY_ENV holds any env-var assignments needed so 'harness_converter' is importable.
if [ -x "$CONVERTER_DIR/venv/bin/python" ]; then
  PY="$CONVERTER_DIR/venv/bin/python"
  PY_ENV=()
  CONVERTER=("$PY" -m harness_converter.cli)
else
  PY="$(command -v python3 || true)"
  if [ -z "$PY" ]; then
    echo "Error: python3 not found on PATH and no venv at $CONVERTER_DIR/venv." >&2
    exit 1
  fi
  PY_ENV=("PYTHONPATH=$CONVERTER_DIR/src")
  CONVERTER=("env" "${PY_ENV[@]}" "$PY" -m harness_converter.cli)
fi

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <toolkit_dir> <target_dir> [rules_definitions.json] [--link]" >&2
  echo "  --link  Install the bundle as symlinks into the target (default: copy)." >&2
  exit 1
fi

# Parse options (--link/-l may appear anywhere); collect positionals.
LINK_MODE=0
positionals=()
for arg in "$@"; do
  case "$arg" in
    --link|-l) LINK_MODE=1 ;;
    *) positionals+=("$arg") ;;
  esac
done
if [ "${#positionals[@]}" -lt 2 ]; then
  echo "Usage: $0 <toolkit_dir> <target_dir> [rules_definitions.json] [--link]" >&2
  exit 1
fi

TOOLKIT="$(cd "${positionals[0]}" && pwd)"
TARGET="$(cd "${positionals[1]}" && pwd)"
CONFIG="${positionals[2]:-$TOOLKIT/rules_definitions.json}"
# BUNDLE may be overridden (e.g. web toolkit's per-variant output dirs).
BUNDLE="${INSTALL_BUNDLE:-$TOOLKIT/copy-content-to-prj-directory}"

echo "==> Toolkit : $TOOLKIT"
echo "==> Target  : $TARGET"
echo "==> Config  : $CONFIG"
echo "==> Bundle  : $BUNDLE"
echo "==> Python  : $PY"
if [ "$LINK_MODE" -eq 1 ]; then
  echo "==> Mode    : symlink (--link)"
else
  echo "==> Mode    : copy (default)"
fi

# 1. Convert (skip if INSTALL_BUNDLE preset and bundle already exists — install-only mode)
if [ -z "${INSTALL_BUNDLE:-}" ]; then
  echo "==> Converting..."
  rm -rf "$TOOLKIT/cooked_rules_template" "$BUNDLE"
  "${CONVERTER[@]}" "$TOOLKIT" "$CONFIG" -o "$BUNDLE" 2>&1 \
    | sed -n '/Stage 2/,/completed successfully/p'
else
  echo "==> Converting... (skipped — using preset bundle $BUNDLE)"
fi

# 2. Clean generated harness artifacts in target (generated files; never hand-edited).
#    Remove both real dirs/files and any leftover symlinks from prior symlink installs.
#    CRITICAL: remove any symlink BEFORE operating on a path beneath it. If .github is a
#    symlink into the bundle, `rm -rf target/.github/instructions` would follow the link
#    and delete the bundle's own files. So: unlink .github first, then clean instructions.
#    NOTE: .github is NOT removed wholesale when real — a project may have real
#    .github/workflows. Only .github/instructions (the harness output) is removed.
GENERATED_DIRS=(.agent .claude .clinerules .gemini .kilo .kilocode .qwen .roo .windsurf)
for d in "${GENERATED_DIRS[@]}"; do
  if [ -L "$TARGET/$d" ] || [ -e "$TARGET/$d" ]; then rm -rf "$TARGET/$d"; fi
done
if [ -L "$TARGET/.github" ]; then
  rm -f "$TARGET/.github"                       # leftover symlink from a prior install
else
  rm -rf "$TARGET/.github/instructions"         # real .github — clear only the harness output
fi
rm -f "$TARGET/kilo.jsonc" "$TARGET/AGENTS.md"

# 3. Install bundle into target (non-interactive: we pre-cleaned conflicts).
#    --link: symlink each top-level entry into the target (default: copy).
#    .github is handled specially to preserve any real .github content
#    (e.g. .github/workflows): only .github/instructions is installed.
echo "==> Installing..."
cd "$BUNDLE"

# Install one top-level bundle entry into the target.
# Args: <item basename>. Uses LINK_MODE, $BUNDLE, $TARGET from the environment.
install_item() {
  local item="$1"
  local src="$BUNDLE/$item"
  if [ "$item" = ".github" ]; then
    mkdir -p "$TARGET/.github"
    if [ "$LINK_MODE" -eq 1 ]; then
      # Remove a stale instructions (dir or symlink) then link the bundle's dir.
      rm -rf "$TARGET/.github/instructions"
      if [ -d "$BUNDLE/.github/instructions" ]; then
        ln -sfn "$BUNDLE/.github/instructions" "$TARGET/.github/instructions"
      fi
      echo "  linked: .github/instructions"
    else
      mkdir -p "$TARGET/.github/instructions"
      if [ -d "$BUNDLE/.github/instructions" ]; then
        cp -R "$BUNDLE/.github/instructions/." "$TARGET/.github/instructions/"
      fi
      echo "  merged: .github/instructions"
    fi
    return
  fi
  if [ "$LINK_MODE" -eq 1 ]; then
    ln -sfn "$src" "$TARGET/$item"
    echo "  linked: $item"
  else
    cp -R "$item" "$TARGET/"
    echo "  copied: $item"
  fi
}
for item in *; do [ -e "$item" ] && install_item "$item"; done
for item in .*; do
  [ "$item" = "." ] && continue
  [ "$item" = ".." ] && continue
  [ -e "$item" ] && install_item "$item"
done

# 4. Verify referenced paths resolve (validate against target dir)
echo "==> Verifying references..."
env "${PY_ENV[@]}" "$PY" - "$TARGET/AGENTS.md" "$TARGET" <<'PYEOF'
import sys
from harness_converter.converter import extract_file_paths_from_content, validate_file_path
agents, base = sys.argv[1], sys.argv[2]
content = open(agents).read()
paths = extract_file_paths_from_content(content)
missing = []
for p in paths:
    cand = p
    ok, _ = validate_file_path(cand, base)
    if not ok and cand.endswith('.'):
        ok, _ = validate_file_path(cand.rstrip('.'), base)
    if not ok:
        missing.append(p)
print(f"  references: {len(paths)} | unresolved: {len(missing)}")
for p in missing:
    print(f"    MISSING: {p}")
sys.exit(1 if missing else 0)
PYEOF
echo "==> Done: $TARGET"
