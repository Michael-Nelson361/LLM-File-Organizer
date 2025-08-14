import click
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import colorama
from colorama import Fore, Style

from .filesystem_operations import SafeFilesystemOperations
from .llm_interface import (FilesystemLLM, OpenAIInterface, AnthropicInterface, 
                           OllamaInterface, LMStudioInterface, HuggingFaceLocalInterface)
from .logging_system import FileOrganizerLogger
from .safety_validator import SafetyValidator

# Initialize colorama for Windows compatibility
colorama.init()

class CLIInterface:
    def __init__(self, root_path: str, llm_provider: str, api_key: str = None, model: str = None, 
                 base_url: str = None):
        # Initialize logging first
        self.logger_system = FileOrganizerLogger()
        self.logger = self.logger_system.get_logger()
        
        # Initialize safety validator
        self.safety_validator = SafetyValidator(self.logger)
        
        # Validate root path
        if not self.safety_validator.validate_root_path(root_path):
            raise ValueError(f"Invalid or unsafe root path: {root_path}")
        
        # Initialize filesystem operations
        self.fs_ops = SafeFilesystemOperations(root_path, self.logger)
        
        # Initialize LLM interface based on provider
        llm_interface = self._create_llm_interface(llm_provider, api_key, model, base_url)
        
        # Initialize the filesystem LLM
        self.filesystem_llm = FilesystemLLM(llm_interface, self.fs_ops, self.logger)
        
        self.logger.info(f"CLI initialized with root path: {root_path}")
        self.logger.info(f"LLM provider: {llm_provider}, model: {model}")
    
    def _create_llm_interface(self, provider: str, api_key: str, model: str, base_url: str):
        provider = provider.lower()
        
        if provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable or use --api-key")
            return OpenAIInterface(api_key, model or "gpt-3.5-turbo")
        
        elif provider == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable or use --api-key")
            return AnthropicInterface(api_key, model or "claude-3-haiku-20240307")
        
        elif provider == "ollama":
            return OllamaInterface(
                model=model or "llama3.2",
                base_url=base_url or "http://localhost:11434"
            )
        
        elif provider == "lmstudio":
            return LMStudioInterface(
                model=model or "local-model",
                base_url=base_url or "http://localhost:1234"
            )
        
        elif provider == "huggingface":
            return HuggingFaceLocalInterface(
                model=model or "microsoft/DialoGPT-medium"
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}. "
                           f"Supported providers: openai, anthropic, ollama, lmstudio, huggingface")
    
    def print_banner(self):
        banner = f"""
{Fore.CYAN}================================================================
                    LLM File Organizer                       
              Intelligent Filesystem Management              
================================================================{Style.RESET_ALL}

{Fore.GREEN}[OK] Root directory: {self.fs_ops.root_path}
[OK] Logging enabled
[OK] Safety constraints active{Style.RESET_ALL}

{Fore.YELLOW}Available commands:
- Type your instructions naturally (e.g., "organize my photos by year")
- Ask questions (e.g., "what files are in the downloads folder?")
- Request specific actions (e.g., "move all .txt files to documents")
- Type 'help' for more information
- Type 'exit' or 'quit' to end session{Style.RESET_ALL}

{Fore.RED}Safety Notice: The AI can only work within the specified directory and cannot delete files.{Style.RESET_ALL}
"""
        print(banner)
    
    def print_help(self):
        help_text = f"""
{Fore.CYAN}LLM File Organizer Help{Style.RESET_ALL}

{Fore.GREEN}What the AI can do:{Style.RESET_ALL}
- List and explore directory contents
- Move files and folders to new locations
- Rename files and folders
- Create new directories
- Remove empty directories
- Provide information about files and folders

{Fore.RED}Safety restrictions:{Style.RESET_ALL}
- Cannot delete or remove files
- Cannot work outside the specified root directory
- Cannot remove non-empty directories
- All actions are logged

{Fore.YELLOW}Example commands:{Style.RESET_ALL}
- "Show me what's in the current directory"
- "Organize all my photos by year and month"
- "Move all PDF files to a Documents folder"
- "Create a folder structure for my project"
- "Rename all files with spaces to use underscores"
- "Where are all my .txt files located?"

{Fore.BLUE}Special commands:{Style.RESET_ALL}
- help - Show this help message
- status - Show current session information
- summary - Show session summary and statistics
- exit/quit - End the session
"""
        print(help_text)
    
    def print_status(self):
        summary = self.logger_system.get_session_summary()
        status_text = f"""
{Fore.CYAN}Session Status{Style.RESET_ALL}

{Fore.GREEN}Session ID:{Style.RESET_ALL} {summary['session_id']}
{Fore.GREEN}Root Directory:{Style.RESET_ALL} {self.fs_ops.root_path}
{Fore.GREEN}Conversations:{Style.RESET_ALL} {summary.get('conversation_count', 0)}
{Fore.GREEN}Actions Performed:{Style.RESET_ALL} {summary.get('action_count', 0)}
{Fore.GREEN}Successful Actions:{Style.RESET_ALL} {summary.get('successful_actions', 0)}
{Fore.GREEN}Failed Actions:{Style.RESET_ALL} {summary.get('failed_actions', 0)}

{Fore.BLUE}Log Files:{Style.RESET_ALL}
- Main log: {summary['log_files']['main_log']}
- Conversations: {summary['log_files']['conversations']}
- Actions: {summary['log_files']['actions']}
"""
        print(status_text)
    
    def run_interactive(self):
        self.print_banner()
        
        try:
            while True:
                try:
                    # Get user input
                    user_input = input(f"\n{Fore.BLUE}organizer>{Style.RESET_ALL} ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle special commands
                    if user_input.lower() in ['exit', 'quit']:
                        print(f"\n{Fore.GREEN}Session ended. Check logs for complete activity record.{Style.RESET_ALL}")
                        break
                    elif user_input.lower() == 'help':
                        self.print_help()
                        continue
                    elif user_input.lower() == 'status':
                        self.print_status()
                        continue
                    elif user_input.lower() == 'summary':
                        summary = self.logger_system.get_session_summary()
                        print(f"\n{Fore.CYAN}Session Summary:{Style.RESET_ALL}")
                        for key, value in summary.items():
                            if key != 'log_files':
                                print(f"{Fore.GREEN}{key}:{Style.RESET_ALL} {value}")
                        continue
                    
                    # Process with LLM
                    print(f"\n{Fore.YELLOW}Processing...{Style.RESET_ALL}")
                    
                    response = self.filesystem_llm.process_user_input(user_input)
                    
                    # Log the conversation
                    self.logger_system.log_conversation(user_input, response)
                    
                    # Display response
                    print(f"\n{Fore.GREEN}Assistant:{Style.RESET_ALL} {response}")
                    
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}Use 'exit' or 'quit' to end the session properly.{Style.RESET_ALL}")
                    continue
                except Exception as e:
                    error_msg = f"An error occurred: {str(e)}"
                    print(f"\n{Fore.RED}Error: {error_msg}{Style.RESET_ALL}")
                    self.logger.error(error_msg)
                    continue
        
        except Exception as e:
            print(f"\n{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
            self.logger.error(f"Fatal error in interactive session: {str(e)}")
        finally:
            # Print session summary
            summary = self.logger_system.get_session_summary()
            print(f"\n{Fore.CYAN}Final Session Summary:{Style.RESET_ALL}")
            print(f"Actions performed: {summary.get('action_count', 0)}")
            print(f"Successful: {summary.get('successful_actions', 0)}")
            print(f"Failed: {summary.get('failed_actions', 0)}")
            print(f"Log files saved in: {Path(summary['log_files']['main_log']).parent}")

@click.command()
@click.option('--root-path', '-r', required=True, 
              help='Root directory path where the organizer can operate')
@click.option('--llm-provider', '-p', default='ollama', 
              type=click.Choice(['openai', 'anthropic', 'ollama', 'lmstudio', 'huggingface'], case_sensitive=False),
              help='LLM provider to use')
@click.option('--model', '-m', default=None,
              help='Specific model to use (optional)')
@click.option('--api-key', '-k', default=None,
              help='API key for cloud LLM providers (or set via environment)')
@click.option('--base-url', '-u', default=None,
              help='Base URL for local LLM servers (Ollama/LM Studio)')
@click.option('--env-file', '-e', default='.env',
              help='Environment file path for loading API keys')
def main(root_path, llm_provider, model, api_key, base_url, env_file):
    # Load environment variables
    if Path(env_file).exists():
        load_dotenv(env_file)
    
    # Get API key from parameter or environment (only for cloud providers)
    if llm_provider.lower() in ['openai', 'anthropic'] and not api_key:
        if llm_provider.lower() == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
        elif llm_provider.lower() == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            print(f"{Fore.RED}Error: API key not provided for {llm_provider}.{Style.RESET_ALL}")
            print(f"Set it via --api-key parameter or environment variable:")
            if llm_provider.lower() == 'openai':
                print(f"For OpenAI: Set OPENAI_API_KEY")
            elif llm_provider.lower() == 'anthropic':
                print(f"For Anthropic: Set ANTHROPIC_API_KEY")
            print(f"\n{Fore.YELLOW}Tip: Use a local LLM instead:{Style.RESET_ALL}")
            print(f"  --llm-provider ollama    (requires Ollama to be running)")
            print(f"  --llm-provider lmstudio  (requires LM Studio to be running)")
            print(f"  --llm-provider huggingface  (downloads model locally)")
            sys.exit(1)
    
    # Expand user path and make absolute
    root_path = os.path.abspath(os.path.expanduser(root_path))
    
    try:
        cli = CLIInterface(root_path, llm_provider, api_key, model, base_url)
        cli.run_interactive()
    except Exception as e:
        print(f"{Fore.RED}Failed to initialize: {str(e)}{Style.RESET_ALL}")
        if "Cannot connect to" in str(e):
            print(f"\n{Fore.YELLOW}Local LLM Setup Help:{Style.RESET_ALL}")
            if "ollama" in str(e).lower():
                print("For Ollama:")
                print("1. Install Ollama: https://ollama.ai/")
                print("2. Run: ollama serve")
                print("3. Pull a model: ollama pull llama3.2")
            elif "lm studio" in str(e).lower():
                print("For LM Studio:")
                print("1. Install LM Studio: https://lmstudio.ai/")
                print("2. Load a model and start the local server")
                print("3. Make sure 'Local Server' is running on port 1234")
        sys.exit(1)

if __name__ == '__main__':
    main()