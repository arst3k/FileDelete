"""
Core file filtering and deletion logic for FileDelete CLI tool.
"""

import fnmatch
import logging
import re
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from .types import SizeSpec, DateSpec, TimeField, SIZE_UNITS, ExitCode

logger = logging.getLogger(__name__)

class FileDelete:
    """Main class for file deletion operations with configurable filters."""
    
    def __init__(self, base_path: Path, recursive: bool = False):
        self.base_path = base_path.resolve()
        self.recursive = recursive
        self.filters: List[Callable[[Path], bool]] = []
        self.file_counters = {
            'scanned': 0,
            'matched': 0,
            'deleted': 0,
            'errors': 0
        }
    
    def add_extension_filter(self, extensions: List[str]) -> None:
        """Add filter for file extensions."""
        if not extensions:
            return
            
        ext_set = {ext.lower().lstrip('.') for ext in extensions}
        
        def extension_filter(file_path: Path) -> bool:
            if not file_path.is_file():
                return False
            file_ext = file_path.suffix.lower().lstrip('.')
            return file_ext in ext_set
        
        self.filters.append(extension_filter)
        logger.debug(f"Added extension filter for: {ext_set}")
    
    def add_age_filter(self, older_than_days: Optional[int] = None, 
                      before_date: Optional[DateSpec] = None,
                      time_field: TimeField = TimeField.MTIME) -> None:
        """Add filter based on file age."""
        if not older_than_days and not before_date:
            return
            
        cutoff_time = None
        
        if older_than_days:
            cutoff_time = time.time() - (older_than_days * 24 * 3600)
        elif before_date:
            try:
                cutoff_date = datetime.strptime(before_date, "%d-%m-%Y")
                cutoff_time = cutoff_date.timestamp()
            except ValueError:
                logger.error(f"Invalid date format: {before_date}. Expected DD-MM-YYYY.")
                return
        
        def age_filter(file_path: Path) -> bool:
            if not file_path.is_file():
                return False
            
            try:
                if time_field == TimeField.MTIME:
                    file_time = file_path.stat().st_mtime
                elif time_field == TimeField.CTIME:
                    file_time = file_path.stat().st_ctime
                elif time_field == TimeField.ATIME:
                    file_time = file_path.stat().st_atime
                else:
                    file_time = file_path.stat().st_mtime
                
                return file_time < cutoff_time
            except (OSError, PermissionError):
                logger.warning(f"Could not access file time for: {file_path}")
                return False
        
        self.filters.append(age_filter)
        logger.debug(f"Added age filter: {time_field} before {cutoff_time}")
    
    def add_size_filter(self, min_size: Optional[SizeSpec] = None, 
                       max_size: Optional[SizeSpec] = None) -> None:
        """Add filter based on file size."""
        if not min_size and not max_size:
            return
            
        def parse_size(size_spec: SizeSpec) -> int:
            if isinstance(size_spec, int):
                return size_spec
                
            size_spec = str(size_spec).upper().strip()
            if size_spec[-1] in SIZE_UNITS:
                unit = size_spec[-1]
                number = size_spec[:-1]
                return int(number) * SIZE_UNITS[unit]
            return int(size_spec)
        
        min_bytes = parse_size(min_size) if min_size else 0
        max_bytes = parse_size(max_size) if max_size else float('inf')
        
        def size_filter(file_path: Path) -> bool:
            if not file_path.is_file():
                return False
            
            try:
                file_size = file_path.stat().st_size
                return min_bytes <= file_size <= max_bytes
            except (OSError, PermissionError):
                logger.warning(f"Could not access file size for: {file_path}")
                return False
        
        self.filters.append(size_filter)
        logger.debug(f"Added size filter: {min_bytes} <= size <= {max_bytes}")
    
    def add_glob_filter(self, include_patterns: List[str], 
                       exclude_patterns: List[str]) -> None:
        """Add filter based on glob patterns."""
        if not include_patterns and not exclude_patterns:
            return
            
        def glob_filter(file_path: Path) -> bool:
            if not file_path.is_file():
                return False
            
            filename = file_path.name
            
            # Include patterns (whitelist)
            if include_patterns:
                included = any(fnmatch.fnmatch(filename, pattern) for pattern in include_patterns)
                if not included:
                    return False
            
            # Exclude patterns (blacklist)
            if exclude_patterns:
                excluded = any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns)
                if excluded:
                    return False
            
            return True
        
        self.filters.append(glob_filter)
        logger.debug(f"Added glob filter: include={include_patterns}, exclude={exclude_patterns}")
    
    def add_regex_filter(self, pattern: str, flags: int = 0) -> None:
        """Add filter based on regex pattern."""
        if not pattern:
            return
            
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {pattern} - {e}")
            return
        
        def regex_filter(file_path: Path) -> bool:
            if not file_path.is_file():
                return False
            return bool(regex.search(file_path.name))
        
        self.filters.append(regex_filter)
        logger.debug(f"Added regex filter: {pattern}")
    
    def apply_filters(self, file_path: Path) -> bool:
        """Apply all filters to a file path."""
        if not self.filters:
            return file_path.is_file()
        
        for filter_func in self.filters:
            if not filter_func(file_path):
                return False
        return True
    
    def find_files(self) -> List[Path]:
        """Find all files that match the configured filters."""
        matched_files = []
        
        if self.recursive:
            file_iter = self.base_path.rglob('*')
        else:
            file_iter = self.base_path.iterdir()
        
        for item in file_iter:
            self.file_counters['scanned'] += 1
            
            if self.apply_filters(item):
                matched_files.append(item)
                self.file_counters['matched'] += 1
                logger.debug(f"Matched: {item}")
        
        return matched_files
    
    def delete_files(self, files: List[Path], dry_run: bool = True) -> Tuple[int, int]:
        """Delete matched files (or simulate deletion in dry-run mode)."""
        deleted = 0
        errors = 0
        
        for file_path in files:
            try:
                if dry_run:
                    logger.info(f"[DRY-RUN] Would delete: {file_path}")
                    deleted += 1
                else:
                    file_path.unlink()
                    logger.info(f"Deleted: {file_path}")
                    deleted += 1
            except (OSError, PermissionError) as e:
                logger.error(f"Error deleting {file_path}: {e}")
                errors += 1
        
        self.file_counters['deleted'] += deleted
        self.file_counters['errors'] += errors
        
        return deleted, errors
    
    def get_stats(self) -> Dict[str, int]:
        """Get current statistics."""
        return self.file_counters.copy()
    
    def reset_stats(self) -> None:
        """Reset all counters."""
        self.file_counters = {
            'scanned': 0,
            'matched': 0,
            'deleted': 0,
            'errors': 0
        }

    def delete_empty_dirs(self) -> int:
        """
        Remove empty directories under base_path (post-order).
        Returns the number of directories removed.
        """
        removed = 0
        try:
            for dirpath, dirnames, filenames in os.walk(self.base_path, topdown=False):
                # Skip the base path itself if desired? We'll allow removing subdirs only
                path_obj = Path(dirpath)
                if path_obj == self.base_path:
                    continue
                # If no files and no subdirs remain, remove this directory
                if not dirnames and not filenames:
                    try:
                        path_obj.rmdir()
                        removed += 1
                        logger.info(f"Removed empty directory: {path_obj}")
                    except (OSError, PermissionError) as e:
                        logger.debug(f"Could not remove directory {path_obj}: {e}")
            return removed
        except Exception as e:
            logger.debug(f"Error while removing empty directories: {e}")
            return removed

def parse_size_string(size_str: str) -> int:
    """Parse a size string with optional unit suffix."""
    size_str = size_str.upper().strip()
    
    if size_str[-1] in SIZE_UNITS:
        unit = size_str[-1]
        number = size_str[:-1]
        return int(number) * SIZE_UNITS[unit]
    
    return int(size_str)

def parse_date_string(date_str: str) -> datetime:
    """Parse a date string in DD-MM-YYYY format."""
    return datetime.strptime(date_str, "%d-%m-%Y")
