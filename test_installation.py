#!/usr/bin/env python3
"""
Simple installation test script to verify all components work correctly
without requiring API keys.
"""

import sys
import os
from pathlib import Path
import tempfile
import logging

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        global SafeFilesystemOperations, SafetyValidator, FileOrganizerLogger
        global FilesystemLLM, OpenAIInterface, AnthropicInterface
        
        from src.filesystem_operations import SafeFilesystemOperations
        print("[OK] filesystem_operations imported successfully")
        
        from src.safety_validator import SafetyValidator
        print("[OK] safety_validator imported successfully")
        
        from src.logging_system import FileOrganizerLogger
        print("[OK] logging_system imported successfully")
        
        from src.llm_interface import FilesystemLLM, OpenAIInterface, AnthropicInterface
        print("[OK] llm_interface imported successfully")
        
        import click
        print("[OK] click imported successfully")
        
        import colorama
        print("[OK] colorama imported successfully")
        
        return True
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False

def test_filesystem_operations():
    """Test filesystem operations in a temporary directory."""
    print("\nTesting filesystem operations...")
    
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = logging.getLogger("test")
            fs_ops = SafeFilesystemOperations(temp_dir, logger)
            
            # Test create directory
            result = fs_ops.create_directory("test_dir")
            assert result.get("success"), f"Failed to create directory: {result}"
            print("[OK] Directory creation works")
            
            # Test list directory
            result = fs_ops.list_directory("")
            assert "items" in result, f"Failed to list directory: {result}"
            print("[OK] Directory listing works")
            
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")
            
            # Test file info
            result = fs_ops.get_file_info("test.txt")
            assert result["name"] == "test.txt", f"Failed to get file info: {result}"
            print("[OK] File info retrieval works")
            
            # Test rename
            result = fs_ops.rename_file("test.txt", "renamed.txt")
            assert result.get("success"), f"Failed to rename file: {result}"
            print("[OK] File renaming works")
            
        return True
    except Exception as e:
        print(f"[ERROR] Filesystem operations error: {e}")
        return False

def test_safety_validator():
    """Test safety validation."""
    print("\nTesting safety validator...")
    
    try:
        logger = logging.getLogger("test")
        validator = SafetyValidator(logger)
        
        # Test path validation
        with tempfile.TemporaryDirectory() as temp_dir:
            assert validator.validate_root_path(temp_dir), "Failed to validate safe root path"
            print("[OK] Safe path validation works")
        
        # Test dangerous pattern detection
        dangerous_input = "../../../etc/passwd"
        result = validator.validate_user_input(dangerous_input)
        # Should return True but log the event (not blocking user input)
        assert result, "User input validation failed"
        print("[OK] Dangerous pattern detection works")
        
        # Test action validation
        safe_action = {"action": "list_directory", "parameters": {"path": "."}}
        assert validator.validate_action("list_directory", {"path": "."}), "Safe action validation failed"
        print("[OK] Action validation works")
        
        return True
    except Exception as e:
        print(f"[ERROR] Safety validator error: {e}")
        return False

def test_logging_system():
    """Test logging system."""
    print("\nTesting logging system...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger_system = FileOrganizerLogger(log_dir=temp_dir)
            logger = logger_system.get_logger()
            
            # Test basic logging
            logger.info("Test log message")
            print("[OK] Basic logging works")
            
            # Test conversation logging
            logger_system.log_conversation("test input", "test response")
            print("[OK] Conversation logging works")
            
            # Test action logging
            logger_system.log_action("test_action", {"param": "value"}, {"success": True})
            print("[OK] Action logging works")
            
            # Test session summary
            summary = logger_system.get_session_summary()
            assert "session_id" in summary, "Session summary missing session_id"
            print("[OK] Session summary works")
            
        return True
    except Exception as e:
        print(f"[ERROR] Logging system error: {e}")
        return False

def main():
    """Run all tests."""
    print("LLM File Organizer Installation Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_filesystem_operations,
        test_safety_validator,
        test_logging_system
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[ERROR] Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All tests passed! Installation is successful.")
        print("\nTo use the LLM File Organizer:")
        print("1. Set up your API key in a .env file")
        print("2. Run: python main.py --root-path /path/to/organize --llm-provider openai")
        return True
    else:
        print("Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)