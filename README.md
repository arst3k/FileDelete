# FileDelete

A secure command-line tool for deleting files with configurable filters and safety protections. Works on both Windows and Linux systems.

## Features

- **Multiple Filter Criteria**: Delete files by age, extension, size, and patterns
- **Safety First**: Blocks operations on system roots and critical directories
- **Dry-run Mode**: Default simulation mode prevents accidental deletions
- **Cross-platform**: Works on Windows and Linux with identical behavior
- **Configurable**: Extensive options for precise file selection

## Installation

Using UV (recommended):

```bash
uv pip install -e .
```

Or with pip:

```bash
pip install -e .
```

## Usage

### Basic Examples

**Dry-run simulation (safe mode):**
```bash
filedelete --path ./logs --recursive --ext log --older-than-days 30 --dry-run
```

**Delete files older than 90 days:**
```bash
filedelete --path /tmp --recursive --before-date 01-01-2024 --apply --max-delete 200
```

**Filter by size and name pattern:**
```bash
filedelete --path ./data --min-size 10M --name-regex "backup_.*" --dry-run
```

### Command Line Options

#### Required Arguments
- `--path PATH`: Base directory path to search (required)

#### Search Scope
- `--recursive`: Search recursively in subdirectories

#### Date Filters
- `--older-than-days N`: Delete files older than N days
- `--before-date DD-MM-YYYY`: Delete files before specific date
- `--time-field {mtime,ctime,atime}`: Time field to use (default: mtime)

#### Extension Filters
- `--ext EXT`: File extension to include (can be used multiple times)

#### Size Filters
- `--min-size SIZE`: Minimum file size (e.g., 10K, 5M, 1G)
- `--max-size SIZE`: Maximum file size (e.g., 10K, 5M, 1G)

#### Pattern Filters
- `--include-glob PATTERN`: Glob pattern to include (multiple allowed)
- `--exclude-glob PATTERN`: Glob pattern to exclude (multiple allowed)
- `--name-regex REGEX`: Regex pattern for filename matching
- `--regex-flags FLAGS`: Regex flags (comma-separated)

#### Execution Mode
- `--dry-run`: Simulate deletion (default)
- `--apply`/`--yes`: Actually delete files
- `--force`: Skip confirmation prompts
- `--no-prompt`: Non-interactive mode
- `--max-delete N`: Maximum files to delete without confirmation (default: 100)

#### Output Options
- `--log-level {DEBUG,INFO,WARNING,ERROR}`: Logging level (default: INFO)
- `--log-file FILE`: Log file path
- `--summary-only`: Only show summary at the end
- `--json`: Output results in JSON format

### Safety Features

The tool includes multiple safety mechanisms:

1. **Dangerous Path Blocking**: Prevents operations on system roots (C:\, /, etc.)
2. **Path Depth Validation**: Requires minimum path depth for safety
3. **Dry-run by Default**: Always starts in simulation mode
4. **Confirmation Threshold**: Asks for confirmation for large operations
5. **Exit Codes**: Detailed exit codes for different scenarios

### Exit Codes

- `0`: Success without errors
- `2`: Invalid arguments
- `3`: Safety block activated (dangerous path)
- `4`: Completed with partial errors
- `5`: Nothing to do (no files matched)

## Development

### Project Structure

```
src/
  filedelete/
    __init__.py      # Package initialization
    cli.py           # Command-line interface
    core.py          # File filtering and deletion logic
    safety.py        # Safety validations
    types.py         # Types and constants
pyproject.toml       # Project configuration
README.md           # This file
```

### Running Tests

```bash
# Run basic functionality tests
python -m pytest tests/ -v

# Test with different log levels
filedelete --path ./test-data --dry-run --log-level DEBUG
```

### Building and Distribution

```bash
# Build package
uv build

# Install locally
uv pip install -e .
```

## Examples

### Delete temporary files older than 7 days
```bash
filedelete --path ~/temp --recursive --older-than-days 7 --apply
```

### Clean up log files larger than 100MB
```bash
filedelete --path /var/log --min-size 100M --ext log --dry-run
```

### Remove specific backup patterns
```bash
filedelete --path ./backups --include-glob "*.bak" --include-glob "*.tmp" --apply
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security

Please report any security issues through appropriate channels. This tool is designed with safety in mind but should always be used with caution when performing file deletion operations.
