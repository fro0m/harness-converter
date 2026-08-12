
# Product Requirements Document: Harness Converter

## 1. Introduction

*   **Purpose**: The Harness Converter is a multi-stage command-line tool that converts AI coding rules and instruction files (harnesses) among different IDEs and AI agentic environments. It processes template-based rule files through variable substitution, validation, and format conversion to generate ready-to-use rules for different AI-powered code editors and assistants. This ensures that a single source of truth for coding rules and instructions can be parameterized and deployed across multiple development environments.
*   **Target Audience**: Developers and teams who use multiple AI coding tools (like VS Code Copilot, Roo Code, Windsurf, and Cline) and want to maintain a consistent, parameterized set of custom instructions across all of them.
*   **Scope**: This document covers the 4-stage processing pipeline of the Harness Converter: template variable substitution, validation, format conversion, and deployment to target directories.

## 2. Goals and Objectives

*   **Business Goals**:
    *   Improve developer efficiency by allowing them to manage parameterized rule templates for multiple tools.
    *   Encourage the adoption of standardized coding practices within development teams by making it easy to customize, share and deploy rules.
    *   Reduce configuration drift by using a single source of truth with variable substitution.
*   **Product Goals**:
    *   Provide a reliable 4-stage processing pipeline for rule template conversion.
    *   Support template variable substitution with comprehensive error handling.
    *   Validate file paths and references in processed rules.
    *   Support the most common AI coding assistants with proper format conversion.
    *   Ensure that the converted files are placed in the correct directory structure for each respective tool.

## 3. User Personas and Stories

*   **User Persona: "Alex the Polyglot Developer"**
    *   **Goals**: To use the best AI tool for the task at hand while maintaining consistent, project-specific custom instructions without manual duplication and formatting.
    *   **Motivations**: Efficiency, consistency, parameterization for different projects, and a desire to stay on the cutting edge of AI development tools.
    *   **Pain Points**: Manually maintaining the same set of rules in different formats for VS Code, Roo Code, and other tools is time-consuming and error-prone. Rules need to be customized for different projects but share common patterns.
*   **User Stories**:
    *   "As Alex, I want to define rule templates with variables so that I can customize them for different projects without duplicating content."
    *   "As Alex, I want the converter to validate that all file paths and references in my rules are correct before deploying them."
    *   "As Alex, I want clear error messages when variables are missing from my configuration so that I can fix issues quickly."
    *   "As Alex, I want to convert an entire directory of rule templates so that I can set up a new project with all my standard rules in one command."
    *   "As Alex, I want the converter to automatically place the output files in the correct locations for each tool so that I don't have to move them manually."

## 4. Architecture and Processing Stages

The Harness Converter follows a 4-stage processing pipeline:

### Stage 1: Template Variable Substitution
*   **Input**: `raw-rules-template/` directory containing template files with `{variable}` placeholders
*   **Process**: 
    *   Accept path to `rules-description.json` file containing variable definitions
    *   Parse all template files and substitute `{variable}` placeholders with values from JSON
    *   Validate that all variables have corresponding values in the JSON file
    *   If any variables are missing values: show error, cancel operation, and revert changes
*   **Output**: `cooked_rules_template/` directory with fully substituted files

### Stage 2: Path and File Validation
*   **Input**: `cooked_rules_template/` directory
*   **Process**:
    *   Parse all files in the cooked rules template directory
    *   Extract and identify file paths and directory references
    *   Validate that all found paths exist and are accessible
    *   Report validation errors to standard output
*   **Output**: Validation report with any path/file issues

### Stage 3: Format Conversion
*   **Input**: `cooked_rules_template/` directory (follows Cursor IDE MDC source format)
*   **Process**: Convert files to target formats for different AI tools and agentic environments
*   **Output**: Multiple format-specific directories with converted rules

### Stage 4: Deployment
*   **Input**: Source directory containing `raw-rules-template/`
*   **Process**: 
    *   The output directory must be specified explicitly (no default); converted rules are written to the given output directory
    *   Place files in appropriate directory structure for each target tool
*   **Output**: Ready-to-deploy rule files in correct locations

## 5. Features and Functionality

### Core Processing Features
*   **Template Variable Substitution**:
    *   Parse JSON configuration file for variable definitions
    *   Substitute `{variable}` placeholders in template files
    *   Comprehensive error handling for missing variables
*   **Path Validation**:
    *   Extract file and directory paths from processed rules
    *   Validate existence and accessibility of referenced paths
    *   Detailed error reporting for invalid references
*   **Format Conversion**:
    *   Convert from Cursor IDE MDC source format to VS Code instruction files (`.instructions.md`)
    *   Convert to Roo Code rules files (`.md`)
    *   Convert to Windsurf rules files (`.md` with YAML frontmatter)
    *   Convert to Cline rules files (`.md`)
    *   Convert to Kilo Code rules files (`.md`)
    *   Convert to Gemini CLI rules files (`.md`)
    *   Convert to Google Antigravity, Qwen Code, Claude Code, OpenAI Codex, and ZCode formats
    *   Emit the Codex `.rules` command-policy scaffold (`.codex/rules/default.rules`)
*   **Directory Management**:
    *   Process entire directory trees recursively
    *   Maintain directory structure in output
    *   Smart output directory selection
    *   Copy non-template files to output directories

### Command Line Interface
*   Accept source directory path (containing `raw-rules-template/`)
*   Accept path to `rules-description.json` configuration file (optional - defaults to `rules_definitions.json` in same directory as `raw-rules-template/`)
*   Output directory specification (required; both source and output must be specified explicitly)
*   Help and usage information
### Feature Prioritization (MoSCoW)
*   **Must-have**: 
    *   4-stage processing pipeline
    *   Template variable substitution with JSON configuration
    *   Missing variable error handling with operation cancellation
    *   Path validation and error reporting
    *   Conversion to all eleven target formats
    *   Codex `.rules` command-policy scaffold
    *   Smart output directory management
*   **Should-have**: 
    *   Recursive directory processing
    *   Correct output directory structure for each tool
*   **Could-have**: 
    *   Configuration file validation
*   **Won't-have**: 
    *   A graphical user interface (GUI)
    *   Real-time file watching

## 6. Non-Functional Requirements

*   **Security**: As a local command-line tool, it should respect standard file system permissions and not expose sensitive configuration data
*   **Usability**: 
    *   Clear command-line interface with helpful instructions and error messages
*   **Compatibility**: The tool is written in Python and should be compatible with Python 3.7+. It should run on Linux, macOS, and Windows

## 7. Input/Output Specifications

### Input Files and Directories
*   **Source Directory**: Contains `raw-rules-template/` subdirectory with template files
*   **rules-description.json**: JSON configuration file with variable definitions (optional - defaults to `rules_definitions.json` in same directory as `raw-rules-template/`)
    ```json
    {
      "project_name": "MyProject",
      "version": "1.0.0",
      "author": "Developer Name",
      "custom_variable": "custom_value"
    }
    ```
*   **Template Files**: Files containing `{variable}` placeholders for substitution

### Output Directory Structure
```
source_directory/
├── raw-rules-template/             # Input templates
└── cooked_rules_template/          # Stage 1 output (sibling to raw-rules-template)

copy-content-to-prj-directory/
├── .github/instructions/           # VS Code format
├── .roo/rules/                     # Roo Code format
├── .windsurf/rules/               # Windsurf format
├── .clinerules/                   # Cline format
├── .kilocode/rules/ + .kilo/rules/ # Kilo Code format (+ kilo.jsonc)
├── .gemini/                       # Gemini CLI format
├── .agent/rules/                  # Google Antigravity format
├── .qwen/                         # Qwen Code format
├── .claude/rules/                 # Claude Code format (+ .claude/CLAUDE.md)
├── .codex/rules/default.rules     # Codex .rules command-policy scaffold
└── AGENTS.md                      # OpenAI Codex + ZCode format (shared)
```

#### Format Documentation References
*   **.github/instructions/** (VS Code format):
    *   [GitHub Copilot Chat Documentation](https://docs.github.com/en/copilot/using-github-copilot/github-copilot-chat)
    *   [GitHub Copilot in Your IDE](https://docs.github.com/en/copilot/using-github-copilot/github-copilot-in-your-ide)
    *   [VS Code Copilot Chat Documentation](https://code.visualstudio.com/docs/copilot/chat)
*   **.roo/rules/** (Roo Code format):
    *   [Roo Code Rules Configuration](https://docs.roocode.ai/configuration/rules)
    *   [Roo Code Custom Instructions](https://docs.roocode.ai/advanced/custom-instructions)
    *   [Roo Code Rules Configuration Wiki](https://github.com/roo-code/roo/wiki/Rules-Configuration)
*   **.windsurf/rules/** (Windsurf format):
    *   [Windsurf Customization Rules](https://docs.windsurf.ai/customization/rules)
    *   [Windsurf Configuration Instructions](https://docs.windsurf.ai/configuration/instructions)
    *   [Windsurf Custom Rules Documentation](https://windsurf.ai/docs/custom-rules)
*   **.clinerules/** (Cline format):
    *   [Cline Rules Documentation](https://github.com/saoudrizwan/cline/blob/main/docs/rules.md)
    *   [Cline Customization Documentation](https://github.com/saoudrizwan/cline/blob/main/docs/customization.md)
    *   [Cline Configuration Documentation](https://cline.ai/docs/configuration)
*   **.gemini/** (Gemini format):
    *   [Google AI System Instructions](https://ai.google.dev/docs/system_instructions)
    *   [Gemini CLI Configuration](https://github.com/google-gemini/gemini-cli/blob/main/docs/config.md)
    *   [System Instruction Python Tutorial](https://ai.google.dev/tutorials/system_instruction_python)

Note: Stage 2 validation errors are reported to standard output, not saved to a file.

### Error Handling
*   **Missing Variables**: List all undefined variables, cancel operation, revert changes
*   **Invalid Paths**: Report all invalid file/directory references with line numbers
*   **File System Errors**: Handle permission issues, disk space, etc. with clear messages
*   **JSON Parsing Errors**: Detailed error reporting for malformed configuration files

## 8. Assumptions and Constraints

*   **Assumptions**:
    *   Users have Python and Poetry (or pip) installed
    *   The `rules-description.json` file is well-formed JSON
    *   Template files use `{variable}` syntax for placeholders
    *   Source directory contains a `raw-rules-template/` subdirectory
    *   Users have appropriate file system permissions for read/write operations
*   **Constraints**:
    *   The tool is a command-line application only
    *   Template variable syntax is limited to `{variable}` format
    *   Output directory structures are dictated by the requirements of the target tools
    *   All processing stages must complete successfully or the entire operation fails

## 9. Success Metrics

*   **Key Performance Indicators (KPIs)**:
    *   Successful template variable substitution rate (target: >99%)
    *   Path validation accuracy (target: 100% for valid paths, 0% false positives)
    *   Format conversion success rate (target: >99%)
    *   User adoption by internal development teams
    *   Reduction in configuration errors across different AI tools
    *   Time saved in rule management (target: 80% reduction in manual effort)

## 10. Example Usage

### Command Line Interface
```bash
# Basic usage with default configuration file (rules_definitions.json); output directory is required
./harness-converter.py /path/to/source/directory --output /custom/output/path

# Basic usage with explicit configuration file and output directory
./harness-converter.py /path/to/source/directory /path/to/rules-description.json --output /custom/output/path

```

### Sample rules-description.json
```json
{
    "CodingGuidelinesURLs": ["https://docs.google.com/document/d/e/2PACX-1vTCsVH6gYSmt2imnAbUmw4cljDelRyYD8WxGnhrtPYDPvV_1bUmuaOTmJIyKm7Kw-FuB1AqZbQ_JxiT/pub",
     "https://docs.google.com/document/d/e/2PACX-1vScy4_hNCq7JbTB1BK1B_fnclz4mSUCyRCUN5o4QYW6HOkThpU77Y1dzEGDYe3d8acQXUMJDoIfwzwi/pub"],
    "ApplicationName": "MyDesktopApp",
    "GeneralAIToolkitPath": "/absolute/path/to/general-ai-toolkit",
    "ProjectSpecificAIToolkitPath": "/absolute/path/to/project-ai-toolkit"
}
```

