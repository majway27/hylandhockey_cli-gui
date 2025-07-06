#!/usr/bin/env python3
"""
Tests for file utilities module.
"""

import unittest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from utils.file_utils import FileUtils, DownloadManager


class TestFileUtils(unittest.TestCase):
    """Test cases for FileUtils class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_file.txt"
        
        # Create a test file
        with open(self.test_file, 'w') as f:
            f.write("Test content")
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_format_file_size(self):
        """Test file size formatting."""
        self.assertEqual(FileUtils.format_file_size(0), "0 B")
        self.assertEqual(FileUtils.format_file_size(1024), "1.0 KB")
        self.assertEqual(FileUtils.format_file_size(1024 * 1024), "1.0 MB")
        self.assertEqual(FileUtils.format_file_size(1024 * 1024 * 1024), "1.0 GB")
    
    def test_get_file_info(self):
        """Test getting file information."""
        file_info = FileUtils.get_file_info(self.test_file)
        
        self.assertEqual(file_info['name'], "test_file.txt")
        self.assertEqual(file_info['path'], self.test_file)
        self.assertTrue(file_info['exists'])
        self.assertTrue(file_info['is_file'])
        self.assertFalse(file_info['is_dir'])
        self.assertEqual(file_info['extension'], '.txt')
        self.assertIsInstance(file_info['size'], int)
        self.assertIsInstance(file_info['size_formatted'], str)
        self.assertIsInstance(file_info['modified'], datetime)
        self.assertIsInstance(file_info['modified_str'], str)
    
    def test_get_file_info_nonexistent(self):
        """Test getting file information for non-existent file."""
        nonexistent_file = self.temp_dir / "nonexistent.txt"
        file_info = FileUtils.get_file_info(nonexistent_file)
        
        self.assertEqual(file_info['name'], "nonexistent.txt")
        self.assertEqual(file_info['path'], nonexistent_file)
        self.assertFalse(file_info['exists'])
        self.assertFalse(file_info['is_file'])
        self.assertFalse(file_info['is_dir'])
        self.assertEqual(file_info['size'], 0)
        self.assertEqual(file_info['size_formatted'], "0 B")
        self.assertIsNone(file_info['modified'])
        self.assertEqual(file_info['modified_str'], "Unknown")
    
    def test_list_files(self):
        """Test listing files in directory."""
        # Create additional test files
        test_file2 = self.temp_dir / "test_file2.csv"
        test_file3 = self.temp_dir / "test_file3.xlsx"
        
        with open(test_file2, 'w') as f:
            f.write("CSV content")
        with open(test_file3, 'w') as f:
            f.write("Excel content")
        
        # Test listing all files
        all_files = FileUtils.list_files(self.temp_dir)
        self.assertEqual(len(all_files), 3)
        
        # Test listing CSV files only
        csv_files = FileUtils.list_files(self.temp_dir, pattern="*.csv")
        self.assertEqual(len(csv_files), 1)
        self.assertEqual(csv_files[0]['name'], "test_file2.csv")
        
        # Test sorting by name
        sorted_files = FileUtils.list_files(self.temp_dir, sort_by="name", reverse=False)
        self.assertEqual(sorted_files[0]['name'], "test_file.txt")
    
    def test_ensure_directory(self):
        """Test directory creation."""
        new_dir = self.temp_dir / "new_subdir" / "nested"
        created_dir = FileUtils.ensure_directory(new_dir)
        
        self.assertEqual(created_dir, new_dir)
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())
    
    def test_safe_delete_file(self):
        """Test safe file deletion."""
        # Test successful deletion
        success, message = FileUtils.safe_delete_file(self.test_file)
        self.assertTrue(success)
        self.assertIn("deleted successfully", message)
        self.assertFalse(self.test_file.exists())
        
        # Test deleting non-existent file
        success, message = FileUtils.safe_delete_file(self.test_file)
        self.assertFalse(success)
        self.assertIn("File not found", message)
    
    def test_get_unique_filename(self):
        """Test unique filename generation."""
        # Create a file with the base name
        base_file = self.temp_dir / "unique_test.txt"
        with open(base_file, 'w') as f:
            f.write("content")
        
        # Generate unique filename
        unique_file = FileUtils.get_unique_filename(self.temp_dir, "unique_test", ".txt")
        self.assertEqual(unique_file.name, "unique_test_1.txt")
        self.assertFalse(unique_file.exists())
        
        # Create the unique file
        with open(unique_file, 'w') as f:
            f.write("content")
        
        # Generate another unique filename
        unique_file2 = FileUtils.get_unique_filename(self.temp_dir, "unique_test", ".txt")
        self.assertEqual(unique_file2.name, "unique_test_2.txt")


class TestDownloadManager(unittest.TestCase):
    """Test cases for DownloadManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.download_manager = DownloadManager(str(self.temp_dir))
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test download manager initialization."""
        self.assertEqual(self.download_manager.base_dir, self.temp_dir)
        self.assertEqual(self.download_manager.usa_hockey_dir, self.temp_dir / "usa_hockey")
        self.assertTrue(self.download_manager.base_dir.exists())
        self.assertTrue(self.download_manager.usa_hockey_dir.exists())
    
    def test_get_usa_hockey_files(self):
        """Test getting USA Hockey files."""
        # Create test CSV files
        test_file1 = self.download_manager.usa_hockey_dir / "test1.csv"
        test_file2 = self.download_manager.usa_hockey_dir / "test2.csv"
        
        with open(test_file1, 'w') as f:
            f.write("content1")
        with open(test_file2, 'w') as f:
            f.write("content2")
        
        files = self.download_manager.get_usa_hockey_files()
        self.assertEqual(len(files), 2)
        
        # Files should be sorted by modification time (newest first)
        # Note: The order might vary depending on file creation timing
        file_names = [f['name'] for f in files]
        self.assertIn("test1.csv", file_names)
        self.assertIn("test2.csv", file_names)
    
    def test_get_download_directory(self):
        """Test getting download directories."""
        # Test base directory
        base_dir = self.download_manager.get_download_directory()
        self.assertEqual(base_dir, self.temp_dir)
        
        # Test subdirectory
        sub_dir = self.download_manager.get_download_directory("test_subdir")
        self.assertEqual(sub_dir, self.temp_dir / "test_subdir")
        self.assertTrue(sub_dir.exists())
    
    def test_cleanup_old_files(self):
        """Test cleanup of old files."""
        # Create a test file
        test_file = self.download_manager.usa_hockey_dir / "old_file.csv"
        with open(test_file, 'w') as f:
            f.write("old content")
        
        # The file should be deleted by cleanup (it's "old" by default)
        deleted_count = self.download_manager.cleanup_old_files(
            self.download_manager.usa_hockey_dir, 
            days_old=0  # Set to 0 to ensure the file is considered old
        )
        self.assertEqual(deleted_count, 1)
        self.assertFalse(test_file.exists())


if __name__ == '__main__':
    unittest.main() 