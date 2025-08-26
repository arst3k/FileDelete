"""
FileDelete - A secure CLI tool for deleting files with configurable filters.

This package provides a command-line interface for safely deleting files
based on various criteria like age, extension, size, and patterns.
"""

__version__ = "0.1.0"
__author__ = "arst3k"
__description__ = "Secure file deletion tool with configurable filters"

# Import main components for easier access
from .cli import main
from .core import FileDelete
from .safety import is_dangerous_path, validate_path_safety

__all__ = [
    'main',
    'FileDelete',
    'is_dangerous_path',
    'validate_path_safety',
]
