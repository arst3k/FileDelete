"""
Command-line interface for FileDelete tool.
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import List, Optional

from .core import FileDelete, parse_size_string, parse_date_string
from .safety import validate_path_safety, confirm_large_operation
from .types import ExitCode, TimeField, DEFAULT_MAX_DELETE

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configure logging for the application."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Secure file deletion tool with configurable filters",
        epilog="Example: filedelete --path ./logs --recursive --ext log --older-than-days 30 --dry-run"
    )
    
    # Required arguments
    parser.add_argument(
        "--path", 
        type=Path,
        required=True,
        help="Base directory path to search for files (required)"
    )
    
    # Search scope
    parser.add_argument(
        "--recursive", 
        action="store_true",
        help="Search recursively in subdirectories"
    )
    
    # Date filters
    date_group = parser.add_argument_group("Date filters")
    date_group.add_argument(
        "--older-than-days",
        type=int,
        help="Delete files older than N days"
    )
    date_group.add_argument(
        "--before-date",
        type=str,
        help="Delete files before date (DD-MM-YYYY format)"
    )
    date_group.add_argument(
        "--time-field",
        type=TimeField,
        choices=list(TimeField),
        default=TimeField.MTIME,
        help="Time field to use for age comparison (default: mtime)"
    )
    
    # Extension filters
    parser.add_argument(
        "--ext",
        action="append",
        default=[],
        help="File extension to include (can be used multiple times)"
    )
    
    # Size filters
    size_group = parser.add_argument_group("Size filters")
    size_group.add_argument(
        "--min-size",
        type=str,
        help="Minimum file size (e.g., 10K, 5M, 1G)"
    )
    size_group.add_argument(
        "--max-size",
        type=str,
        help="Maximum file size (e.g., 10K, 5M, 1G)"
    )
    
    # Pattern filters
    pattern_group = parser.add_argument_group("Pattern filters")
    pattern_group.add_argument(
        "--include-glob",
        action="append",
        default=[],
        help="Glob pattern to include (can be used multiple times)"
    )
    pattern_group.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="Glob pattern to exclude (can be used multiple times)"
    )
    pattern_group.add_argument(
        "--name-regex",
        type=str,
        help="Regex pattern for filename matching"
    )
    pattern_group.add_argument(
        "--regex-flags",
        type=str,
        default="",
        help="Regex flags (comma-separated, e.g., IGNORECASE,MULTILINE)"
    )
    
    # Execution mode
    mode_group = parser.add_argument_group("Execution mode")
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate deletion without actually deleting (default)"
    )
    mode_group.add_argument(
        "--apply",
        "--yes",
        action="store_true",
        dest="apply",
        help="Actually delete files (requires confirmation for large operations)"
    )
    mode_group.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts (use with caution)"
    )
    mode_group.add_argument(
        "--no-prompt",
        action="store_true",
        help="Non-interactive mode (will abort if confirmation needed)"
    )
    mode_group.add_argument(
        "--max-delete",
        type=int,
        default=DEFAULT_MAX_DELETE,
        help=f"Maximum files to delete without confirmation (default: {DEFAULT_MAX_DELETE})"
    )
    
    # Directory cleanup
    parser.add_argument(
        "--delete-empty-dirs",
        action="store_true",
        help="Delete empty directories after file deletion"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output options")
    output_group.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    output_group.add_argument(
        "--log-file",
        type=str,
        help="Log file path"
    )
    output_group.add_argument(
        "--summary-only",
        action="store_true",
        help="Only show summary at the end"
    )
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    return parser.parse_args()

def parse_regex_flags(flags_str: str) -> int:
    """Parse regex flags from comma-separated string."""
    flags = 0
    if not flags_str:
        return flags
    
    flag_map = {
        "IGNORECASE": re.IGNORECASE,
        "I": re.IGNORECASE,
        "MULTILINE": re.MULTILINE,
        "M": re.MULTILINE,
        "DOTALL": re.DOTALL,
        "S": re.DOTALL,
        "VERBOSE": re.VERBOSE,
        "X": re.VERBOSE,
    }
    
    for flag_name in flags_str.split(','):
        flag_name = flag_name.strip().upper()
        if flag_name in flag_map:
            flags |= flag_map[flag_name]
        else:
            logging.warning(f"Unknown regex flag: {flag_name}")
    
    return flags

def main() -> int:
    """Main entry point for the CLI tool."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate path safety
        safety_result = validate_path_safety(args.path, args.max_delete)
        if safety_result:
            return safety_result.value
        
        # Create file delete instance
        file_delete = FileDelete(args.path, args.recursive)
        
        # Add filters
        if args.ext:
            file_delete.add_extension_filter(args.ext)
        
        if args.older_than_days or args.before_date:
            file_delete.add_age_filter(
                args.older_than_days,
                args.before_date,
                args.time_field
            )
        
        if args.min_size or args.max_size:
            file_delete.add_size_filter(args.min_size, args.max_size)
        
        if args.include_glob or args.exclude_glob:
            file_delete.add_glob_filter(args.include_glob, args.exclude_glob)
        
        if args.name_regex:
            regex_flags = parse_regex_flags(args.regex_flags)
            file_delete.add_regex_filter(args.name_regex, regex_flags)
        
        # Find matching files
        matched_files = file_delete.find_files()
        
        if not matched_files:
            logger.info("No files matched the specified criteria.")
            return ExitCode.NOTHING_TO_DO.value
        
        # Execute operation
        if not args.apply:
            logger.info(f"Dry-run mode: Found {len(matched_files)} files that would be deleted")
            # Use common deletion path in dry-run to keep stats consistent
            deleted, errors = file_delete.delete_files(matched_files, dry_run=True)
        else:
            # Check for large operations
            if not args.force and not args.no_prompt:
                if not confirm_large_operation(len(matched_files), args.max_delete):
                    logger.info("Operation cancelled by user.")
                    return ExitCode.SUCCESS.value
            
            # Actually delete files
            deleted, errors = file_delete.delete_files(matched_files, dry_run=False)
            logger.info(f"Deleted {deleted} files with {errors} errors")
            
            # Optionally remove empty directories
            if args.delete_empty_dirs:
                removed_dirs = file_delete.delete_empty_dirs()
                logger.info(f"Removed {removed_dirs} empty directories")
        
        # Show summary (after operations)
        stats = file_delete.get_stats()
        if not args.summary_only:
            logger.info(f"Summary: Scanned={stats['scanned']}, "
                        f"Matched={stats['matched']}, "
                        f"Deleted={stats['deleted']}, "
                        f"Errors={stats['errors']}")
        
        # Return appropriate exit code
        return ExitCode.PARTIAL_ERRORS.value if stats['errors'] > 0 else ExitCode.SUCCESS.value
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            import traceback
            logger.debug(traceback.format_exc())
        return ExitCode.INVALID_ARGUMENTS.value

if __name__ == "__main__":
    sys.exit(main())
