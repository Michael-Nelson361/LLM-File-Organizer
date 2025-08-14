#!/usr/bin/env python3
"""Quick test to demonstrate the filesystem question functionality."""

import sys
import tempfile
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_filesystem_question():
    """Test asking about filesystem structure."""
    
    # Create a test directory with some files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test structure
        (temp_path / "documents").mkdir()
        (temp_path / "photos").mkdir()
        (temp_path / "photos" / "vacation").mkdir()
        
        (temp_path / "readme.txt").write_text("This is a readme file")
        (temp_path / "report.pdf").write_text("PDF content")
        (temp_path / "documents" / "letter.docx").write_text("Letter content")
        (temp_path / "photos" / "sunset.jpg").write_text("Photo content")
        (temp_path / "photos" / "vacation" / "beach.jpg").write_text("Beach photo")
        
        # Initialize the system
        from src.filesystem_operations import SafeFilesystemOperations
        from src.llm_interface import OllamaInterface, FilesystemLLM
        from src.logging_system import FileOrganizerLogger
        
        logger_system = FileOrganizerLogger()
        logger = logger_system.get_logger()
        
        fs_ops = SafeFilesystemOperations(str(temp_path), logger)
        ollama = OllamaInterface()
        filesystem_llm = FilesystemLLM(ollama, fs_ops, logger)
        
        print("Test directory structure created:")
        print(f"Root: {temp_path}")
        print("- readme.txt")
        print("- report.pdf") 
        print("- documents/")
        print("  - letter.docx")
        print("- photos/")
        print("  - sunset.jpg")
        print("  - vacation/")
        print("    - beach.jpg")
        
        print("\nTesting filesystem structure question...")
        
        # Test the question
        response = filesystem_llm.process_user_input("What is the structure of this filesystem?")
        
        print("\nAI Response:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
        return True

if __name__ == "__main__":
    try:
        test_filesystem_question()
        print("\n[SUCCESS] Test completed successfully!")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        sys.exit(1)