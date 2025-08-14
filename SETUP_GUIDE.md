# LLM File Organizer - Setup Guide

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Choose Your LLM Option

**Option A: Local LLM (Recommended - No API Key Required)**
```bash
# Install Ollama from https://ollama.ai/
ollama pull llama3.2

# Run with local LLM
python main.py --root-path /path/to/organize --llm-provider ollama
```

**Option B: Cloud LLM (Requires API Key)**
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your API key:
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Run with cloud LLM
python main.py --root-path /path/to/organize --llm-provider openai
```

### 3. Test Installation
```bash
python test_installation.py
```

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError
**Error:** `ModuleNotFoundError: No module named 'click'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

#### 2. API Key Errors
**Error:** `Error: API key not provided`

**Solution:** 
- Create a `.env` file with your API key
- Or pass it directly: `--api-key your_key_here`

#### 3. Path Issues
**Error:** `Invalid or unsafe root path`

**Solution:**
- Use absolute paths
- Ensure the directory exists
- Don't use system directories

#### 4. Permission Errors
**Error:** `Permission denied` or file access errors

**Solution:**
- Run as administrator (Windows)
- Check folder permissions
- Ensure folder is not read-only

### Windows-Specific Notes

1. **Emoji Display:** The CLI may not display emojis properly in some Windows terminals. This is cosmetic only.

2. **File Paths:** Use forward slashes or escape backslashes:
   ```bash
   python main.py --root-path "C:/Users/YourName/Documents/test"
   # or
   python main.py --root-path "C:\\Users\\YourName\\Documents\\test"
   ```

3. **Environment Variables:** You can also set API keys as system environment variables instead of using a `.env` file.

## Example Usage

### Basic Organization
```bash
# Organize a Downloads folder
python main.py --root-path "C:/Users/YourName/Downloads" --llm-provider openai

# Then in the interactive session:
organizer> show me what's in the current directory
organizer> organize all PDF files into a Documents folder
organizer> move all images to a Photos folder organized by date
```

### Advanced Usage
```bash
# Use specific model
python main.py --root-path "/home/user/messy_folder" --llm-provider anthropic --model claude-3-sonnet-20240229

# Use different env file
python main.py --root-path "/path/to/organize" --llm-provider openai --env-file custom.env
```

## Safety Features

The program is designed with safety as the primary concern:

✅ **Can do:**
- Move files and folders
- Rename files and folders
- Create new directories
- Remove empty directories
- List and explore contents

❌ **Cannot do:**
- Delete files
- Work outside designated directory
- Access system directories
- Execute arbitrary commands

## Getting Help

1. **In the program:** Type `help` for available commands
2. **Command line:** Run with `--help` for options
3. **Status:** Type `status` to see session information
4. **Logs:** Check the `logs/` directory for detailed activity records

## API Key Setup

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add it to your `.env` file

### Anthropic
1. Go to https://console.anthropic.com/
2. Create an API key
3. Add it to your `.env` file

### Supported Models

**OpenAI:**
- gpt-3.5-turbo (default, recommended for cost)
- gpt-4
- gpt-4-turbo

**Anthropic:**
- claude-3-haiku-20240307 (default, recommended for cost)
- claude-3-sonnet-20240229
- claude-3-opus-20240229

## Log Files

All activities are logged in the `logs/` directory:
- `organizer_[timestamp].log` - Main application log
- `conversations_[timestamp].jsonl` - User interactions
- `actions_[timestamp].jsonl` - Filesystem operations
- `security_[timestamp].jsonl` - Security events (if any)

These logs help with:
- Debugging issues
- Tracking what changes were made
- Security auditing
- Understanding the AI's decisions