#!/usr/bin/env python3
"""
Test script to verify the Ollama timeout fixes.
"""

import sys
import tempfile
import time
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_timeout_fix():
    """Test that the timeout fix works with a potentially problematic query."""
    
    print("Testing Ollama Timeout Fix")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create some test files with dates in names
        test_files = [
            "report_2016_01_15.pdf",
            "photo_2016_summer.jpg",
            "notes_2017_meeting.txt",
            "backup_2015_final.zip",
            "project_2016_q4.docx"
        ]
        
        for filename in test_files:
            (temp_path / filename).write_text(f"Content of {filename}")
        
        print(f"Created test files in: {temp_path}")
        for f in test_files:
            print(f"  - {f}")
        
        print("\nInitializing LLM with timeout fixes...")
        
        from src.filesystem_operations import SafeFilesystemOperations
        from src.llm_interface import FilesystemLLM, OllamaInterface
        from src.logging_system import FileOrganizerLogger
        
        try:
            logger_system = FileOrganizerLogger()
            logger = logger_system.get_logger()
            
            fs_ops = SafeFilesystemOperations(str(temp_path), logger)
            ollama = OllamaInterface()  # Uses auto-selection and timeout fixes
            filesystem_llm = FilesystemLLM(ollama, fs_ops, logger)
            
            print(f"[OK] LLM initialized successfully")
            
            # Test the problematic query type
            print("\nTesting query: 'What can you tell me about the files in 2016?'")
            start_time = time.time()
            
            try:
                response = filesystem_llm.process_user_input("What can you tell me about the files in 2016?")
                end_time = time.time()
                
                print(f"[OK] Query completed in {end_time - start_time:.1f} seconds")
                print("\nResponse received:")
                print("-" * 40)
                print(response)
                print("-" * 40)
                
                # Check if response contains expected information
                if "2016" in response and ("report" in response or "photo" in response or "project" in response):
                    print("\n[SUCCESS] Response contains relevant file information")
                    return True
                else:
                    print("\n[WARNING] Response may not contain expected file information")
                    return True  # Still a success if no timeout occurred
                    
            except Exception as e:
                end_time = time.time()
                
                if "timeout" in str(e).lower():
                    print(f"[PARTIAL] Timeout still occurred after {end_time - start_time:.1f} seconds")
                    print(f"Error: {str(e)}")
                    print("\nSuggestions:")
                    print("1. Try restarting Ollama: ollama serve")
                    print("2. Use a smaller model: ollama pull llama3.2:1b")
                    print("3. Try a simpler query first")
                    return False
                else:
                    print(f"[ERROR] Non-timeout error: {str(e)}")
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Failed to initialize: {str(e)}")
            return False

def test_retry_mechanism():
    """Test the retry mechanism with a simple query."""
    
    print("\n" + "=" * 40)
    print("Testing Retry Mechanism")
    print("=" * 40)
    
    try:
        from src.llm_interface import OllamaInterface
        
        ollama = OllamaInterface()
        
        # Simple test message
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Keep responses brief."},
            {"role": "user", "content": "Say hello"}
        ]
        
        print("Testing simple query with retry logic...")
        start_time = time.time()
        
        response = ollama.generate_response(messages)
        end_time = time.time()
        
        print(f"[OK] Response received in {end_time - start_time:.1f} seconds")
        print(f"Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Retry test failed: {str(e)}")
        return False

def main():
    """Run timeout fix tests."""
    
    print("LLM File Organizer - Timeout Fix Verification")
    print("=" * 50)
    
    # Test 1: Retry mechanism
    retry_ok = test_retry_mechanism()
    
    # Test 2: Full system with problematic query
    if retry_ok:
        timeout_ok = test_timeout_fix()
    else:
        print("\nSkipping full test due to retry test failure")
        timeout_ok = False
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Retry Mechanism: {'PASS' if retry_ok else 'FAIL'}")
    print(f"Timeout Fix: {'PASS' if timeout_ok else 'FAIL'}")
    
    if retry_ok and timeout_ok:
        print("\n[SUCCESS] All timeout fixes working correctly!")
        print("The system should now handle queries about 'files in 2016' without timing out.")
    else:
        print("\n[PARTIAL] Some tests failed - check Ollama configuration")
    
    return retry_ok and timeout_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)