"""
Safety validations for FileDelete CLI tool.
Prevents accidental mass deletions in dangerous locations.
"""

import os
import sys
from pathlib import Path
from typing import Set, Optional

from .types import DANGEROUS_PATHS_WINDOWS, DANGEROUS_PATHS_LINUX, ExitCode

def is_windows() -> bool:
    """Check if running on Windows."""
    return os.name == 'nt'

def get_dangerous_paths() -> Set[str]:
    """Get the appropriate set of dangerous paths for the current OS."""
    return DANGEROUS_PATHS_WINDOWS if is_windows() else DANGEROUS_PATHS_LINUX

def is_dangerous_path(path: Path) -> bool:
    """
    Check if a path is considered dangerous for deletion operations.
    
    Args:
        path: Path to check
        
    Returns:
        bool: True if path is dangerous, False otherwise
    """
    path_str = str(path.resolve())
    dangerous_paths = get_dangerous_paths()

    # Normalize case on Windows for comparisons
    path_cmp = path_str.lower() if is_windows() else path_str

    # Evaluate against dangerous paths
    for dp in dangerous_paths:
        dp_norm = dp.rstrip('\\/')
        dp_cmp = dp_norm.lower() if is_windows() else dp_norm

        # Drive root (e.g., C:\) should only block exact match, not subpaths
        is_drive_root = (len(dp_norm) == 2 and dp_norm.endswith(':'))
        if is_drive_root:
            root = dp_norm + os.sep
            root_cmp = root.lower() if is_windows() else root
            if path_cmp == root_cmp:
                return True
            continue

        # System or critical directories: block equal or subpaths
        if path_cmp == dp_cmp or path_cmp.startswith(dp_cmp + os.sep):
            return True
    
    # Check for root-level paths (like C:\, D:\, etc.)
    if is_windows():
        # Check for drive roots (C:\, D:\, etc.)
        if len(path_str) == 3 and path_str[1:3] == ':\\' and path_str[0].isalpha():
            return True
        # Check for UNC roots (\\server\share)
        if path_str.startswith('\\\\') and path_str.count('\\') <= 3:
            return True
    else:
        # Check for Unix root
        if path_str == '/':
            return True
        # Check for very shallow paths (like /bin, /etc, etc.)
        if path_str.count('/') < 2:
            return True
    
    return False

def validate_path_safety(path: Path, max_delete_threshold: int = 100) -> Optional[ExitCode]:
    """
    Validate that a path is safe for deletion operations.
    
    Args:
        path: Path to validate
        max_delete_threshold: Maximum number of files that can be deleted without confirmation
        
    Returns:
        ExitCode or None: Exit code if validation fails, None if safe
    """
    # Check if path exists
    if not path.exists():
        print(f"Error: Path '{path}' does not exist.", file=sys.stderr)
        return ExitCode.INVALID_ARGUMENTS
    
    # Check if path is a directory
    if not path.is_dir():
        print(f"Error: Path '{path}' is not a directory.", file=sys.stderr)
        return ExitCode.INVALID_ARGUMENTS
    
    # Check for dangerous paths
    if is_dangerous_path(path):
        print(f"Error: Path '{path}' is considered dangerous for deletion operations.", file=sys.stderr)
        print("This tool blocks operations on system roots and critical directories.", file=sys.stderr)
        return ExitCode.SAFETY_BLOCKED
    
    # Check path depth (additional safety measure)
    # Allow current directory and test directories for development
    path_parts = path.parts
    if len(path_parts) < 2 and not any(part.startswith('.') or part == 'test-data' for part in path_parts):
        print(f"Error: Path '{path}' is too shallow (depth: {len(path_parts)}).", file=sys.stderr)
        print("Minimum path depth requirement not met for safety.", file=sys.stderr)
        return ExitCode.SAFETY_BLOCKED
    
    # Allow test directories for development
    if 'test-data' in path.parts:
        return None
    
    return None

def confirm_large_operation(file_count: int, max_delete_threshold: int) -> bool:
    """
    Confirm with user if operation affects many files.
    
    Args:
        file_count: Number of files that would be affected
        max_delete_threshold: Threshold for requiring confirmation
        
    Returns:
        bool: True if operation should proceed, False if cancelled
    """
    if file_count <= max_delete_threshold:
        return True
    
    print(f"Warning: This operation would affect {file_count} files.")
    print(f"This exceeds the safety threshold of {max_delete_threshold} files.")
    
    try:
        response = input("Do you want to continue? (y/N): ").strip().lower()
        return response in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user.", file=sys.stderr)
        return False
