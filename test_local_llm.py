#!/usr/bin/env python3
"""
Test script to verify local LLM functionality without interactive input.
This demonstrates that the LLM File Organizer can work with local models.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_ollama_connection():
    """Test if Ollama is available and working."""
    print("Testing Ollama connection...")
    
    try:
        from src.llm_interface import OllamaInterface
        
        # Try to create interface
        ollama = OllamaInterface(model="llama3.2:3b")
        print("[OK] Ollama connection successful")
        
        # Test simple generation
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Respond briefly."},
            {"role": "user", "content": "Say hello"}
        ]
        
        response = ollama.generate_response(messages)
        print(f"[OK] Ollama response: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"[INFO] Ollama not available: {str(e)}")
        return False

def test_huggingface_local():
    """Test HuggingFace local model (if transformers is installed)."""
    print("\nTesting HuggingFace local model...")
    
    try:
        import transformers
        import torch
        
        # Use a very small model for testing
        from src.llm_interface import HuggingFaceLocalInterface
        
        print("Loading small HuggingFace model (this may take a moment)...")
        hf = HuggingFaceLocalInterface(model="microsoft/DialoGPT-small")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        
        response = hf.generate_response(messages)
        print(f"[OK] HuggingFace response: {response[:100]}...")
        return True
        
    except ImportError:
        print("[INFO] HuggingFace transformers not installed (pip install transformers torch)")
        return False
    except Exception as e:
        print(f"[INFO] HuggingFace model not available: {str(e)}")
        return False

def test_filesystem_operations():
    """Test that filesystem operations work."""
    print("\nTesting filesystem operations...")
    
    try:
        from src.filesystem_operations import SafeFilesystemOperations
        from src.logging_system import FileOrganizerLogger
        
        # Create temporary test
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            logger_system = FileOrganizerLogger()
            logger = logger_system.get_logger()
            
            fs_ops = SafeFilesystemOperations(temp_dir, logger)
            
            # Test basic operations
            result = fs_ops.list_directory("")
            assert "items" in result, "Directory listing failed"
            
            result = fs_ops.create_directory("test_folder")
            assert result.get("success"), "Directory creation failed"
            
            print("[OK] Filesystem operations working")
            return True
            
    except Exception as e:
        print(f"[ERROR] Filesystem operations failed: {str(e)}")
        return False

def main():
    """Run all tests and provide recommendations."""
    print("LLM File Organizer - Local LLM Test")
    print("=" * 50)
    
    # Test filesystem operations first
    fs_ok = test_filesystem_operations()
    
    # Test local LLM options
    ollama_ok = test_ollama_connection()
    hf_ok = test_huggingface_local()
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print(f"Filesystem Operations: {'[OK]' if fs_ok else '[FAIL]'}")
    print(f"Ollama: {'[OK]' if ollama_ok else '[FAIL]'}")
    print(f"HuggingFace: {'[OK]' if hf_ok else '[FAIL]'}")
    
    print("\nRecommendations:")
    
    if ollama_ok:
        print("[SUCCESS] Ollama is ready! You can use:")
        print("   python main.py --root-path /path/to/organize --llm-provider ollama")
    elif hf_ok:
        print("[SUCCESS] HuggingFace local models are ready! You can use:")
        print("   python main.py --root-path /path/to/organize --llm-provider huggingface")
    else:
        print("[SETUP] No local LLMs available. To get started:")
        print("   1. Install Ollama: https://ollama.ai/")
        print("   2. Run: ollama pull llama3.2")
        print("   3. Or install transformers: pip install transformers torch")
    
    if fs_ok and (ollama_ok or hf_ok):
        print("\n[SUCCESS] Local LLM File Organizer is ready to use!")
        return True
    else:
        print("\n[SETUP] Setup required - see recommendations above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)