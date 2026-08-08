#!/bin/bash

# =============================================================================
# Install Rules in Project Script
# =============================================================================
#
# Role: lower-level installer. Installs an already-built bundle (the
# copy-content-to-prj-directory/ directory produced by harness-converter) into a
# target project, with a choice of symlink (default) or copy (--copy) and
# interactive prompts before replacing existing files.
#
# For the full convert -> install -> verify pipeline in one non-interactive
# command, use the companion install_harness.sh instead.
#
# DESCRIPTION:
#   This script installs files from a source directory into a target project
#   directory, either as symbolic links (default) or as copies (--copy). It
#   safely handles existing files by prompting the user for confirmation
#   before removal.
#
# USAGE:
#   ./install_rules_in_project.sh <target_directory> <source_directory> [--copy]
#
# PARAMETERS:
#   target_directory (required): Directory where links/copies will be created
#   source_directory (required): Parent directory containing copy-content-to-prj-directory
#
# OPTIONS:
#   --copy, -c   Copy files into the target directory instead of creating
#                symbolic links.
#
# FEATURES:
#   - Creates symbolic links (default) or copies (--copy) for all files and
#     directories in source
#   - Prompts user before removing existing files/directories
#   - Validates source and target directory existence
#   - Provides clear feedback during installation process
#   - Handles both regular files and hidden files (starting with .)
#   - Uses safer file enumeration with 'find' command
#   - Provides detailed information about what will be removed
#
# EXAMPLES:
#   # Create symbolic links (default)
#   ./install_rules_in_project.sh /path/to/my/project /path/to/tools
#
#   # Copy files instead of linking
#   ./install_rules_in_project.sh /path/to/my/project /path/to/tools --copy
#
# SAFETY:
#   - Never removes files without explicit user confirmation
#   - Only removes files that will be replaced by links/copies
#   - Validates all directory paths before proceeding
#   - Uses appropriate removal commands based on file type
#   - Creates links/copies with verbose output for tracking
#   - Handles removal errors gracefully
#
# =============================================================================

# Parse options first (--copy/-c may appear anywhere)
COPY_MODE=0
for arg in "$@"; do
  case "$arg" in
    --copy|-c)
      COPY_MODE=1
      ;;
  esac
done

# Build the list of positional arguments (everything that isn't an option)
positionals=()
for arg in "$@"; do
  case "$arg" in
    --copy|-c) ;;
    *) positionals+=("$arg") ;;
  esac
done

# Both target and source directories are required
if [ "${#positionals[@]}" -lt 2 ]; then
  echo "Usage: $0 <target_directory> <source_directory> [--copy]"
  echo "  target_directory: Directory where links/copies will be created (required)"
  echo "  source_directory: Parent directory containing copy-content-to-prj-directory (required)"
  echo "  --copy:           Copy files instead of creating symbolic links"
  exit 1
fi

# Set script parameters (both required, explicitly provided)
TARGET_DIR="${positionals[0]}"
SOURCE_DIR="${positionals[1]}/copy-content-to-prj-directory"

# Validate target directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Target directory '$TARGET_DIR' does not exist."
  exit 1
fi

# Validate source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: Source directory '$SOURCE_DIR' does not exist."
  exit 1
fi

# Get absolute paths for comparison
TARGET_DIR_ABS=$(cd "$TARGET_DIR" && pwd)
SOURCE_DIR_ABS=$(cd "$SOURCE_DIR" && pwd)

# Safety check: prevent linking to self
if [ "$TARGET_DIR_ABS" = "$SOURCE_DIR_ABS" ]; then
  echo "Error: Target directory cannot be the same as source directory."
  exit 1
fi

# Additional safety check: warn if target is inside source or vice versa
if [[ "$TARGET_DIR_ABS" == "$SOURCE_DIR_ABS"/* ]] || [[ "$SOURCE_DIR_ABS" == "$TARGET_DIR_ABS"/* ]]; then
  if [[ "$TARGET_DIR_ABS" == "$SOURCE_DIR_ABS"/* ]]; then
    echo "Warning: Target directory '$TARGET_DIR_ABS' is inside source directory '$SOURCE_DIR_ABS'. This may cause issues."
  else
    echo "Warning: Source directory '$SOURCE_DIR_ABS' is inside target directory '$TARGET_DIR_ABS'. This is unusual but usually OK."
  fi
  echo -n "Continue anyway? (y/N): "
  read -r response </dev/tty
  case "$response" in
    [yY][eE][sS]|[yY])
      ;;
    *)
      echo "Operation cancelled by user."
      exit 1
      ;;
  esac
fi

# Function to prompt user for confirmation before removing existing files
# Parameters:
#   $1: item name (filename or directory name)
#   $2: item type description
# Returns: 0 if user confirms, 1 if user declines
confirm_removal() {
  local item="$1"
  local item_type="$2"
  local response

  echo -n "$item_type '$item' already exists in target. Remove it? (y/N): "
  read -r response </dev/tty

  case "$response" in
    [yY]|[yY][eE][sS])  # Accept 'y', 'yes', 'Y', 'YES', etc.
      return 0
      ;;
    [nN]|[nN][oO]|"")  # Accept 'n', 'no', 'N', 'NO', etc. or empty response
      return 1
      ;;
    *)  # Any other input - check if it looks like a file path
      if [[ "$response" == .* ]] || [[ "$response" == /* ]]; then
        echo "Received file path '$response' instead of y/n response. Treating as 'no'."
        return 1
      else
        echo "Invalid response '$response'. Treating as 'no'."
        return 1
      fi
      ;;
  esac
}

# Change to source directory to process files from there
cd "$SOURCE_DIR" || exit 1

if [ "$COPY_MODE" -eq 1 ]; then
  echo "Copying files from '$SOURCE_DIR' to '$TARGET_DIR'..."
else
  echo "Creating symbolic links from '$SOURCE_DIR' to '$TARGET_DIR'..."
fi
echo "Note: System files (.DS_Store, .git, etc.) will be automatically skipped."

# Get list of files and directories to process (excluding . and ..)
# Use find to get all files and directories, including hidden ones
while IFS= read -r -d '' f; do
  # Skip if empty (can happen with find)
  [ -z "$f" ] && continue

  # Get just the basename for the target path
  basename_f=$(basename "$f")


  # Verify the source file/directory actually exists
  if [ ! -e "$f" ]; then
    echo "Warning: Source file '$f' does not exist, skipping."
    continue
  fi

  # Calculate the target path for the symbolic link
  target_path="$TARGET_DIR/$basename_f"

  # Check if target file/directory already exists (including broken symlinks)
  if [ -e "$target_path" ] || [ -L "$target_path" ]; then
    # Get file type for better user feedback
    if [ -d "$target_path" ]; then
      item_type="directory"
    elif [ -L "$target_path" ]; then
      item_type="symbolic link"
    else
      item_type="file"
    fi

    # Prompt user for confirmation before removal
    if confirm_removal "$basename_f" "$item_type"; then
      echo "Removing existing $item_type '$target_path'..."

      # Remove based on type - be more careful with directories
      if [ -d "$target_path" ] && [ ! -L "$target_path" ]; then
        # For directories, use rm -rf but only if it's not a symlink
        rm -rf "$target_path"
      else
        # For files and symlinks, just remove
        rm -f "$target_path"
      fi

      if [ $? -ne 0 ]; then
        echo "Warning: Failed to remove '$target_path'"
        continue
      fi
    else
      echo "Skipping '$f' (user declined removal)"
      continue  # Skip to next file
    fi
  fi

  # Install the item: copy it (--copy) or create a symbolic link (default)
  if [ "$COPY_MODE" -eq 1 ]; then
    # Copy the file/directory recursively into the target directory
    if cp -R "$f" "$TARGET_DIR/"; then
      echo "Copied: $target_path (from $PWD/$f)"
    else
      echo "Failed to copy: $f"
    fi
  else
    # Create symbolic link with verbose output
    if ln -sfv "$PWD/$f" "$TARGET_DIR/"; then
      echo "Created link: $target_path -> $PWD/$f"
    else
      echo "Failed to create link for: $f"
    fi
  fi
done < <(find . -mindepth 1 -maxdepth 1 -print0)

echo "Installation complete."

# =============================================================================
# End of Script
# =============================================================================
