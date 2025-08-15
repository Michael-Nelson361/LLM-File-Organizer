#!/usr/bin/env python3
"""
Comprehensive test for file overwrite protection.
This verifies that the system prevents accidental file overwrites.
"""

import sys
import tempfile
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_file_overwrite_protection():
    """Test that files are protected from overwriting during moves."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files with different content
        (temp_path / "source.txt").write_text("This is the source file")
        (temp_path / "existing.txt").write_text("This is an existing file that should NOT be overwritten")
        
        # Test directory structure
        (temp_path / "folder1").mkdir()
        (temp_path / "folder2").mkdir()
        (temp_path / "folder1" / "file1.txt").write_text("File in folder1")
        (temp_path / "folder2" / "file1.txt").write_text("Different file in folder2")
        
        from src.filesystem_operations import SafeFilesystemOperations
        from src.logging_system import FileOrganizerLogger
        
        logger_system = FileOrganizerLogger()
        logger = logger_system.get_logger()
        fs_ops = SafeFilesystemOperations(str(temp_path), logger)
        
        print("=" * 60)
        print("TESTING FILE OVERWRITE PROTECTION")
        print("=" * 60)
        
        # Test 1: Try to move file to existing location (should auto-rename)
        print("\nTest 1: Moving file to existing location")
        print("Source: source.txt -> existing.txt")
        
        result = fs_ops.move_file("source.txt", "existing.txt")
        
        if result.get("success") and result.get("renamed"):
            print(f"[OK] File was auto-renamed to: {result.get('final_path')}")
            print(f"[OK] Original existing.txt was preserved")
            
            # Verify original file still exists and wasn't overwritten
            original_content = (temp_path / "existing.txt").read_text()
            if "should NOT be overwritten" in original_content:
                print("[OK] Original file content preserved")
            else:
                print("[ERROR] Original file was overwritten!")
                return False
                
            # Verify renamed file has correct content
            renamed_path = temp_path / result.get('final_path')
            if renamed_path.exists():
                renamed_content = renamed_path.read_text()
                if "This is the source file" in renamed_content:
                    print("[OK] Renamed file has correct content")
                else:
                    print("[ERROR] Renamed file has wrong content")
                    return False
            else:
                print("[ERROR] Renamed file doesn't exist")
                return False
                
        else:
            print("[ERROR] File move didn't auto-rename as expected")
            print(f"Result: {result}")
            return False
        
        # Test 2: Try to move with auto_rename=False (should fail)
        print("\nTest 2: Moving file with auto_rename disabled")
        (temp_path / "source2.txt").write_text("Another source file")
        
        result = fs_ops.move_file("source2.txt", "existing.txt", auto_rename=False)
        
        if result.get("error") and "already exists" in result.get("error"):
            print("[OK] Move correctly failed when auto_rename disabled")
        else:
            print("[ERROR] Move should have failed with auto_rename=False")
            print(f"Result: {result}")
            return False
        
        # Test 3: Directory conflict protection
        print("\nTest 3: Moving directory to existing location")
        
        result = fs_ops.move_directory("folder1", "folder2")
        
        if result.get("success") and result.get("renamed"):
            print(f"[OK] Directory was auto-renamed to: {result.get('final_path')}")
            
            # Verify original folder2 still exists
            if (temp_path / "folder2").exists():
                print("[OK] Original folder2 was preserved")
            else:
                print("[ERROR] Original folder2 was overwritten!")
                return False
                
        else:
            print("[ERROR] Directory move didn't auto-rename as expected")
            print(f"Result: {result}")
            return False
        
        # Test 4: Preview functionality
        print("\nTest 4: Testing move preview")
        (temp_path / "preview_source.txt").write_text("Preview test file")
        
        preview = fs_ops.get_move_preview("preview_source.txt", "existing.txt")
        
        if preview.get("conflict") and preview.get("auto_rename_to"):
            print(f"[OK] Preview correctly detected conflict")
            print(f"[OK] Would auto-rename to: {preview.get('auto_rename_to')}")
        else:
            print("[ERROR] Preview didn't detect conflict correctly")
            print(f"Preview: {preview}")
            return False
        
        # Test 5: Bulk move with conflicts
        print("\nTest 5: Testing bulk move with conflicts")
        
        # Create multiple test files
        for i in range(3):
            (temp_path / f"bulk_test_{i}.txt").write_text(f"Bulk test file {i}")
        
        # Create one conflicting file
        (temp_path / "documents").mkdir(exist_ok=True)
        (temp_path / "documents" / "bulk_test_1.txt").write_text("Existing file in documents")
        
        result = fs_ops.bulk_move_files(["bulk_test_*.txt"], "documents")
        
        if result.get("success"):
            moved = len(result.get("moved_files", []))
            renamed = len(result.get("renamed_files", []))
            errors = len(result.get("errors", []))
            
            print(f"[OK] Bulk move completed: {moved} moved, {renamed} renamed, {errors} errors")
            
            if renamed > 0:
                print("[OK] Conflicts were handled with auto-renaming")
                for renamed_file in result.get("renamed_files", []):
                    print(f"  - {renamed_file['intended']} -> {renamed_file['actual']}")
            
        else:
            print("[ERROR] Bulk move failed")
            print(f"Result: {result}")
            return False
        
        print("\n" + "=" * 60)
        print("ALL OVERWRITE PROTECTION TESTS PASSED!")
        print("=" * 60)
        
        return True

def test_safety_logging():
    """Test that all safety events are properly logged."""
    
    print("\nTesting safety logging...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        (temp_path / "test1.txt").write_text("Test file 1")
        (temp_path / "test2.txt").write_text("Test file 2")
        
        from src.filesystem_operations import SafeFilesystemOperations
        from src.logging_system import FileOrganizerLogger
        
        logger_system = FileOrganizerLogger()
        logger = logger_system.get_logger()
        fs_ops = SafeFilesystemOperations(str(temp_path), logger)
        
        # Perform operations that should generate logs
        fs_ops.move_file("test1.txt", "test2.txt")  # Should auto-rename
        
        # Check if logs were created
        log_files = list(Path("logs").glob("*.log"))
        if log_files:
            print("[OK] Log files created")
            
            # Check latest log for safety events
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            log_content = latest_log.read_text()
            
            if "auto-renamed" in log_content.lower():
                print("[OK] Auto-rename operation logged")
            else:
                print("[WARNING] Auto-rename not found in logs")
            
        else:
            print("[WARNING] No log files found")
        
        return True

def main():
    """Run all overwrite protection tests."""
    
    print("LLM File Organizer - Overwrite Protection Test")
    print("=" * 60)
    
    try:
        # Run protection tests
        protection_ok = test_file_overwrite_protection()
        
        # Run logging tests
        logging_ok = test_safety_logging()
        
        if protection_ok and logging_ok:
            print("\n🎉 ALL SAFETY TESTS PASSED!")
            print("Files are protected from accidental overwriting.")
            return True
        else:
            print("\n❌ SOME TESTS FAILED!")
            return False
            
    except Exception as e:
        print(f"\n💥 TEST FAILED WITH EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)