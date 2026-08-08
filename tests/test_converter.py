#!/usr/bin/env python3
"""
Test script to demonstrate how to use the converter programmatically.
"""
import os
import sys
from harness_converter.converter import convert_file, convert_directory


def main():
    """Run a simple test of the converter."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the sample MDC file (test fixtures live alongside this script)
    sample_file = os.path.join(script_dir, 'test-mdc-files', 'test_1.mdc')
    
    if not os.path.exists(sample_file):
        print(f"Error: Sample file {sample_file} not found.")
        sys.exit(1)
    
    print("Converting single file...")
    vscode_output_file, roo_output_file, windsurf_output_file, cline_output_file, gemini_cli_output_file, kilo_code_output_file, antigravity_output_file, qwen_code_output_file, claude_code_output_file, codex_output_file, zcode_output_file = convert_file(sample_file)
    print(f"Converted {sample_file}:")
    print(f"  - VS Code: {vscode_output_file}")
    print(f"  - Roo Code: {roo_output_file}")
    print(f"  - Windsurf: {windsurf_output_file}")
    print(f"  - Cline: {cline_output_file}")
    print(f"  - Gemini CLI: {gemini_cli_output_file}")
    print(f"  - Kilo Code: {kilo_code_output_file}")
    print(f"  - Antigravity: {antigravity_output_file}")
    print(f"  - Qwen Code: {qwen_code_output_file}")
    print(f"  - Claude Code: {claude_code_output_file}")
    print(f"  - OpenAI Codex: {codex_output_file}")
    print(f"  - ZCode: {zcode_output_file}")
    
    # Create a test directory with multiple MDC files
    test_project_dir = os.path.join(script_dir, 'test_project_programmatic')
    test_dir = os.path.join(test_project_dir, '.cursor', 'rules')
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a few test MDC files
    for i in range(1, 4):
        test_file = os.path.join(test_dir, f'test_{i}.mdc')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(f'''{{
  "name": "Test Rule {i}",
  "description": "This is test rule {i}",
  "rules": [
    {{
      "pattern": "test pattern {i}",
      "message": "Test message {i}"
    }}
  ],
  "content": "This is test content {i}."
}}''')
    
    # Create a subdirectory with more MDC files
    sub_dir = os.path.join(test_dir, 'subdir')
    os.makedirs(sub_dir, exist_ok=True)
    
    for i in range(1, 3):
        test_file = os.path.join(sub_dir, f'subtest_{i}.mdc')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(f'''{{
  "name": "Subdir Test Rule {i}",
  "description": "This is subdir test rule {i}",
  "rules": [
    {{
      "pattern": "subdir test pattern {i}",
      "message": "Subdir test message {i}"
    }}
  ],
  "content": "This is subdir test content {i}."
}}''')
    
    print("\nConverting directory...")
    output_dir = os.path.join(script_dir, 'output_test_programmatic') # Generated; gitignored under tests/
    os.makedirs(output_dir, exist_ok=True) # Ensure output_dir exists
    
    vscode_converted_paths, roo_converted_paths, windsurf_converted_paths, cline_converted_paths, gemini_cli_converted_paths, kilo_code_converted_paths, antigravity_converted_paths, qwen_code_converted_paths, claude_code_converted_paths, codex_converted_paths, zcode_converted_paths, copied_paths = convert_directory(test_project_dir, output_dir)
    
    total_processed = len(vscode_converted_paths) + len(copied_paths)
    print(f"Processed {total_processed} files to {output_dir}:")
    if vscode_converted_paths:
        print(f"  Converted {len(vscode_converted_paths)} '.mdc' files to VS Code instructions:")
        for file_path in vscode_converted_paths:
            print(f"    - {file_path}")
    if roo_converted_paths:
        print(f"  Converted {len(roo_converted_paths)} '.mdc' files to Roo Code rules:")
        for file_path in roo_converted_paths:
            print(f"    - {file_path}")
    if windsurf_converted_paths:
        print(f"  Converted {len(windsurf_converted_paths)} '.mdc' files to Windsurf rules:")
        for file_path in windsurf_converted_paths:
            print(f"    - {file_path}")
    if cline_converted_paths:
        print(f"  Converted {len(cline_converted_paths)} '.mdc' files to Cline rules:")
        for file_path in cline_converted_paths:
            print(f"    - {file_path}")
    if gemini_cli_converted_paths:
        print(f"  Converted {len(gemini_cli_converted_paths)} '.mdc' files to Gemini CLI rules:")
        for file_path in gemini_cli_converted_paths:
            print(f"    - {file_path}")
    if kilo_code_converted_paths:
        print(f"  Converted {len(kilo_code_converted_paths)} '.mdc' files to Kilo Code rules:")
        for file_path in kilo_code_converted_paths:
            print(f"    - {file_path}")
    if antigravity_converted_paths:
        print(f"  Converted {len(antigravity_converted_paths)} '.mdc' files to Antigravity rules:")
        for file_path in antigravity_converted_paths:
            print(f"    - {file_path}")
    if qwen_code_converted_paths:
        print(f"  Converted {len(qwen_code_converted_paths)} '.mdc' files to Qwen Code rules:")
        for file_path in qwen_code_converted_paths:
            print(f"    - {file_path}")
    if claude_code_converted_paths:
        print(f"  Converted {len(claude_code_converted_paths)} '.mdc' files to Claude Code rules:")
        for file_path in claude_code_converted_paths:
            print(f"    - {file_path}")
    if codex_converted_paths:
        print(f"  Converted {len(codex_converted_paths)} '.mdc' files to OpenAI Codex rules:")
        for file_path in codex_converted_paths:
            print(f"    - {file_path}")
    if zcode_converted_paths:
        print(f"  Converted {len(zcode_converted_paths)} '.mdc' files to ZCode rules:")
        for file_path in zcode_converted_paths:
            print(f"    - {file_path}")
    if copied_paths:
        print(f"  Copied {len(copied_paths)} other files:")
        for file_path in copied_paths:
            print(f"    - {file_path}")


if __name__ == "__main__":
    main()
