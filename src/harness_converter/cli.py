"""
Command-line interface for the Harness Converter.

Harness Converter converts AI coding rules and instruction files (harnesses)
among different IDEs and AI agentic environments.
"""
import os
import sys
import click
from .converter import (
    convert_directory,
    process_stage1_template_substitution,
    process_stage2_path_validation,
    load_rules_description_json
)


@click.command(no_args_is_help=True)
@click.argument('source_directory', type=click.Path(exists=True), required=False)
@click.argument('rules_description_json', type=click.Path(exists=True), required=False)
@click.option(
    '--output-dir', '-o',
    type=click.Path(),
    help='Directory to save converted files. If not specified, files are saved in source_directory/copy-content-to-prj-directory/'
)
def main(source_directory, rules_description_json, output_dir):
    """
    Convert rules template files through a 4-stage processing pipeline.
    
    SOURCE_DIRECTORY must contain a 'raw-rules-template/' subdirectory with template files containing {variable} placeholders.
    
    RULES_DESCRIPTION_JSON is an optional JSON file containing variable definitions for template substitution. If not provided, defaults to 'rules_definitions.json' in the same directory as 'raw-rules-template/'.
    
    Processing Stages:
    1. Template Variable Substitution - Replace {variable} placeholders with values from JSON
    2. Path and File Validation - Validate all file paths and references in processed rules
    3. Format Conversion - Convert to VS Code, Roo Code, Windsurf, Cline, Gemini, Kilo Code, Antigravity, Qwen Code, Claude Code, Codex, and ZCode formats
    4. Deployment - Place files in correct directory structure for each tool
    
    Examples:

        # Basic usage with default configuration (rules_definitions.json) and output directory
        harness-converter /path/to/project

        # With explicit configuration file
        harness-converter /path/to/project /path/to/rules-description.json

        # With custom output directory
        harness-converter /path/to/project /path/to/rules-description.json -o /path/to/output
    """
    source_directory = os.path.abspath(source_directory)
    
    # Validate source directory contains raw-rules-template subdirectory
    raw_rules_dir = os.path.join(source_directory, 'raw-rules-template')
    if not os.path.isdir(raw_rules_dir):
        click.echo(f"Error: Source directory must contain 'raw-rules-template/' subdirectory", err=True)
        click.echo(f"Expected: {raw_rules_dir}", err=True)
        sys.exit(1)
    
    # Handle default JSON configuration file
    if rules_description_json is None:
        # Default to rules_definitions.json in the same directory as raw-rules-template
        default_json_path = os.path.join(source_directory, 'rules_definitions.json')
        if os.path.exists(default_json_path):
            rules_description_json = default_json_path
            click.echo(f"Using default configuration: {rules_description_json}")
        else:
            click.echo(f"Error: No configuration file specified and default not found: {default_json_path}", err=True)
            click.echo("Please provide a rules-description.json file as argument or place 'rules_definitions.json' in the source directory.", err=True)
            sys.exit(1)
    else:
        rules_description_json = os.path.abspath(rules_description_json)
    
    # Determine output directory
    if output_dir:
        output_dir = os.path.abspath(output_dir)
    else:
        output_dir = os.path.join(source_directory, 'copy-content-to-prj-directory')
    
    # Stage paths - cooked_rules_template should be sibling to raw-rules-template
    cooked_rules_dir = os.path.join(source_directory, 'cooked_rules_template')
    
    try:
        click.echo(f"Processing rules from: {source_directory}")
        click.echo(f"Using configuration: {rules_description_json}")
        click.echo(f"Output directory: {output_dir}")
        click.echo("")
        
        # Stage 1: Template Variable Substitution
        click.echo("Stage 1: Template Variable Substitution...")
        process_stage1_template_substitution(raw_rules_dir, rules_description_json, cooked_rules_dir)
        click.echo(f"✓ Variables substituted successfully")
        click.echo(f"✓ Processed files saved to: {cooked_rules_dir}")
        
        # Stage 2: Path and File Validation
        click.echo("\nStage 2: Path and File Validation...")
        validation_issues = process_stage2_path_validation(cooked_rules_dir)
        if validation_issues:
            click.echo("⚠ Validation issues found:")
            for issue in validation_issues:
                click.echo(f"  - {issue}")
        else:
            click.echo("✓ All file paths and references are valid")
        
        click.echo("\nStage 3 & 4: Format Conversion and Deployment...")
        (vscode_converted_files, roo_converted_files, windsurf_converted_files,
         cline_converted_files, gemini_cli_converted_files, kilo_code_converted_files,
         antigravity_converted_files, qwen_code_converted_files, claude_code_converted_files,
         codex_converted_files, zcode_converted_files, copied_files) = convert_directory(cooked_rules_dir, output_dir)

        total_processed = len(vscode_converted_files) + len(copied_files)

        click.echo(f"✓ Processed {total_processed} files")
        click.echo(f"✓ Converted {len(vscode_converted_files)} template files")
        click.echo(f"  - VS Code instructions: {len(vscode_converted_files)} files")
        click.echo(f"  - Roo Code rules: {len(roo_converted_files)} files")
        click.echo(f"  - Windsurf rules: {len(windsurf_converted_files)} files")
        click.echo(f"  - Cline rules: {len(cline_converted_files)} files")
        click.echo(f"  - Gemini CLI rules: {len(gemini_cli_converted_files)} files")
        click.echo(f"  - Kilo Code rules: {len(kilo_code_converted_files)} files")
        click.echo(f"  - Antigravity rules: {len(antigravity_converted_files)} files")
        click.echo(f"  - Qwen Code rules: {len(qwen_code_converted_files)} files")
        click.echo(f"  - Claude Code rules: {len(claude_code_converted_files)} files")
        click.echo(f"  - OpenAI Codex rules: {len(codex_converted_files)} files")
        click.echo(f"  - ZCode rules: {len(zcode_converted_files)} files")
        click.echo(f"✓ Copied {len(copied_files)} other files")
        
        click.echo(f"\n✅ Rules conversion completed successfully!")
        click.echo(f"Output directory: {output_dir}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()