"""
Converter module that transforms AI coding rules and instruction files (harnesses)
among different IDEs and AI agentic environments.
Supports VS Code, Roo Code, Windsurf, Cline, Gemini CLI, Kilo Code, Antigravity,
Qwen Code, Claude Code, OpenAI Codex, and ZCode.
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def normalize_directory_component(name: str) -> str:
    """
    Normalize a single directory component.

    Directories should use hyphens between parts, not underscores.
    """
    if not name or name in ('.', '..'):
        return name

    prefix = ''
    if name.startswith('.'):
        prefix = '.'
        name = name[1:]

    normalized = re.sub(r'[_\s]+', '-', name)
    normalized = re.sub(r'-+', '-', normalized)
    return prefix + normalized


def normalize_relative_path(path: str) -> str:
    """Normalize all components of a relative path for directories."""
    if not path or path == '.':
        return ''

    parts = path.split(os.sep)
    normalized_parts = [normalize_directory_component(part) for part in parts if part and part != '.']
    return os.sep.join(normalized_parts)


def normalize_file_base_name(name: str) -> str:
    """Normalize a file base name to use underscores for part separators."""
    if not name:
        return name

    prefix = ''
    if name.startswith('.'):
        prefix = '.'
        name = name[1:]

    normalized = re.sub(r'[-\s]+', '_', name)
    normalized = re.sub(r'_+', '_', normalized)
    return prefix + normalized


def normalize_file_name(file_name: str) -> str:
    """Normalize a file name while preserving its extension."""
    base, ext = os.path.splitext(file_name)
    return normalize_file_base_name(base) + ext


def substitute_template_variables(content: str, variables: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Substitute {variable} placeholders in content with values from variables dict.

    Args:
        content: Text content with {variable} placeholders
        variables: Dictionary of variable name -> value mappings
50
    Returns:
        Tuple of (substituted_content, list_of_missing_variables)
    """
    # Find all {variable} patterns in the content, but exclude JSON-like structures
    # This pattern looks for {variable} where variable doesn't contain quotes or colons
    # to avoid matching JSON object syntax like {"key": "value"}
    variable_pattern = re.compile(r'\{([^}"\':\s][^}]*)\}')
    found_variables = variable_pattern.findall(content)

    # Track missing variables
    missing_variables = []
    substituted_content = content

    for var_name in found_variables:
        if var_name in variables:
            # Substitute the variable with its value
            placeholder = f"{{{var_name}}}"
            substituted_content = substituted_content.replace(placeholder, str(variables[var_name]))
        else:
            missing_variables.append(var_name)

    return substituted_content, missing_variables


def load_rules_description_json(json_path: str) -> Dict[str, Any]:
    """
    Load and parse the rules-description.json configuration file.
    
    Args:
        json_path: Path to the rules-description.json file
        
    Returns:
        Dictionary containing variable definitions
        
    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the JSON file is malformed
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Configuration file not found: {json_path}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Malformed JSON in {json_path}: {e.msg}", e.doc, e.pos)


def process_stage1_template_substitution(raw_rules_dir: str, rules_json_path: str, cooked_rules_dir: str) -> None:
    """
    Stage 1: Template Variable Substitution
    Process all template files in raw-rules-template directory and substitute variables.
    
    Args:
        raw_rules_dir: Path to raw-rules-template directory
        rules_json_path: Path to rules-description.json file
        cooked_rules_dir: Path to output cooked-rules-template directory
        
    Raises:
        ValueError: If any variables are missing from configuration
        FileNotFoundError: If directories or files don't exist
    """
    if not os.path.isdir(raw_rules_dir):
        raise FileNotFoundError(f"Raw rules template directory not found: {raw_rules_dir}")
    
    # Load variable definitions
    variables = load_rules_description_json(rules_json_path)
    
    # Track all missing variables across all files
    all_missing_variables = set()
    
    # Create output directory
    os.makedirs(cooked_rules_dir, exist_ok=True)
    
    # Process all files recursively
    for root, dirs, files in os.walk(raw_rules_dir):
        for file in files:
            input_file_path = os.path.join(root, file)
            
            # Calculate relative path from raw_rules_dir to maintain structure
            rel_path = os.path.relpath(input_file_path, raw_rules_dir)
            output_file_path = os.path.join(cooked_rules_dir, rel_path)
            
            # Create output directory structure
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            # Read file content
            try:
                with open(input_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Substitute variables
                substituted_content, missing_vars = substitute_template_variables(content, variables)
                
                # Track missing variables
                all_missing_variables.update(missing_vars)
                
                # Write substituted content to output file
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(substituted_content)
                    
            except UnicodeDecodeError:
                # For binary files, just copy them as-is
                with open(input_file_path, 'rb') as f_in:
                    with open(output_file_path, 'wb') as f_out:
                        f_out.write(f_in.read())
    
    # If any variables are missing, show error and raise exception
    if all_missing_variables:
        missing_list = sorted(list(all_missing_variables))
        error_msg = f"Missing variables in rules-description.json: {', '.join(missing_list)}"
        print(f"Error: {error_msg}")
        
        # Clean up cooked_rules_dir on error
        import shutil
        if os.path.exists(cooked_rules_dir):
            shutil.rmtree(cooked_rules_dir)
        
        raise ValueError(error_msg)


def extract_file_paths_from_content(content: str) -> List[str]:
    """
    Extract potential file paths and directory references from content.
    
    Args:
        content: Text content to scan for file paths
        
    Returns:
        List of potential file paths found in the content
    """
    paths = []
    
    # Common path patterns to look for
    path_patterns = [
        # Absolute paths starting with / or ~
        r'["\']([/~][^\s"\']+)["\']',
        r'["\']([A-Za-z]:[\\\/][^\s"\']+)["\']',  # Windows paths
        # Relative paths 
        r'["\']([.]{1,2}[/\\][^\s"\']+)["\']',
        # Common file extensions
        r'["\']([^\s"\']+\.[a-zA-Z0-9]{1,5})["\']',
        # Path-like patterns without quotes
        r'\b([/~][^\s]+)\b',
        r'\b([.]{1,2}[/\\][^\s]+)\b',
    ]
    
    for pattern in path_patterns:
        matches = re.findall(pattern, content)
        paths.extend(matches)
    
    # Remove duplicates while preserving order
    unique_paths = []
    seen = set()
    for path in paths:
        if path not in seen and len(path) > 1:  # Filter out very short matches
            seen.add(path)
            unique_paths.append(path)
    
    return unique_paths


def validate_file_path(path: str, base_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate if a file path exists and is accessible.
    
    Args:
        path: File path to validate
        base_dir: Base directory for relative paths
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Handle relative paths
        if not os.path.isabs(path) and base_dir:
            full_path = os.path.join(base_dir, path)
        else:
            full_path = path
        
        # Expand user home directory
        full_path = os.path.expanduser(full_path)
        
        if os.path.exists(full_path):
            return True, ""
        else:
            return False, f"Path does not exist: {path}"
            
    except (OSError, ValueError) as e:
        return False, f"Invalid path '{path}': {str(e)}"


def process_stage2_path_validation(cooked_rules_dir: str) -> List[str]:
    """
    Stage 2: Path and File Validation
    Parse all files in cooked-rules-template and validate file paths and references.
    
    Args:
        cooked_rules_dir: Path to cooked-rules-template directory
        
    Returns:
        List of validation error messages (empty if all paths are valid)
    """
    if not os.path.isdir(cooked_rules_dir):
        return [f"Cooked rules directory not found: {cooked_rules_dir}"]
    
    validation_issues = []
    
    # Process all files recursively
    for root, _, files in os.walk(cooked_rules_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            try:
                # Try to read as text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract potential file paths
                found_paths = extract_file_paths_from_content(content)
                
                # Validate each path
                for path in found_paths:
                    # Skip very common patterns that are not file paths
                    if any(skip in path.lower() for skip in ['http://', 'https://', 'mailto:', 'ftp://']):
                        continue
                    
                    is_valid, error_msg = validate_file_path(path, os.path.dirname(file_path))
                    
                    if not is_valid:
                        rel_file_path = os.path.relpath(file_path, cooked_rules_dir)
                        validation_issues.append(f"In {rel_file_path}: {error_msg}")
                        
            except UnicodeDecodeError:
                # Skip binary files
                continue
            except Exception as e:
                rel_file_path = os.path.relpath(file_path, cooked_rules_dir)
                validation_issues.append(f"Error reading {rel_file_path}: {str(e)}")
    
    return validation_issues


def parse_mdc_file(file_path: str) -> str:
    """
    Read a Cursor IDE MDC file and return its content as plain text.
    
    Args:
        file_path: Path to the MDC file
        
    Returns:
        Content of the MDC file as plain text
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Return the content as is, to be processed by convert_to_vscode_instructions
    return content


def _escape_yaml_string(value: str) -> str:
    """Escapes single quotes for YAML single-quoted strings."""
    return value.replace("'", "'''")


def convert_to_vscode_instructions(mdc_content: str) -> str:
    """
    Convert MDC content (JSON or YAML-like) to VS Code Copilot instruction file format.
    The output will have YAML frontmatter with 'description' (if available) and 'files: ["**"]',
    followed by the main instruction body.
    
    Args:
        mdc_content: Content from the MDC file
        
    Returns:
        Content formatted for VS Code instruction files
    """
    extracted_description: Optional[str] = None
    main_body_content_str: str = ""

    try:
        # Attempt to parse as JSON first
        data = json.loads(mdc_content)
        extracted_description = data.get("description")
        main_body_content_str = data.get("content", "")
        # Note: 'name' and 'rules' from JSON are not directly used in the new output format
    except json.JSONDecodeError:
        # JSON parsing failed, attempt to parse as YAML-like with frontmatter
        lines = mdc_content.splitlines()
        
        if lines and lines[0] == "---":
            frontmatter_lines: List[str] = []
            body_lines: List[str] = []
            in_frontmatter = True
            
            # Start scanning from the line *after* the first '---'
            for i in range(1, len(lines)):
                if in_frontmatter and lines[i] == "---":
                    in_frontmatter = False # Closing '---' found
                    continue # Don't add this '---' to body or frontmatter
                
                if in_frontmatter:
                    frontmatter_lines.append(lines[i])
                else:
                    body_lines.append(lines[i])
            
            if in_frontmatter: 
                # Closing '---' was not found, but we started with '---'.
                # This is malformed. Treat everything after the first '---' as body for robustness.
                # However, if no actual content follows, this list could be empty.
                main_body_content_str = "\n".join(frontmatter_lines) # frontmatter_lines here are actually body lines
            else:
                 # Properly closed frontmatter was found, parse it
                for fm_line in frontmatter_lines:
                    if ":" in fm_line:
                        key, val = fm_line.split(":", 1)
                        key = key.strip()
                        val = val.strip() # Raw value
                        if key == "description":
                            # Basic unquoting for description
                            if (val.startswith("'") and val.endswith("'")) or \
                               (val.startswith('"') and val.endswith('"')):
                                extracted_description = val[1:-1]
                            else:
                                extracted_description = val
                        # Other frontmatter keys like 'name', 'globs', 'alwaysApply' are ignored
                main_body_content_str = "\n".join(body_lines)

        else:
            # No leading '---', so assume the entire content is the main body
            main_body_content_str = mdc_content

    # Construct the output in VS Code instruction file format
    output_lines: List[str] = []
    output_lines.append("---")
    
    if extracted_description:
        output_lines.append(f"description: '{_escape_yaml_string(extracted_description)}'")
    
    output_lines.append('applyTo: "**"') # This ensures applyTo: "**"
    
    output_lines.append("---")
    output_lines.append("") # Blank line after frontmatter block
    
    # Append the main body content, stripping only leading/trailing whitespace from the whole block
    output_lines.append(main_body_content_str.strip())
            
    return "\n".join(output_lines)


def save_vscode_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save VS Code instructions to a file.
    
    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def convert_to_windsurf_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to Windsurf rules format.
    Windsurf rules have YAML frontmatter with trigger: always_on, description, and globs: **/*
    followed by the main instruction body.
    
    Args:
        mdc_content: Content from the MDC file
        
    Returns:
        Content formatted for Windsurf rules files
    """
    extracted_description: Optional[str] = None
    main_body_content_str: str = ""

    try:
        # Attempt to parse as JSON first
        data = json.loads(mdc_content)
        extracted_description = data.get("description")
        main_body_content_str = data.get("content", "")
        # Note: 'name' and 'rules' from JSON are not directly used in the new output format
    except json.JSONDecodeError:
        # JSON parsing failed, attempt to parse as YAML-like with frontmatter
        lines = mdc_content.splitlines()
        
        if lines and lines[0] == "---":
            frontmatter_lines: List[str] = []
            body_lines: List[str] = []
            in_frontmatter = True
            
            # Start scanning from the line *after* the first '---'
            for i in range(1, len(lines)):
                if in_frontmatter and lines[i] == "---":
                    in_frontmatter = False # Closing '---' found
                    continue # Don't add this '---' to body or frontmatter
                
                if in_frontmatter:
                    frontmatter_lines.append(lines[i])
                else:
                    body_lines.append(lines[i])
            
            if in_frontmatter: 
                # Closing '---' was not found, but we started with '---'.
                # This is malformed. Treat everything after the first '---' as body for robustness.
                main_body_content_str = "\n".join(frontmatter_lines)
            else:
                 # Properly closed frontmatter was found, parse it
                for fm_line in frontmatter_lines:
                    if ":" in fm_line:
                        key, val = fm_line.split(":", 1)
                        key = key.strip()
                        val = val.strip() # Raw value
                        if key == "description":
                            # Basic unquoting for description
                            if (val.startswith("'") and val.endswith("'")) or \
                               (val.startswith('"') and val.endswith('"')):
                                extracted_description = val[1:-1]
                            else:
                                extracted_description = val
                main_body_content_str = "\n".join(body_lines)

        else:
            # No leading '---', so assume the entire content is the main body
            main_body_content_str = mdc_content

    # Construct the output in Windsurf rules format
    output_lines: List[str] = []
    output_lines.append("---")
    output_lines.append("trigger: always_on")
    
    if extracted_description:
        output_lines.append(f"description: {extracted_description}")
    else:
        output_lines.append("description: ")
    
    output_lines.append("globs: **/*")
    output_lines.append("---")
    output_lines.append("") # Blank line after frontmatter block
    
    # Append the main body content, stripping only leading/trailing whitespace from the whole block
    output_lines.append(main_body_content_str.strip())
            
    return "\n".join(output_lines)


def save_windsurf_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save Windsurf instructions to a file.
    
    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def convert_to_cline_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to Cline rules format.
    Cline rules are plain markdown files without frontmatter, similar to Roo Code format.
    
    Args:
        mdc_content: Content from the MDC file
        
    Returns:
        Content formatted for Cline rules files
    """
    extracted_description: Optional[str] = None
    main_body_content_str: str = ""

    try:
        # Attempt to parse as JSON first
        data = json.loads(mdc_content)
        extracted_description = data.get("description")
        main_body_content_str = data.get("content", "")
    except json.JSONDecodeError:
        # JSON parsing failed, attempt to parse as YAML-like with frontmatter
        lines = mdc_content.splitlines()
        
        if lines and lines[0] == "---":
            frontmatter_lines: List[str] = []
            body_lines: List[str] = []
            in_frontmatter = True
            
            # Start scanning from the line *after* the first '---'
            for i in range(1, len(lines)):
                if in_frontmatter and lines[i] == "---":
                    in_frontmatter = False # Closing '---' found
                    continue # Don't add this '---' to body or frontmatter
                
                if in_frontmatter:
                    frontmatter_lines.append(lines[i])
                else:
                    body_lines.append(lines[i])
            
            if in_frontmatter: 
                # Closing '---' was not found, but we started with '---'.
                # This is malformed. Treat everything after the first '---' as body for robustness.
                main_body_content_str = "\n".join(frontmatter_lines)
            else:
                 # Properly closed frontmatter was found, parse it
                for fm_line in frontmatter_lines:
                    if ":" in fm_line:
                        key, val = fm_line.split(":", 1)
                        key = key.strip()
                        val = val.strip() # Raw value
                        if key == "description":
                            # Basic unquoting for description
                            if (val.startswith("'") and val.endswith("'")) or \
                               (val.startswith('"') and val.endswith('"')):
                                extracted_description = val[1:-1]
                            else:
                                extracted_description = val
                main_body_content_str = "\n".join(body_lines)

        else:
            # No leading '---', so assume the entire content is the main body
            main_body_content_str = mdc_content

    # Construct the output for Cline format (plain text/markdown like Roo Code)
    output_parts: List[str] = []
    
    # Add description as a header if available
    if extracted_description:
        output_parts.append(f"# {extracted_description}")
        output_parts.append("")  # Add blank line after header
    
    # Add the main body content
    output_parts.append(main_body_content_str.strip())
    
    return "\n".join(output_parts)


def save_cline_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save Cline instructions to a file.
    
    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def convert_to_roo_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to Roo Code instructions format.
    Roo Code instructions are plain text/markdown files without frontmatter.
    
    Args:
        mdc_content: Content from the MDC file
        
    Returns:
        Content formatted for Roo Code instruction files
    """
    extracted_description: Optional[str] = None
    main_body_content_str: str = ""

    try:
        # Attempt to parse as JSON first
        data = json.loads(mdc_content)
        extracted_description = data.get("description")
        main_body_content_str = data.get("content", "")
    except json.JSONDecodeError:
        # JSON parsing failed, attempt to parse as YAML-like with frontmatter
        lines = mdc_content.splitlines()
        
        if lines and lines[0] == "---":
            frontmatter_lines: List[str] = []
            body_lines: List[str] = []
            in_frontmatter = True
            
            # Start scanning from the line *after* the first '---'
            for i in range(1, len(lines)):
                if in_frontmatter and lines[i] == "---":
                    in_frontmatter = False # Closing '---' found
                    continue # Don't add this '---' to body or frontmatter
                
                if in_frontmatter:
                    frontmatter_lines.append(lines[i])
                else:
                    body_lines.append(lines[i])
            
            if in_frontmatter: 
                # Closing '---' was not found, but we started with '---'.
                # This is malformed. Treat everything after the first '---' as body for robustness.
                main_body_content_str = "\n".join(frontmatter_lines)
            else:
                 # Properly closed frontmatter was found, parse it
                for fm_line in frontmatter_lines:
                    if ":" in fm_line:
                        key, val = fm_line.split(":", 1)
                        key = key.strip()
                        val = val.strip() # Raw value
                        if key == "description":
                            # Basic unquoting for description
                            if (val.startswith("'") and val.endswith("'")) or \
                               (val.startswith('"') and val.endswith('"')):
                                extracted_description = val[1:-1]
                            else:
                                extracted_description = val
                main_body_content_str = "\n".join(body_lines)

        else:
            # No leading '---', so assume the entire content is the main body
            main_body_content_str = mdc_content

    # Construct the output for Roo Code format (plain text/markdown)
    output_parts: List[str] = []
    
    # Add description as a header if available
    if extracted_description:
        output_parts.append(f"# {extracted_description}")
        output_parts.append("")  # Add blank line after header
    
    # Add the main body content
    output_parts.append(main_body_content_str.strip())
    
    return "\n".join(output_parts)


def save_roo_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save Roo Code instructions to a file.
    
    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def convert_to_gemini_cli_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to Gemini CLI instructions format.
    Gemini CLI instructions are plain text/markdown files without frontmatter.

    Args:
        mdc_content: Content from the MDC file

    Returns:
        Content formatted for Gemini CLI instruction files
    """
    return convert_to_roo_instructions(mdc_content)


def convert_to_antigravity_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to Google Antigravity instructions format.
    Antigravity instructions are plain text/markdown files without frontmatter,
    stored in .agent/rules/ directory.

    Args:
        mdc_content: Content from the MDC file

    Returns:
        Content formatted for Google Antigravity instruction files
    """
    return convert_to_roo_instructions(mdc_content)


def save_antigravity_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save Google Antigravity instructions to a file.

    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)

def convert_to_kilo_code_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to Kilo Code instructions format.
    Kilo Code instructions are plain markdown files without frontmatter, similar to Roo Code format.

    Args:
        mdc_content: Content from the MDC file

    Returns:
        Content formatted for Kilo Code instruction files
    """
    extracted_description: Optional[str] = None
    main_body_content_str: str = ""

    try:
        # Attempt to parse as JSON first
        data = json.loads(mdc_content)
        extracted_description = data.get("description")
        main_body_content_str = data.get("content", "")
    except json.JSONDecodeError:
        # JSON parsing failed, attempt to parse as YAML-like with frontmatter
        lines = mdc_content.splitlines()

        if lines and lines[0] == "---":
            frontmatter_lines: List[str] = []
            body_lines: List[str] = []
            in_frontmatter = True

            # Start scanning from the line *after* the first '---'
            for i in range(1, len(lines)):
                if in_frontmatter and lines[i] == "---":
                    in_frontmatter = False # Closing '---' found
                    continue # Don't add this '---' to body or frontmatter

                if in_frontmatter:
                    frontmatter_lines.append(lines[i])
                else:
                    body_lines.append(lines[i])

            if in_frontmatter:
                # Closing '---' was not found, but we started with '---'.
                # This is malformed. Treat everything after the first '---' as body for robustness.
                main_body_content_str = "\n".join(frontmatter_lines)
            else:
                  # Properly closed frontmatter was found, parse it
                for fm_line in frontmatter_lines:
                    if ":" in fm_line:
                        key, val = fm_line.split(":", 1)
                        key = key.strip()
                        val = val.strip() # Raw value
                        if key == "description":
                            # Basic unquoting for description
                            if (val.startswith("'") and val.endswith("'")) or \
                               (val.startswith('"') and val.endswith('"')):
                                extracted_description = val[1:-1]
                            else:
                                extracted_description = val
                main_body_content_str = "\n".join(body_lines)

        else:
            # No leading '---', so assume the entire content is the main body
            main_body_content_str = mdc_content

    # Construct the output for Kilo Code format (plain text/markdown)
    output_parts: List[str] = []

    # Add description as a header if available
    if extracted_description:
        output_parts.append(f"# {extracted_description}")
        output_parts.append("")  # Add blank line after header

    # Add the main body content
    output_parts.append(main_body_content_str.strip())

    return "\n".join(output_parts)


def save_gemini_cli_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save Gemini CLI instructions to a file.

    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def save_kilo_code_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save Kilo Code instructions to a file.

    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def write_kilo_json(base_output_dir: str, rule_files: List[str]) -> str:
    """
    Write a kilo.jsonc config file with instructions referencing all rule files.

    Per Kilo documentation (https://kilo.ai/docs/customize/custom-rules#vscode):
    - Project rules are configured via the 'instructions' key in kilo.jsonc
    - Rules are placed in .kilo/rules/ directory
    - A glob pattern can reference all rules

    Args:
        base_output_dir: Base output directory (e.g. copy-content-to-prj-directory)
        rule_files: List of relative rule file paths

    Returns:
        Path to the written kilo.jsonc file
    """
    kilo_json_path = os.path.join(base_output_dir, "kilo.jsonc")

    instructions = [".kilo/rules/*.md"]

    kilo_config = {
        "$schema": "https://app.kilo.ai/config.json",
        "instructions": instructions
    }

    os.makedirs(base_output_dir, exist_ok=True)
    with open(kilo_json_path, 'w', encoding='utf-8') as f:
        json.dump(kilo_config, f, indent=2)
        f.write('\n')

    return kilo_json_path


def convert_to_qwen_code_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to Qwen Code instructions format.
    Qwen Code (fork of Gemini CLI) uses QWEN.md context files with plain markdown.
    Individual rule files are plain markdown without frontmatter.

    See: https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/
    (Context Files section)

    Args:
        mdc_content: Content from the MDC file

    Returns:
        Content formatted for Qwen Code instruction files
    """
    return convert_to_roo_instructions(mdc_content)


def save_qwen_code_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save Qwen Code instructions to a file.

    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def convert_to_claude_code_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to Claude Code instructions format.
    Claude Code uses .claude/rules/ directory with plain markdown files.
    Rules without a 'paths' frontmatter field are loaded unconditionally.

    See: https://code.claude.com/docs/en/memory
    (Organize rules with .claude/rules/ section)

    Args:
        mdc_content: Content from the MDC file

    Returns:
        Content formatted for Claude Code rule files
    """
    return convert_to_roo_instructions(mdc_content)


def save_claude_code_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save Claude Code instructions to a file.

    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def convert_to_codex_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to OpenAI Codex instructions format.
    Codex uses AGENTS.md files with plain markdown content.
    Codex discovers AGENTS.md by walking from project root to current directory.

    See: https://developers.openai.com/codex/guides/agents-md

    Args:
        mdc_content: Content from the MDC file

    Returns:
        Content formatted for OpenAI Codex AGENTS.md
    """
    return convert_to_roo_instructions(mdc_content)


def save_codex_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save OpenAI Codex instructions to a file.

    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def convert_to_zcode_instructions(mdc_content: str) -> str:
    """
    Convert MDC content to ZCode instructions format.
    ZCode uses a single AGENTS.md file (plain markdown, no frontmatter) at the
    workspace root as its always-on instruction/rules mechanism. Per-rule content
    is identical to the Codex target; the directory walk concatenates all rules
    into one AGENTS.md.

    See: https://zcode.z.ai/en/docs/agents

    Args:
        mdc_content: Content from the MDC file

    Returns:
        Content formatted for ZCode AGENTS.md
    """
    return convert_to_roo_instructions(mdc_content)


def save_zcode_instructions(instructions_content: str, output_path: str) -> None:
    """
    Save ZCode instructions to a file.

    Args:
        instructions_content: Content for the instructions file
        output_path: Path to save the instructions file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions_content)


def convert_file(input_path_str: str, output_dir_str: Optional[str] = None) -> Tuple[str, str, str, str, str, str, str, str, str, str, str]:
    """
    Convert a single template file to all target formats.

    Args:
        input_path_str: Path to the input template file
        output_dir_str: Directory to save the output files (optional)

    Returns:
        Tuple of (VS Code, Roo Code, Windsurf, Cline, Gemini CLI, Kilo Code,
        Antigravity, Qwen Code, Claude Code, Codex, ZCode instructions file paths)
    """
    input_path_abs = os.path.abspath(input_path_str)
    input_file_name = os.path.basename(input_path_abs)
    input_file_dir = os.path.dirname(input_path_abs)

    try:
        mdc_content = parse_mdc_file(input_path_abs)
        vscode_instructions_content = convert_to_vscode_instructions(mdc_content)
        roo_instructions_content = convert_to_roo_instructions(mdc_content)
        windsurf_instructions_content = convert_to_windsurf_instructions(mdc_content)
        cline_instructions_content = convert_to_cline_instructions(mdc_content)
        gemini_cli_instructions_content = convert_to_gemini_cli_instructions(mdc_content)
        kilo_code_instructions_content = convert_to_kilo_code_instructions(mdc_content)
        antigravity_instructions_content = convert_to_antigravity_instructions(mdc_content)
        qwen_code_instructions_content = convert_to_qwen_code_instructions(mdc_content)
        claude_code_instructions_content = convert_to_claude_code_instructions(mdc_content)
        codex_instructions_content = convert_to_codex_instructions(mdc_content)
        
        # Determine base output directory
        if output_dir_str:
            base_for_output = os.path.abspath(output_dir_str)
        else:
            base_for_output = input_file_dir
        
        # VS Code output structure: base_for_output/.github/instructions/original_filename.instructions.md
        github_instructions_dir = os.path.join(base_for_output, ".github", "instructions")
        input_file_base = normalize_file_base_name(os.path.splitext(input_file_name)[0])
        vscode_output_filename = input_file_base + ".instructions.md"
        vscode_output_path = os.path.join(github_instructions_dir, vscode_output_filename)
        save_vscode_instructions(vscode_instructions_content, vscode_output_path)
        
        # Roo Code output structure: base_for_output/.roo/rules/original_filename.md
        roo_rules_dir = os.path.join(base_for_output, ".roo", "rules")
        roo_output_filename = input_file_base + ".md"
        roo_output_path = os.path.join(roo_rules_dir, roo_output_filename)
        save_roo_instructions(roo_instructions_content, roo_output_path)
        
        # Windsurf output structure: base_for_output/.windsurf/rules/original_filename.md
        windsurf_rules_dir = os.path.join(base_for_output, ".windsurf", "rules")
        windsurf_output_filename = input_file_base + ".md"
        windsurf_output_path = os.path.join(windsurf_rules_dir, windsurf_output_filename)
        save_windsurf_instructions(windsurf_instructions_content, windsurf_output_path)
        
        # Cline output structure: base_for_output/.clinerules/original_filename.md
        cline_rules_dir = os.path.join(base_for_output, ".clinerules")
        cline_output_filename = input_file_base + ".md"
        cline_output_path = os.path.join(cline_rules_dir, cline_output_filename)
        save_cline_instructions(cline_instructions_content, cline_output_path)

        # Gemini CLI output structure
        gemini_rules_dir = os.path.join(base_for_output, ".gemini")
        gemini_master_file_path = os.path.join(gemini_rules_dir, "GEMINI.md")
        gemini_cli_output_filename = input_file_base + ".md"
        gemini_cli_output_path = os.path.join(gemini_rules_dir, gemini_cli_output_filename)
        save_gemini_cli_instructions(gemini_cli_instructions_content, gemini_cli_output_path)

        relative_path_for_import = os.path.relpath(gemini_cli_output_path, gemini_rules_dir)
        with open(gemini_master_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Gemini CLI Rules\n\n@{relative_path_for_import}\n")

        # Kilo Code legacy output structure: base_for_output/.kilocode/rules/original_filename.md
        kilo_code_rules_dir = os.path.join(base_for_output, ".kilocode", "rules")
        kilo_code_output_filename = input_file_base + ".md"
        kilo_code_output_path = os.path.join(kilo_code_rules_dir, kilo_code_output_filename)
        save_kilo_code_instructions(kilo_code_instructions_content, kilo_code_output_path)

        # Kilo Code new standard output: base_for_output/.kilo/rules/original_filename.md
        kilo_new_rules_dir = os.path.join(base_for_output, ".kilo", "rules")
        kilo_new_output_filename = input_file_base + ".md"
        kilo_new_output_path = os.path.join(kilo_new_rules_dir, kilo_new_output_filename)
        save_kilo_code_instructions(kilo_code_instructions_content, kilo_new_output_path)

        # Google Antigravity output structure: base_for_output/.agent/rules/original_filename.md
        antigravity_rules_dir = os.path.join(base_for_output, ".agent", "rules")
        antigravity_output_filename = input_file_base + ".md"
        antigravity_output_path = os.path.join(antigravity_rules_dir, antigravity_output_filename)
        save_antigravity_instructions(antigravity_instructions_content, antigravity_output_path)

        # Qwen Code output structure: base_for_output/.qwen/ with QWEN.md master file and individual rule files
        # See: https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/
        qwen_rules_dir = os.path.join(base_for_output, ".qwen")
        qwen_master_file_path = os.path.join(qwen_rules_dir, "QWEN.md")
        qwen_code_output_filename = input_file_base + ".md"
        qwen_code_output_path = os.path.join(qwen_rules_dir, qwen_code_output_filename)
        save_qwen_code_instructions(qwen_code_instructions_content, qwen_code_output_path)

        relative_path_for_qwen_import = os.path.relpath(qwen_code_output_path, qwen_rules_dir)
        with open(qwen_master_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Qwen Code Rules\n\n@{relative_path_for_qwen_import}\n")

        # Claude Code output structure: base_for_output/.claude/rules/original_filename.md
        # with .claude/CLAUDE.md master file importing rules via @rules/filename.md
        # See: https://code.claude.com/docs/en/memory
        claude_rules_dir = os.path.join(base_for_output, ".claude", "rules")
        claude_master_file_path = os.path.join(base_for_output, ".claude", "CLAUDE.md")
        claude_code_output_filename = input_file_base + ".md"
        claude_code_output_path = os.path.join(claude_rules_dir, claude_code_output_filename)
        save_claude_code_instructions(claude_code_instructions_content, claude_code_output_path)

        relative_path_for_claude_import = os.path.relpath(claude_code_output_path, os.path.join(base_for_output, ".claude"))
        os.makedirs(os.path.dirname(claude_master_file_path), exist_ok=True)
        with open(claude_master_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Claude Code Rules\n\n@{relative_path_for_claude_import}\n")

        # OpenAI Codex output structure: base_for_output/AGENTS.md (single file at project root)
        # See: https://developers.openai.com/codex/guides/agents-md
        codex_output_path = os.path.join(base_for_output, "AGENTS.md")
        save_codex_instructions(codex_instructions_content, codex_output_path)

        # ZCode output structure: base_for_output/AGENTS.md (single file at project root).
        # ZCode and Codex share an identical AGENTS.md (plain markdown, no frontmatter),
        # so they reference the same file rather than writing a duplicate.
        # See: https://zcode.z.ai/en/docs/agents
        zcode_output_path = codex_output_path

        # Write kilo.jsonc with instructions referencing .kilo/rules/ directory
        kilo_rule_files_convert_file = [kilo_new_output_path]
        write_kilo_json(base_for_output, kilo_rule_files_convert_file)

        return (vscode_output_path, roo_output_path, windsurf_output_path,
                cline_output_path, gemini_master_file_path, kilo_code_output_path,
                antigravity_output_path, qwen_master_file_path, claude_master_file_path,
                codex_output_path, zcode_output_path)
    except Exception as e:
        print(f"Error converting {input_path_abs}: {str(e)}")
        raise


def copy_file(input_path: str, output_dir: str, output_name: Optional[str] = None) -> str:
    """
    Copy a file from the input path to the output directory.
    
    Args:
        input_path: Path to the input file
        output_dir: Directory to save the output file
        output_name: Optional output filename to use in the destination directory

    Returns:
        Path to the copied file
    """
    # Create output directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    
    if output_name is None:
        output_name = os.path.basename(input_path)
    output_path = os.path.join(output_dir, output_name)
    
    # Copy the file
    with open(input_path, 'rb') as source_file:
        with open(output_path, 'wb') as dest_file:
            dest_file.write(source_file.read())
            
    return output_path


def convert_directory(input_dir_str: str, output_dir_str: Optional[str] = None) -> Tuple[List[str], List[str], List[str], List[str], List[str], List[str], List[str], List[str], List[str], List[str], List[str], List[str]]:
    """
    Convert all template files in a directory and its subdirectories.
    Input directory should contain processed template files (from Stage 1).
    Converts files to all target formats (VS Code, Roo Code, Windsurf, Cline, Gemini,
    Kilo Code, Antigravity, Qwen Code, Claude Code, Codex, ZCode).
    Also copies non-template files to the output directory.

    Args:
        input_dir_str: Directory containing processed template files (cooked-rules-template).
        output_dir_str: Directory to save output files.

    Returns:
        Tuple containing lists of converted file paths for each format and copied files:
        (vscode, roo, windsurf, cline, gemini_cli, kilo_code, antigravity,
         qwen_code, claude_code, codex, zcode, copied_files)
    """
    input_dir_abs = os.path.abspath(input_dir_str)
    vscode_converted_files = []
    roo_converted_files = []
    windsurf_converted_files = []
    cline_converted_files = []
    gemini_cli_converted_files = []
    kilo_code_converted_files = []
    antigravity_converted_files = []
    qwen_code_converted_files = []
    claude_code_converted_files = []
    codex_converted_files = []
    zcode_converted_files = []
    copied_files = []

    if not os.path.isdir(input_dir_abs):
        print(f"Info: Input directory not found at {input_dir_abs}. No files will be converted from this path.")
        return [], [], [], [], [], [], [], [], [], [], [], []

    # Use provided output directory or the parent of input directory
    if output_dir_str:
        base_for_output = os.path.abspath(output_dir_str)
    else:
        base_for_output = os.path.dirname(input_dir_abs)

    gemini_rules_dir = os.path.join(base_for_output, ".gemini")
    gemini_master_file_path = os.path.join(gemini_rules_dir, "GEMINI.md")
    gemini_master_file_content = ["# Gemini CLI Rules\n\n"]

    # Qwen Code: .qwen/ directory with QWEN.md master file and @import syntax
    # See: https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/
    qwen_rules_dir = os.path.join(base_for_output, ".qwen")
    qwen_master_file_path = os.path.join(qwen_rules_dir, "QWEN.md")
    qwen_master_file_content = ["# Qwen Code Rules\n\n"]

    # Claude Code: .claude/ directory with CLAUDE.md master file and .claude/rules/ for rule files
    # See: https://code.claude.com/docs/en/memory
    claude_base_dir = os.path.join(base_for_output, ".claude")
    claude_master_file_path = os.path.join(claude_base_dir, "CLAUDE.md")
    claude_master_file_content = ["# Claude Code Rules\n\n"]

    # OpenAI Codex: AGENTS.md at project root, all rules concatenated
    # See: https://developers.openai.com/codex/guides/agents-md
    codex_output_path = os.path.join(base_for_output, "AGENTS.md")
    codex_all_content_parts = []

    for root, _, files in os.walk(input_dir_abs):
        for file in files:
            input_file_path = os.path.join(root, file)

            # rel_path is relative to input_dir_abs to preserve structure in output directories
            rel_path_from_input = os.path.relpath(root, input_dir_abs)
            if rel_path_from_input == '.':
                rel_path_from_input = ''

            normalized_rel_path_from_input = normalize_relative_path(rel_path_from_input)

            # Process template files (.mdc files)
            if file.endswith(".mdc"):
                mdc_content = parse_mdc_file(input_file_path)
                vscode_instructions_content = convert_to_vscode_instructions(mdc_content)
                roo_instructions_content = convert_to_roo_instructions(mdc_content)
                windsurf_instructions_content = convert_to_windsurf_instructions(mdc_content)
                cline_instructions_content = convert_to_cline_instructions(mdc_content)
                gemini_cli_instructions_content = convert_to_gemini_cli_instructions(mdc_content)
                kilo_code_instructions_content = convert_to_kilo_code_instructions(mdc_content)
                antigravity_instructions_content = convert_to_antigravity_instructions(mdc_content)
                qwen_code_instructions_content = convert_to_qwen_code_instructions(mdc_content)
                claude_code_instructions_content = convert_to_claude_code_instructions(mdc_content)
                codex_instructions_content = convert_to_codex_instructions(mdc_content)

                # Determine output paths maintaining directory structure
                # VS Code: base_for_output / .github / instructions / rel_path_from_input / filename.instructions.md
                vscode_output_instructions_subdir = os.path.join(base_for_output, ".github", "instructions", normalized_rel_path_from_input)
                vscode_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".instructions.md"
                vscode_output_path = os.path.join(vscode_output_instructions_subdir, vscode_output_filename)
                save_vscode_instructions(vscode_instructions_content, vscode_output_path)
                vscode_converted_files.append(vscode_output_path)

                # Roo Code: base_for_output / .roo / rules / rel_path_from_input / filename.md
                roo_output_rules_subdir = os.path.join(base_for_output, ".roo", "rules", normalized_rel_path_from_input)
                roo_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".md"
                roo_output_path = os.path.join(roo_output_rules_subdir, roo_output_filename)
                save_roo_instructions(roo_instructions_content, roo_output_path)
                roo_converted_files.append(roo_output_path)

                # Windsurf: base_for_output / .windsurf / rules / rel_path_from_input / filename.md
                windsurf_output_rules_subdir = os.path.join(base_for_output, ".windsurf", "rules", normalized_rel_path_from_input)
                windsurf_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".md"
                windsurf_output_path = os.path.join(windsurf_output_rules_subdir, windsurf_output_filename)
                save_windsurf_instructions(windsurf_instructions_content, windsurf_output_path)
                windsurf_converted_files.append(windsurf_output_path)

                # Cline: base_for_output / .clinerules / rel_path_from_input / filename.md
                cline_output_rules_subdir = os.path.join(base_for_output, ".clinerules", normalized_rel_path_from_input)
                cline_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".md"
                cline_output_path = os.path.join(cline_output_rules_subdir, cline_output_filename)
                save_cline_instructions(cline_instructions_content, cline_output_path)
                cline_converted_files.append(cline_output_path)

                # Gemini CLI: base_for_output / .gemini / rel_path_from_input / filename.md
                gemini_cli_output_rules_subdir = os.path.join(base_for_output, ".gemini", normalized_rel_path_from_input)
                gemini_cli_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".md"
                gemini_cli_output_path = os.path.join(gemini_cli_output_rules_subdir, gemini_cli_output_filename)
                save_gemini_cli_instructions(gemini_cli_instructions_content, gemini_cli_output_path)
                gemini_cli_converted_files.append(gemini_cli_output_path)

                # Kilo Code: base_for_output / .kilocode / rules / filename.md (legacy)
                kilo_code_output_rules_subdir = os.path.join(base_for_output, ".kilocode", "rules")
                kilo_code_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".md"
                kilo_code_output_path = os.path.join(kilo_code_output_rules_subdir, kilo_code_output_filename)
                save_kilo_code_instructions(kilo_code_instructions_content, kilo_code_output_path)
                kilo_code_converted_files.append(kilo_code_output_path)

                # Kilo Code: base_for_output / .kilo / rules / filename.md (current standard per docs)
                kilo_rules_subdir = os.path.join(base_for_output, ".kilo", "rules")
                kilo_rules_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".md"
                kilo_rules_output_path = os.path.join(kilo_rules_subdir, kilo_rules_output_filename)
                save_kilo_code_instructions(kilo_code_instructions_content, kilo_rules_output_path)
                kilo_code_converted_files.append(kilo_rules_output_path)

                # Add import statement to Gemini master file
                relative_path_for_import = os.path.relpath(gemini_cli_output_path, gemini_rules_dir)
                gemini_master_file_content.append(f"@{relative_path_for_import}\n")

                # Google Antigravity: base_for_output / .agent / rules / rel_path_from_input / filename.md
                antigravity_output_rules_subdir = os.path.join(base_for_output, ".agent", "rules", normalized_rel_path_from_input)
                antigravity_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".md"
                antigravity_output_path = os.path.join(antigravity_output_rules_subdir, antigravity_output_filename)
                save_antigravity_instructions(antigravity_instructions_content, antigravity_output_path)
                antigravity_converted_files.append(antigravity_output_path)

                # Qwen Code: base_for_output / .qwen / rel_path_from_input / filename.md
                qwen_code_output_rules_subdir = os.path.join(base_for_output, ".qwen", normalized_rel_path_from_input)
                qwen_code_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".md"
                qwen_code_output_path = os.path.join(qwen_code_output_rules_subdir, qwen_code_output_filename)
                save_qwen_code_instructions(qwen_code_instructions_content, qwen_code_output_path)
                qwen_code_converted_files.append(qwen_code_output_path)

                # Add import statement to Qwen master file
                relative_path_for_qwen_import = os.path.relpath(qwen_code_output_path, qwen_rules_dir)
                qwen_master_file_content.append(f"@{relative_path_for_qwen_import}\n")

                # Claude Code: base_for_output / .claude / rules / rel_path_from_input / filename.md
                claude_code_output_rules_subdir = os.path.join(base_for_output, ".claude", "rules", normalized_rel_path_from_input)
                claude_code_output_filename = normalize_file_base_name(os.path.splitext(os.path.basename(input_file_path))[0]) + ".md"
                claude_code_output_path = os.path.join(claude_code_output_rules_subdir, claude_code_output_filename)
                save_claude_code_instructions(claude_code_instructions_content, claude_code_output_path)
                claude_code_converted_files.append(claude_code_output_path)

                # Add import statement to Claude master file
                relative_path_for_claude_import = os.path.relpath(claude_code_output_path, claude_base_dir)
                claude_master_file_content.append(f"@{relative_path_for_claude_import}\n")

                # OpenAI Codex: collect content for single AGENTS.md
                codex_all_content_parts.append(codex_instructions_content)

                # ZCode shares the identical AGENTS.md written for Codex below
                # (plain markdown, no frontmatter), so no separate content is collected.

            else:
                # Copy non-template files maintaining directory structure
                # base_for_output / rel_path_from_input / file
                file_output_dir_specific = os.path.join(base_for_output, normalized_rel_path_from_input)
                output_path = copy_file(
                    input_file_path,
                    file_output_dir_specific,
                    output_name=normalize_file_name(os.path.basename(input_file_path))
                )
                copied_files.append(output_path)

    # Write Gemini master file
    os.makedirs(os.path.dirname(gemini_master_file_path), exist_ok=True)
    with open(gemini_master_file_path, 'w', encoding='utf-8') as f:
        f.write("".join(gemini_master_file_content))
    gemini_cli_converted_files.append(gemini_master_file_path)

    # Write Qwen Code master file
    os.makedirs(os.path.dirname(qwen_master_file_path), exist_ok=True)
    with open(qwen_master_file_path, 'w', encoding='utf-8') as f:
        f.write("".join(qwen_master_file_content))
    qwen_code_converted_files.append(qwen_master_file_path)

    # Write Claude Code master file
    os.makedirs(os.path.dirname(claude_master_file_path), exist_ok=True)
    with open(claude_master_file_path, 'w', encoding='utf-8') as f:
        f.write("".join(claude_master_file_content))
    claude_code_converted_files.append(claude_master_file_path)

    # Write OpenAI Codex AGENTS.md (all rules concatenated)
    os.makedirs(os.path.dirname(codex_output_path), exist_ok=True)
    with open(codex_output_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(codex_all_content_parts))
    codex_converted_files.append(codex_output_path)

    # ZCode shares the identical AGENTS.md written for Codex above (plain markdown,
    # no frontmatter), so reference the same path rather than writing a duplicate.
    # See: https://zcode.z.ai/en/docs/agents
    zcode_converted_files.append(codex_output_path)

    # Write Kilo Code kilo.jsonc with instructions referencing rules directory
    kilo_rule_files = [f for f in kilo_code_converted_files if "/.kilo/rules/" in f.replace("\\", "/")]
    if kilo_rule_files:
        kilo_json_path = write_kilo_json(base_for_output, kilo_rule_files)
        kilo_code_converted_files.append(kilo_json_path)

    return (vscode_converted_files, roo_converted_files, windsurf_converted_files,
            cline_converted_files, gemini_cli_converted_files, kilo_code_converted_files,
            antigravity_converted_files, qwen_code_converted_files, claude_code_converted_files,
            codex_converted_files, zcode_converted_files, copied_files)