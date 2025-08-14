import unittest
import tempfile
import shutil
import os
from pathlib import Path
import logging

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from filesystem_operations import SafeFilesystemOperations

class TestSafeFilesystemOperations(unittest.TestCase):
    
    def setUp(self):
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create logger
        self.logger = logging.getLogger("test")
        self.logger.setLevel(logging.DEBUG)
        
        # Initialize filesystem operations
        self.fs_ops = SafeFilesystemOperations(str(self.test_path), self.logger)
        
        # Create test structure
        (self.test_path / "test_file.txt").write_text("test content")
        (self.test_path / "test_dir").mkdir()
        (self.test_path / "test_dir" / "nested_file.txt").write_text("nested content")
        (self.test_path / "empty_dir").mkdir()
    
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_list_directory(self):
        result = self.fs_ops.list_directory("")
        self.assertIn("items", result)
        items = result["items"]
        
        # Check that our test files are listed
        names = [item["name"] for item in items]
        self.assertIn("test_file.txt", names)
        self.assertIn("test_dir", names)
        self.assertIn("empty_dir", names)
    
    def test_move_file(self):
        # Test moving a file
        result = self.fs_ops.move_file("test_file.txt", "moved_file.txt")
        self.assertTrue(result.get("success"))
        
        # Verify file was moved
        self.assertFalse((self.test_path / "test_file.txt").exists())
        self.assertTrue((self.test_path / "moved_file.txt").exists())
        
        # Verify content is preserved
        content = (self.test_path / "moved_file.txt").read_text()
        self.assertEqual(content, "test content")
    
    def test_move_file_to_subdirectory(self):
        # Test moving file to subdirectory
        result = self.fs_ops.move_file("test_file.txt", "test_dir/moved_here.txt")
        self.assertTrue(result.get("success"))
        
        # Verify file was moved
        self.assertFalse((self.test_path / "test_file.txt").exists())
        self.assertTrue((self.test_path / "test_dir" / "moved_here.txt").exists())
    
    def test_move_nonexistent_file(self):
        # Test moving non-existent file
        result = self.fs_ops.move_file("nonexistent.txt", "destination.txt")
        self.assertIn("error", result)
    
    def test_rename_file(self):
        # Test renaming a file
        result = self.fs_ops.rename_file("test_file.txt", "renamed_file.txt")
        self.assertTrue(result.get("success"))
        
        # Verify file was renamed
        self.assertFalse((self.test_path / "test_file.txt").exists())
        self.assertTrue((self.test_path / "renamed_file.txt").exists())
    
    def test_create_directory(self):
        # Test creating a new directory
        result = self.fs_ops.create_directory("new_directory")
        self.assertTrue(result.get("success"))
        
        # Verify directory was created
        self.assertTrue((self.test_path / "new_directory").exists())
        self.assertTrue((self.test_path / "new_directory").is_dir())
    
    def test_create_nested_directory(self):
        # Test creating nested directories
        result = self.fs_ops.create_directory("level1/level2/level3")
        self.assertTrue(result.get("success"))
        
        # Verify nested structure was created
        self.assertTrue((self.test_path / "level1" / "level2" / "level3").exists())
    
    def test_remove_empty_directory(self):
        # Test removing empty directory
        result = self.fs_ops.remove_empty_directory("empty_dir")
        self.assertTrue(result.get("success"))
        
        # Verify directory was removed
        self.assertFalse((self.test_path / "empty_dir").exists())
    
    def test_remove_non_empty_directory(self):
        # Test removing non-empty directory (should fail)
        result = self.fs_ops.remove_empty_directory("test_dir")
        self.assertIn("error", result)
        
        # Verify directory still exists
        self.assertTrue((self.test_path / "test_dir").exists())
    
    def test_get_file_info(self):
        # Test getting file info
        result = self.fs_ops.get_file_info("test_file.txt")
        
        self.assertEqual(result["name"], "test_file.txt")
        self.assertEqual(result["type"], "file")
        self.assertIn("size", result)
        self.assertIn("modified", result)
    
    def test_get_directory_info(self):
        # Test getting directory info
        result = self.fs_ops.get_file_info("test_dir")
        
        self.assertEqual(result["name"], "test_dir")
        self.assertEqual(result["type"], "directory")
        self.assertIn("contents_count", result)
    
    def test_path_traversal_protection(self):
        # Test protection against path traversal
        with self.assertRaises(ValueError):
            self.fs_ops._safe_path("../outside_directory")
        
        with self.assertRaises(ValueError):
            self.fs_ops._safe_path("/absolute/path/outside")
    
    def test_move_directory(self):
        # Create a test directory with content
        (self.test_path / "source_dir").mkdir()
        (self.test_path / "source_dir" / "file_in_dir.txt").write_text("content")
        
        # Test moving directory
        result = self.fs_ops.move_directory("source_dir", "destination_dir")
        self.assertTrue(result.get("success"))
        
        # Verify directory was moved
        self.assertFalse((self.test_path / "source_dir").exists())
        self.assertTrue((self.test_path / "destination_dir").exists())
        self.assertTrue((self.test_path / "destination_dir" / "file_in_dir.txt").exists())

if __name__ == '__main__':
    unittest.main()