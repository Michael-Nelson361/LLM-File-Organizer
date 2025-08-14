# LLM File Organizer

An intelligent filesystem management tool that uses Large Language Models (LLMs) to help users organize and restructure their files and folders through natural language commands.

## Features

- **Natural Language Interface**: Give instructions like "organize my photos by year" or "move all PDFs to a documents folder"
- **Multi-LLM Support**: Works with OpenAI GPT models and Anthropic Claude
- **Strict Safety Constraints**: 
  - Cannot delete files (only move, rename, create folders)
  - Cannot work outside specified directory
  - Cannot touch system directories
  - Comprehensive path validation and security checks
- **Complete Logging**: All actions and conversations are logged with timestamps
- **Interactive CLI**: Colorful, user-friendly command-line interface
- **Real-time Validation**: Every operation is validated before execution

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/llm-file-organizer.git
cd llm-file-organizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API keys:
```bash
cp .env.example .env
# Edit .env with your OpenAI or Anthropic API key
```

## Usage

### Basic Usage

```bash
python main.py --root-path /path/to/organize --llm-provider openai
```

### Command Line Options

- `--root-path, -r`: Directory where the organizer can operate (required)
- `--llm-provider, -p`: LLM provider to use (`openai` or `anthropic`)
- `--model, -m`: Specific model to use (optional)
- `--api-key, -k`: API key (or set via environment variable)
- `--env-file, -e`: Path to environment file (default: `.env`)

### Example Commands

Once running, you can give natural language instructions:

- "Show me what's in the current directory"
- "Organize all my photos by year and month"
- "Move all PDF files to a Documents folder"
- "Create a folder structure for my project"
- "Rename all files with spaces to use underscores"
- "Where are all my .txt files located?"

### Special Commands

- `help` - Show available commands and examples
- `status` - Show current session information
- `summary` - Show session statistics
- `exit` or `quit` - End the session

## Safety Features

The LLM File Organizer includes multiple layers of security:

### What the AI CAN do:
- List and explore directory contents
- Move files and folders
- Rename files and folders
- Create new directories
- Remove empty directories
- Provide file and folder information

### What the AI CANNOT do:
- Delete or remove files
- Work outside the specified root directory
- Remove non-empty directories
- Access system directories
- Execute arbitrary commands
- Modify file contents

### Security Measures:
- Path traversal prevention
- System directory protection
- Dangerous pattern detection
- Action validation
- Comprehensive logging
- Input sanitization

## Project Structure

```
llm-file-organizer/
├── src/
│   ├── __init__.py
│   ├── cli_interface.py          # Main CLI and user interface
│   ├── filesystem_operations.py  # Safe filesystem operations
│   ├── llm_interface.py          # LLM integration and prompt handling
│   ├── logging_system.py         # Comprehensive logging system
│   └── safety_validator.py       # Security and validation layer
├── logs/                         # Generated log files
├── main.py                       # Entry point
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
├── .env.example                  # Environment configuration template
└── README.md
```

## Logging

All activities are logged in multiple formats:

- **Main Log**: General application logs with timestamps
- **Conversations**: Complete record of user interactions in JSONL format
- **Actions**: Detailed log of all filesystem operations in JSONL format
- **Security Events**: Security-related events and blocked actions

Logs are stored in the `logs/` directory with session timestamps.

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security Notice

This tool is designed with safety as the primary concern. It cannot delete files and operates with strict constraints. However, always:

- Test in a safe environment first
- Keep backups of important data
- Review the logs after each session
- Report any security concerns

## Support

For issues, feature requests, or questions:

1. Check the logs for detailed error information
2. Use the `help` command for usage guidance
3. Open an issue on GitHub with logs and steps to reproduce

## Changelog

### Version 1.0.0
- Initial release with core functionality
- Support for OpenAI and Anthropic LLMs
- Comprehensive safety and logging systems
- Interactive CLI interface 
