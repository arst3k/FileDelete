"""
Types and constants for FileDelete CLI tool.
"""

from enum import Enum
from typing import List, Optional, Set, Tuple, Union
from pathlib import Path
import re

# Exit codes
class ExitCode(int, Enum):
    SUCCESS = 0
    INVALID_ARGUMENTS = 2
    SAFETY_BLOCKED = 3
    PARTIAL_ERRORS = 4
    NOTHING_TO_DO = 5

# Time field options
class TimeField(str, Enum):
    MTIME = "mtime"  # Modification time (default)
    CTIME = "ctime"  # Change time (metadata change)
    ATIME = "atime"  # Access time

# Dangerous paths that should never be deleted from
DANGEROUS_PATHS_WINDOWS = {
    "C:\\",
    "D:\\", 
    "E:\\",
    "F:\\",
    "G:\\",
    "H:\\",
    "I:\\",
    "J:\\",
    "K:\\",
    "L:\\",
    "M:\\",
    "N:\\",
    "O:\\",
    "P:\\",
    "Q:\\",
    "R:\\",
    "S:\\",
    "T:\\",
    "U:\\",
    "V:\\",
    "W:\\",
    "X:\\",
    "Y:\\",
    "Z:\\",
    # System directories (block system folders but allow user folders)
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\System Volume Information",
}

DANGEROUS_PATHS_LINUX = {
    "/",
    "/bin",
    "/sbin",
    "/etc",
    "/usr",
    "/var",
    "/opt",
    "/root",
    "/lib",
    "/lib64",
    "/boot",
    "/dev",
    "/proc",
    "/sys",
    "/tmp",  # Warning but not necessarily blocked
    "/var/log",
}

# Default maximum delete threshold before confirmation
DEFAULT_MAX_DELETE = 100

# Size units mapping
SIZE_UNITS = {
    'K': 1024,
    'M': 1024 * 1024,
    'G': 1024 * 1024 * 1024,
    'T': 1024 * 1024 * 1024 * 1024,
}

# Common file extensions for reference
COMMON_EXTENSIONS = {
    'log', 'txt', 'csv', 'json', 'xml', 'yaml', 'yml',
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg',
    'mp3', 'mp4', 'avi', 'mov', 'wmv', 'flv',
    'zip', 'rar', 'tar', 'gz', '7z',
    'py', 'js', 'java', 'c', 'cpp', 'h', 'html', 'css',
    'exe', 'dll', 'so', 'dylib',
}

# Type aliases
PathLike = Union[str, Path]
SizeSpec = Union[int, str]
DateSpec = Union[str]  # DD-MM-YYYY format
