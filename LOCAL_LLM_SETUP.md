# Local LLM Setup Guide

The LLM File Organizer now supports **completely offline, open-source LLMs** that run locally on your machine. No API keys required!

## 🚀 Quick Start (Recommended: Ollama)

### Option 1: Ollama (Easiest)

1. **Install Ollama:**
   - Windows/Mac/Linux: Download from https://ollama.ai/
   - Or use package manager: `winget install Ollama.Ollama`

2. **Start Ollama:**
   ```bash
   ollama serve
   ```

3. **Download a model:**
   ```bash
   # Lightweight model (1.5GB)
   ollama pull llama3.2:1b
   
   # Standard model (4.7GB) - Recommended
   ollama pull llama3.2
   
   # Larger model (14GB) - Best quality
   ollama pull llama3.1:8b
   ```

4. **Run the File Organizer:**
   ```bash
   python main.py --root-path "C:/path/to/organize" --llm-provider ollama
   
   # Or specify model:
   python main.py --root-path "C:/path/to/organize" --llm-provider ollama --model llama3.2:1b
   ```

### Option 2: LM Studio (User-Friendly GUI)

1. **Install LM Studio:**
   - Download from https://lmstudio.ai/
   - Install and open the application

2. **Download a model in LM Studio:**
   - Go to "Discover" tab
   - Search for and download: `microsoft/Phi-3-mini-4k-instruct-gguf`
   - Or any other model you prefer

3. **Start Local Server:**
   - Go to "Local Server" tab
   - Load your downloaded model
   - Click "Start Server"
   - Default port: 1234

4. **Run the File Organizer:**
   ```bash
   python main.py --root-path "C:/path/to/organize" --llm-provider lmstudio
   ```

### Option 3: HuggingFace Local (Direct Download)

1. **Install additional dependencies:**
   ```bash
   pip install transformers torch
   ```

2. **Run with auto-download:**
   ```bash
   # Uses a small conversational model (downloads automatically)
   python main.py --root-path "C:/path/to/organize" --llm-provider huggingface
   
   # Or specify a different model:
   python main.py --root-path "C:/path/to/organize" --llm-provider huggingface --model "microsoft/DialoGPT-small"
   ```

## 📋 Comparison of Local LLM Options

| Provider | Pros | Cons | Best For |
|----------|------|------|----------|
| **Ollama** | Easy setup, great models, fast | Requires separate install | Most users |
| **LM Studio** | GUI interface, model management | Larger download | Users who prefer GUI |
| **HuggingFace** | No extra software needed | Slower, basic models | Quick testing |

## 🔧 Detailed Setup Instructions

### Ollama Setup (Detailed)

1. **Installation:**
   ```bash
   # Windows (PowerShell as Admin)
   winget install Ollama.Ollama
   
   # Or download installer from https://ollama.ai/
   ```

2. **Available Models:**
   ```bash
   # List available models
   ollama list
   
   # Popular models for file organization:
   ollama pull llama3.2        # Best balance (4.7GB)
   ollama pull llama3.2:1b     # Fastest (1.5GB)
   ollama pull codellama       # Good for structured tasks (7GB)
   ollama pull mistral         # Alternative option (4.1GB)
   ```

3. **Custom Configuration:**
   ```bash
   # Run on different port
   OLLAMA_HOST=0.0.0.0:11435 ollama serve
   
   # Then use:
   python main.py --root-path "C:/path" --llm-provider ollama --base-url http://localhost:11435
   ```

### LM Studio Setup (Detailed)

1. **Model Recommendations:**
   - **Small/Fast:** `microsoft/Phi-3-mini-4k-instruct-gguf`
   - **Balanced:** `microsoft/Phi-3-medium-4k-instruct-gguf`
   - **Large/Quality:** `meta-llama/Llama-2-7b-chat-gguf`

2. **Server Configuration:**
   - Open LM Studio → Local Server
   - Load model → Configure settings
   - **Important:** Set "Chat Template" to "ChatML" or "Alpaca"
   - Start server on port 1234

3. **Troubleshooting:**
   ```bash
   # Test connection
   curl http://localhost:1234/v1/models
   
   # Use different port
   python main.py --root-path "C:/path" --llm-provider lmstudio --base-url http://localhost:8080
   ```

### HuggingFace Local Setup (Detailed)

1. **System Requirements:**
   - At least 8GB RAM
   - 2GB+ free disk space
   - Python 3.8+

2. **Recommended Models:**
   ```bash
   # Small and fast
   --model "microsoft/DialoGPT-small"
   
   # Better quality (requires more RAM)
   --model "microsoft/DialoGPT-medium"
   
   # Instruction-following
   --model "microsoft/Phi-3-mini-4k-instruct"
   ```

3. **First Run:**
   - Models download automatically to `~/.cache/huggingface/`
   - First startup takes 2-5 minutes
   - Subsequent runs are faster

## 🚨 Troubleshooting

### Common Issues

1. **"Cannot connect to Ollama"**
   ```bash
   # Check if Ollama is running
   ollama list
   
   # Start Ollama server
   ollama serve
   
   # Test with curl
   curl http://localhost:11434/api/tags
   ```

2. **"Cannot connect to LM Studio"**
   - Open LM Studio
   - Go to "Local Server" tab
   - Make sure a model is loaded
   - Click "Start Server"
   - Check port number (default: 1234)

3. **HuggingFace "Out of Memory"**
   ```bash
   # Use smaller model
   --model "microsoft/DialoGPT-small"
   
   # Or reduce max length in code
   # Edit src/llm_interface.py, line ~195
   # Change max_length=512 to max_length=256
   ```

4. **Slow Performance**
   - Use smaller models (1B parameters vs 7B+)
   - Close other applications
   - Consider GPU acceleration setup

### Performance Tips

1. **Model Size vs Quality:**
   - 1-3B parameters: Fast, basic functionality
   - 7B parameters: Good balance
   - 13B+ parameters: Best quality, slower

2. **Hardware Recommendations:**
   - **Minimum:** 8GB RAM, CPU-only
   - **Recommended:** 16GB RAM, dedicated GPU
   - **Optimal:** 32GB RAM, RTX 3080+ or similar

3. **GPU Acceleration (Advanced):**
   ```bash
   # For NVIDIA GPUs
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # Ollama automatically uses GPU if available
   # LM Studio has GPU options in settings
   ```

## 🔒 Privacy & Security

**Benefits of Local LLMs:**
- ✅ Complete privacy - no data sent to external servers
- ✅ Works offline
- ✅ No API costs
- ✅ Full control over the model

**Considerations:**
- Local LLMs may be less capable than cloud models
- Require local computing resources
- Model quality varies

## 📝 Example Usage

```bash
# Basic usage with Ollama
python main.py --root-path "~/Downloads" --llm-provider ollama

# Interactive session example:
organizer> show me what's in this directory
organizer> organize all images into a Photos folder
organizer> move PDF files to Documents
organizer> create a folder structure: Work/Projects/2024
```

## 🆘 Getting Help

1. **Check server status:**
   ```bash
   # Ollama
   ollama list
   
   # LM Studio
   # Check GUI - should show "Server Running"
   ```

2. **Test with curl:**
   ```bash
   # Ollama
   curl -X POST http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"Hello"}'
   
   # LM Studio
   curl http://localhost:1234/v1/models
   ```

3. **Check logs:**
   - File organizer logs are in `logs/` directory
   - Ollama logs: `ollama logs`
   - LM Studio logs: Available in GUI

## 🔄 Model Updates

```bash
# Update Ollama models
ollama pull llama3.2

# Update LM Studio models
# Use the GUI to check for updates

# HuggingFace models update automatically
```

Choose the option that works best for your setup. Ollama is generally recommended for most users due to its ease of use and good model selection.