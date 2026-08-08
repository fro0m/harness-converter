# Harness Converter

A Python application that **converts AI coding rules and instruction files (harnesses) among different IDEs and AI agentic environments**. It takes a single source of rules authored as Cursor IDE `.mdc` files and re-emits them in the on-disk formats expected by each supported target — VS Code, Roo Code, Windsurf, Cline, Kilo Code, Gemini CLI, Google Antigravity, Qwen Code, Claude Code, OpenAI Codex, and ZCode.

Each target tool stores its "harness" (the rules/instructions that steer the AI agent or editor) in a different directory and file format. Harness Converter converts a single source of truth into the harness layout required by every supported environment, so you can keep one parameterized rule set and deploy it across all of them.

## Output Formats

Harness Converter transforms Cursor IDE rules MDC files into eleven different harness formats:

1. **VS Code instruction files** (.instructions.md) - Compatible with VS Code Copilot as described in the [VS Code Copilot Customization documentation](https://code.visualstudio.com/docs/copilot/copilot-customization#_instruction-files)
2. **Roo Code rules files** (.md) - Compatible with Roo Code custom instructions as described in the [Roo Code Custom Instructions documentation](https://docs.roocode.com/features/custom-instructions/)
3. **Windsurf rules files** (.md) - Compatible with Windsurf AI editor with YAML frontmatter format
4. **Cline rules files** (.md) - Compatible with Cline AI assistant as plain markdown files
5. **Kilo Code rules files** (.md) - Compatible with Kilo Code AI assistant as plain markdown files. Compatible with Kilo Code as described in the [Kilo Code Customization documentation](https://kilocode.ai/docs/advanced-usage/custom-rules)
6. **Gemini CLI rules files** (.md) - Compatible with Gemini CLI with import structure
7. **Google Antigravity rules files** (.md) - Compatible with Google Antigravity as described in the [Getting Started with Google Antigravity documentation](https://codelabs.developers.google.com/getting-started-google-antigravity#7)
8. **Qwen Code rules files** (.md) - Compatible with Qwen Code CLI (fork of Gemini CLI) as described in the [Qwen Code Configuration documentation](https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/)
9. **Claude Code rules files** (.md) - Compatible with Claude Code as described in the [Claude Code Memory documentation](https://code.claude.com/docs/en/memory)
10. **OpenAI Codex rules files** (.md) - Compatible with OpenAI Codex CLI as described in the [Codex AGENTS.md documentation](https://developers.openai.com/codex/guides/agents-md)
11. **ZCode rules files** (.md) - Compatible with ZCode as described in the [ZCode Agent documentation](https://zcode.z.ai/en/docs/agents)

#### Windsurf Format Details

Windsurf rules files are generated with the following YAML frontmatter:
```yaml
---
trigger: always_on
description: [extracted from original MDC file]
globs: **/*
---
```

#### Cline Format Details

Cline rules files are plain markdown files without frontmatter, similar to Roo Code format but stored in the `.clinerules/` directory. Cline automatically processes all markdown files in this directory.

#### Kilo Code Format Details

Kilo Code rules files are plain markdown files without frontmatter, similar to Roo Code format but stored in the `.kilocode/rules/` directory. Kilo Code automatically processes all markdown files in this directory.

#### Google Antigravity Format Details

Google Antigravity rules files are plain markdown files without frontmatter, stored in the `.agent/rules/` directory. Antigravity automatically processes all markdown files in this directory. Rules help guide the behavior of the agent.

#### Qwen Code Format Details

Qwen Code (fork of Gemini CLI) uses a `.qwen/` directory with a `QWEN.md` master file that imports individual rule files using the `@path/to/file.md` syntax. Individual rule files are plain markdown without frontmatter. Qwen Code loads these context files hierarchically as instructional context for the AI model.

#### Claude Code Format Details

Claude Code uses a `.claude/` directory with a `CLAUDE.md` master file that imports individual rule files using the `@path/to/file.md` syntax. Individual rule files are stored in `.claude/rules/` as plain markdown. Rules without a `paths` frontmatter field are loaded unconditionally at session start.

#### OpenAI Codex Format Details

OpenAI Codex uses a single `AGENTS.md` file at the project root containing all rules as plain markdown. Codex discovers `AGENTS.md` by walking from the project root to the current working directory, loading files in order. All rules are concatenated into a single file.

#### ZCode Format Details

ZCode uses a single `AGENTS.md` file at the project root as its always-on instruction/rules mechanism. The file is plain markdown with no frontmatter or schema, identical in content to the OpenAI Codex output, so the converter writes a single shared `AGENTS.md` rather than a duplicate. All rules are concatenated into this one file. ZCode also reads `~/.zcode/AGENTS.md` for user-level defaults (loaded before the workspace file); the converter only emits the workspace file.

### Output Directory Structure

When converting, the tool creates files in all eleven formats:

- **VS Code**: `.github/instructions/` directory with `.instructions.md` files
- **Roo Code**: `.roo/rules/` directory with `.md` files
- **Windsurf**: `.windsurf/rules/` directory with `.md` files
- **Cline**: `.clinerules/` directory with `.md` files
- **Kilo Code**: `.kilocode/rules/` directory with `.md` files
- **Gemini CLI**: `.gemini/` directory with `.md` files and a master `GEMINI.md` file
- **Google Antigravity**: `.agent/rules/` directory with `.md` files
- **Qwen Code**: `.qwen/` directory with `.md` files and a master `QWEN.md` file
- **Claude Code**: `.claude/rules/` directory with `.md` files and a master `.claude/CLAUDE.md` file
- **OpenAI Codex**: `AGENTS.md` file at the project root
- **ZCode**: `AGENTS.md` file at the project root (shared with Codex)

## Installation

This project uses Poetry for dependency management.

1.  **Install Poetry**:
    If you don't have Poetry installed, follow the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).

2.  **Install dependencies**:
    Navigate to the project root directory and run:
    ```bash
    poetry install
    ```

## Usage

After installation, you can run the script using `poetry run`.

### Basic usage with default configuration:

```bash
poetry run harness-converter path/to/project -o path/to/output
```

This will look for `rules_definitions.json` in the same directory as `raw-rules-template/` for variable substitution. The output directory (`-o`) is required.

### Specify a custom configuration file:

```bash
poetry run harness-converter path/to/project path/to/rules-description.json -o path/to/output
```

### Full example with explicit configuration and output directory:

```bash
poetry run harness-converter path/to/project path/to/rules-description.json -o path/to/output
```

The tool processes template files through a 4-stage pipeline:
1. **Template Variable Substitution** - Replace `{variable}` placeholders with values from the JSON configuration file
2. **Path and File Validation** - Validate all file paths and references in processed rules
3. **Format Conversion** - Convert to VS Code, Roo Code, Windsurf, Cline, Kilo Code, Gemini, Antigravity, Qwen Code, Claude Code, and Codex formats
4. **Deployment** - Place files in correct directory structure for each tool

When processing, the tool will:
- Convert `.mdc` template files to VS Code instruction files (`.instructions.md`) in `.github/instructions/`, Roo Code rules files (`.md`) in `.roo/rules/`, Windsurf rules files (`.md`) in `.windsurf/rules/`, Cline rules files (`.md`) in `.clinerules/`, Kilo Code rules files (`.md`) in `.kilocode/rules/`, Gemini CLI rules files (`.md`) in `.gemini/`, Google Antigravity rules files (`.md`) in `.agent/rules/`, Qwen Code rules files (`.md`) in `.qwen/`, Claude Code rules files (`.md`) in `.claude/rules/`, and OpenAI Codex rules (`.md`) in `AGENTS.md`.
- For Gemini CLI, it will create a `.gemini/` directory in the project for individual rules and a `GEMINI.md` in the same directory to import them.
- For Qwen Code, it will create a `.qwen/` directory with individual rules and a `QWEN.md` master file to import them.
- For Claude Code, it will create a `.claude/rules/` directory with individual rules and a `.claude/CLAUDE.md` master file to import them.
- For OpenAI Codex, it will create a single `AGENTS.md` at the project root with all rules concatenated.
- Copy all non-template files from the source directory to the output directory (if output directory is specified), preserving the directory structure.
- Maintain the directory structure inside each tool's rules directories.

### Help

```bash
poetry run harness-converter --help
```

## Installing a Converted Harness into a Project

A single installer script, `install_harness.sh`, is provided. It is portable (no hardcoded paths) and resolves its own location, so it works from any clone on any Ubuntu machine.

`install_harness.sh` runs the full pipeline: **convert → install → verify**.

```bash
./install_harness.sh <toolkit_dir> <target_dir> [rules_definitions.json] [--link]
```

It installs the **entire** converted bundle into `<target_dir>` — every top-level entry the converter produces, i.e. all eleven harness formats and any pass-through files:

- `.agent/`, `.claude/`, `.clinerules/`, `.gemini/`, `.kilo/`, `.kilocode/`, `.qwen/`, `.roo/`, `.windsurf/`
- `.github/instructions/`
- `AGENTS.md`, `kilo.jsonc`

Behavior:

- Converts `<toolkit_dir>` (which must contain `raw-rules-template/`) into `<toolkit_dir>/copy-content-to-prj-directory/` using the given config, or `<toolkit_dir>/rules_definitions.json` by default.
- By default **copies** every bundle entry into `<target_dir>`. Pass `--link` (or `-l`) to **symlink** each top-level entry instead, so the target always reflects the live toolkit without reinstalling. (Symlinks are machine-local and should be gitignored in the target repo.)
- Force-replaces the generated harness entries in `<target_dir>` (these are generated files, never hand-edited). `.github/instructions/` is **merged** into an existing real `.github/` rather than clobbering other `.github` content (e.g. workflows) — this is the only entry that needs special handling; every other entry is installed wholesale.
- Verifies every path referenced in the installed `AGENTS.md` resolves against the target.
- Non-interactive and idempotent: re-running it cleanly updates the target.

```bash
# Typical use (convert + copy all harness formats in + verify)
./install_harness.sh /path/to/toolkit /path/to/target/project

# With an explicit config
./install_harness.sh /path/to/toolkit /path/to/target/project /path/to/rules_definitions.json

# Symlink the harness into the target instead of copying
./install_harness.sh /path/to/toolkit /path/to/target/project --link

# Install a pre-built bundle only (skip conversion)
INSTALL_BUNDLE=/path/to/bundle ./install_harness.sh /path/to/toolkit /path/to/target/project
```

`INSTALL_BUNDLE=<path>` overrides the bundle source and skips conversion if the bundle already exists — useful for per-variant output dirs.

## Development

To set up the development environment:

1.  **Install Poetry** (if not already installed, see Installation section).
2.  **Clone the repository** (if you haven't already).
3.  **Install dependencies**:
    ```bash
    poetry install
    ```
4.  **Activate the virtual environment**:
    Poetry creates a virtual environment for the project. You can activate it by running:
    ```bash
    poetry shell
    ```
    Alternatively, you can run commands within the environment using `poetry run <command>`.

## Alternative Installation (using pip)

If you prefer not to use Poetry, you can still install the package using pip, but Poetry is the recommended method for managing this project.

```bash
# Ensure you have pip installed
# Clone the repository
pip install -e .
```
To run the script if installed with pip:
```bash
harness-converter path/to/project -o path/to/output
```
