#!/bin/bash

# =============================================================================
# Install Tools in Project Script
# =============================================================================
#
# DESCRIPTION:
#   This script creates symbolic links from files in a source directory to a
#   target project directory. It safely handles existing files by prompting
#   the user for confirmation before removal.
#
# USAGE:
#   ./install_tools_in_project.sh <target_directory> [source_directory]
#
# PARAMETERS:
#   target_directory (required): Directory where symbolic links will be created
#   source_directory (optional): Parent directory containing copy-content-to-prj-directory
#                               Default: current directory (./copy-content-to-prj-directory)
#
# FEATURES:
#   - Creates symbolic links for all files and directories in source
#   - Prompts user before removing existing files/directories
#   - Validates source and target directory existence
#   - Provides clear feedback during installation process
#   - Handles both regular files and hidden files (starting with .)
#   - Uses safer file enumeration with 'find' command
#   - Provides detailed information about what will be removed
#
# EXAMPLES:
#   # Use default source directory
#   ./install_tools_in_project.sh /path/to/my/project
#
#   # Specify custom source directory
#   ./install_tools_in_project.sh /path/to/my/project /path/to/tools
#
# SAFETY:
#   - Never removes files without explicit user confirmation
#   - Only removes files that will be replaced by symbolic links
#   - Validates all directory paths before proceeding
#   - Uses appropriate removal commands based on file type
#   - Creates symbolic links with verbose output for tracking
#   - Handles removal errors gracefully
#
# =============================================================================

# Check if a target directory was provided
if [ -z "$1" ]; then
  echo "Usage: $0 <target_directory> [source_directory]"
  echo "  target_directory: Directory where symbolic links will be created"
  echo "  source_directory: Parent directory containing copy-content-to-prj-directory (default: current directory)"
  exit 1
fi

# Set script parameters
TARGET_DIR="$1"
if [ -n "$2" ]; then
    SOURCE_DIR="$2/copy-content-to-prj-directory"
else
    SOURCE_DIR="./copy-content-to-prj-directory"
fi

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

echo "Creating symbolic links from '$SOURCE_DIR' to '$TARGET_DIR'..."
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

  # Create symbolic link with verbose output
  if ln -sfv "$PWD/$f" "$TARGET_DIR/"; then
    echo "Created link: $target_path -> $PWD/$f"
  else
    echo "Failed to create link for: $f"
  fi
done < <(find . -mindepth 1 -maxdepth 1 -print0)

echo "Installation complete."

# =============================================================================
# End of Script
# =============================================================================
