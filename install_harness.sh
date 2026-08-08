#!/bin/bash
# install_harness.sh — convert a toolkit and install its harness bundle into a
# target project.
#
# Full pipeline: convert -> install -> verify.
#
# Usage: install_harness.sh <toolkit_dir> <target_dir> [rules_definitions.json] [--link]
#
# - Converts <toolkit_dir> via harness-converter into <toolkit_dir>/copy-content-to-prj-directory
#   (using the given rules_definitions.json, or the toolkit's default).
# - Installs the ENTIRE bundle into <target_dir> — that is, every top-level entry
#   produced by the converter: all eleven harness formats (.agent/, .claude/,
#   .clinerules/, .gemini/, .github/instructions/, .kilo/, .kilocode/, .qwen/,
#   .roo/, .windsurf/, AGENTS.md, kilo.jsonc) plus any other files the converter
#   copied through. By default it COPIES them; with --link it SYMLINKS each
#   top-level bundle entry into the target instead (so the harness always reflects
#   the live toolkit without reinstall). Symlinks are machine-local and should be
#   gitignored in the target repo.
# - Force-replaces the generated harness entries in <target_dir> (these are
#   generated files, never hand-edited). Merges .github/instructions/ into an
#   existing .github/ rather than clobbering other .github content.
# - Verifies every referenced path in the installed AGENTS.md resolves.
#
# Designed to be non-interactive and idempotent.
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

if [ ! -d "$BUNDLE" ]; then
  echo "Error: bundle not found at $BUNDLE" >&2
  exit 1
fi

# 2. Clean generated harness artifacts in target (generated files; never hand-edited).
#    Remove both real dirs/files and any leftover symlinks from prior symlink installs.
#    CRITICAL: remove any symlink BEFORE operating on a path beneath it. If .github is a
#    symlink into the bundle, `rm -rf target/.github/instructions` would follow the link
#    and delete the bundle's own files. So: unlink .github first, then clean instructions.
#    NOTE: .github is NOT removed wholesale when real — a project may have real
#    .github/workflows. Only .github/instructions (the harness output) is removed.
echo "==> Cleaning generated entries in target..."
GENERATED_TOP=(.agent .claude .clinerules .gemini .kilo .kilocode .qwen .roo .windsurf kilo.jsonc AGENTS.md)
for d in "${GENERATED_TOP[@]}"; do
  if [ -L "$TARGET/$d" ] || [ -e "$TARGET/$d" ]; then rm -rf "$TARGET/$d"; fi
done
if [ -L "$TARGET/.github" ]; then
  rm -f "$TARGET/.github"                       # leftover symlink from a prior install
else
  rm -rf "$TARGET/.github/instructions"         # real .github — clear only the harness output
fi

# 3. Install the ENTIRE bundle into the target.
#    Iterate every top-level bundle entry. Each entry is installed whole — either
#    copied or symlinked into the target. The ONE special case is .github: a project
#    may keep its own real .github/ (e.g. workflows), so only .github/instructions is
#    deployed and merged, never clobbering the rest of .github.
echo "==> Installing all bundle entries..."
cd "$BUNDLE"

install_count=0

# Install one top-level bundle entry into the target.
# Args: <entry basename>. Uses LINK_MODE, $BUNDLE, $TARGET from the environment.
# Handles ALL bundle entries; .github is the only entry that needs special handling
# (merge instructions only) — everything else is installed wholesale.
install_entry() {
  local entry="$1"
  local src="$BUNDLE/$entry"

  if [ "$entry" = ".github" ]; then
    # .github: preserve any existing real .github content; only deploy instructions.
    mkdir -p "$TARGET/.github"
    rm -rf "$TARGET/.github/instructions"
    if [ -d "$BUNDLE/.github/instructions" ]; then
      if [ "$LINK_MODE" -eq 1 ]; then
        ln -sfn "$BUNDLE/.github/instructions" "$TARGET/.github/instructions"
        echo "  linked: .github/instructions"
      else
        mkdir -p "$TARGET/.github/instructions"
        cp -R "$BUNDLE/.github/instructions/." "$TARGET/.github/instructions/"
        echo "  merged: .github/instructions"
      fi
      install_count=$((install_count + 1))
    fi
    return
  fi

  # All other entries (harness dirs + root files): install wholesale.
  if [ "$LINK_MODE" -eq 1 ]; then
    ln -sfn "$src" "$TARGET/$entry"
    echo "  linked: $entry"
  else
    cp -R "$entry" "$TARGET/"
    echo "  copied: $entry"
  fi
  install_count=$((install_count + 1))
}

# Iterate every top-level entry — regular and dotfiles — so nothing is skipped.
shopt -s dotglob nullglob
for entry in *; do
  [ -e "$entry" ] && install_entry "$entry"
done
shopt -u dotglob nullglob

echo "  installed $install_count top-level bundle entries"

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
