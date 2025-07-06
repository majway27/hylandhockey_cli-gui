#!/usr/bin/env python3
"""
File Utilities for Hyland Hockey Jersey Order Management System

This module provides common filesystem operations and utilities for file management.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class FileUtils:
    """Utility class for common file operations."""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human readable format.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            Formatted size string (e.g., "1.5 MB", "256 KB")
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def get_file_info(file_path: Path) -> Dict[str, any]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file information
        """
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'path': file_path,
                'size': stat.st_size,
                'size_formatted': FileUtils.format_file_size(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'created_str': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'exists': True,
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir(),
                'extension': file_path.suffix.lower(),
            }
        except (OSError, FileNotFoundError):
            return {
                'name': file_path.name,
                'path': file_path,
                'size': 0,
                'size_formatted': '0 B',
                'modified': None,
                'modified_str': 'Unknown',
                'created': None,
                'created_str': 'Unknown',
                'exists': False,
                'is_file': False,
                'is_dir': False,
                'extension': file_path.suffix.lower(),
            }
    
    @staticmethod
    def list_files(directory: Path, pattern: str = "*", sort_by: str = "modified", 
                   reverse: bool = True) -> List[Dict[str, any]]:
        """
        List files in a directory with detailed information.
        
        Args:
            directory: Directory to search
            pattern: File pattern to match (e.g., "*.csv", "*.log")
            sort_by: Sort criteria ("name", "size", "modified", "created")
            reverse: Whether to sort in reverse order
            
        Returns:
            List of file information dictionaries
        """
        if not directory.exists():
            return []
        
        files = []
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                file_info = FileUtils.get_file_info(file_path)
                files.append(file_info)
        
        # Sort files
        if sort_by == "name":
            files.sort(key=lambda x: x['name'], reverse=reverse)
        elif sort_by == "size":
            files.sort(key=lambda x: x['size'], reverse=reverse)
        elif sort_by == "modified":
            files.sort(key=lambda x: x['modified'] or datetime.min, reverse=reverse)
        elif sort_by == "created":
            files.sort(key=lambda x: x['created'] or datetime.min, reverse=reverse)
        
        return files
    
    @staticmethod
    def ensure_directory(directory: Path) -> Path:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory: Directory path to ensure
            
        Returns:
            Path to the directory
        """
        directory.mkdir(parents=True, exist_ok=True)
        return directory
    
    @staticmethod
    def safe_delete_file(file_path: Path) -> Tuple[bool, str]:
        """
        Safely delete a file with error handling.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not file_path.exists():
                return False, f"File not found: {file_path}"
            
            if not file_path.is_file():
                return False, f"Path is not a file: {file_path}"
            
            file_path.unlink()
            return True, f"File deleted successfully: {file_path.name}"
            
        except PermissionError:
            return False, f"Permission denied: {file_path}"
        except OSError as e:
            return False, f"Error deleting file: {e}"
    
    @staticmethod
    def safe_copy_file(source: Path, destination: Path, overwrite: bool = False) -> Tuple[bool, str]:
        """
        Safely copy a file with error handling.
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing files
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not source.exists():
                return False, f"Source file not found: {source}"
            
            if not source.is_file():
                return False, f"Source is not a file: {source}"
            
            if destination.exists() and not overwrite:
                return False, f"Destination file exists and overwrite=False: {destination}"
            
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            return True, f"File copied successfully: {source.name} -> {destination}"
            
        except PermissionError:
            return False, f"Permission denied: {source}"
        except OSError as e:
            return False, f"Error copying file: {e}"
    
    @staticmethod
    def get_directory_size(directory: Path) -> Tuple[int, str]:
        """
        Calculate the total size of a directory.
        
        Args:
            directory: Directory to calculate size for
            
        Returns:
            Tuple of (size_in_bytes, formatted_size)
        """
        total_size = 0
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            pass
        
        return total_size, FileUtils.format_file_size(total_size)
    
    @staticmethod
    def find_files_by_extension(directory: Path, extensions: List[str]) -> List[Path]:
        """
        Find all files with specified extensions in a directory.
        
        Args:
            directory: Directory to search
            extensions: List of file extensions (e.g., [".csv", ".xlsx"])
            
        Returns:
            List of matching file paths
        """
        if not directory.exists():
            return []
        
        files = []
        for ext in extensions:
            files.extend(directory.glob(f"*{ext}"))
        
        return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    @staticmethod
    def get_unique_filename(directory: Path, base_name: str, extension: str) -> Path:
        """
        Generate a unique filename in a directory.
        
        Args:
            directory: Directory to create the file in
            base_name: Base name for the file
            extension: File extension (with or without dot)
            
        Returns:
            Path to the unique filename
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        
        counter = 1
        filename = f"{base_name}{extension}"
        file_path = directory / filename
        
        while file_path.exists():
            filename = f"{base_name}_{counter}{extension}"
            file_path = directory / filename
            counter += 1
        
        return file_path


class DownloadManager:
    """Manager for download directories and file organization."""
    
    def __init__(self, base_download_dir: str = "downloads"):
        """
        Initialize the download manager.
        
        Args:
            base_download_dir: Base directory for downloads
        """
        self.base_dir = Path(base_download_dir)
        self.usa_hockey_dir = self.base_dir / "usa_hockey"
        
        # Ensure directories exist
        FileUtils.ensure_directory(self.base_dir)
        FileUtils.ensure_directory(self.usa_hockey_dir)
    
    def get_usa_hockey_files(self, sort_by: str = "modified", reverse: bool = True) -> List[Dict[str, any]]:
        """
        Get all files in the USA Hockey downloads directory.
        
        Args:
            sort_by: Sort criteria
            reverse: Whether to sort in reverse order
            
        Returns:
            List of file information dictionaries
        """
        return FileUtils.list_files(
            self.usa_hockey_dir, 
            pattern="*.csv", 
            sort_by=sort_by, 
            reverse=reverse
        )
    
    def get_download_directory(self, subdirectory: str = None) -> Path:
        """
        Get a download directory path.
        
        Args:
            subdirectory: Optional subdirectory name
            
        Returns:
            Path to the download directory
        """
        if subdirectory:
            download_dir = self.base_dir / subdirectory
            FileUtils.ensure_directory(download_dir)
            return download_dir
        return self.base_dir
    
    def cleanup_old_files(self, directory: Path, days_old: int = 30) -> int:
        """
        Clean up files older than specified days.
        
        Args:
            directory: Directory to clean
            days_old: Age threshold in days
            
        Returns:
            Number of files deleted
        """
        if not directory.exists():
            return 0
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        success, _ = FileUtils.safe_delete_file(file_path)
                        if success:
                            deleted_count += 1
                except OSError:
                    continue
        
        return deleted_count 