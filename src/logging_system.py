import logging
import json
import datetime
from pathlib import Path
from typing import Dict, Any
import os

class FileOrganizerLogger:
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamp for this session
        self.session_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup main logger
        self.logger = logging.getLogger("file_organizer")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler for general logs
        log_file = self.log_dir / f"organizer_{self.session_timestamp}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Separate files for conversations and actions
        self.conversation_file = self.log_dir / f"conversations_{self.session_timestamp}.jsonl"
        self.actions_file = self.log_dir / f"actions_{self.session_timestamp}.jsonl"
        
        self.logger.info(f"Logging session started: {self.session_timestamp}")
        self.logger.info(f"Log files: {log_file}, {self.conversation_file}, {self.actions_file}")
    
    def get_logger(self) -> logging.Logger:
        return self.logger
    
    def log_conversation(self, user_input: str, assistant_response: str, metadata: Dict[str, Any] = None):
        conversation_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "session_id": self.session_timestamp,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "metadata": metadata or {}
        }
        
        try:
            with open(self.conversation_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(conversation_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to log conversation: {str(e)}")
    
    def log_action(self, action: str, parameters: Dict[str, Any], result: Dict[str, Any], 
                   reasoning: str = None, success: bool = None):
        action_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "session_id": self.session_timestamp,
            "action": action,
            "parameters": parameters,
            "result": result,
            "reasoning": reasoning,
            "success": success if success is not None else ("error" not in result),
            "metadata": {
                "working_directory": str(Path.cwd()),
                "user": os.getenv("USER", os.getenv("USERNAME", "unknown"))
            }
        }
        
        try:
            with open(self.actions_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(action_entry, ensure_ascii=False) + '\n')
                
            # Also log to main logger
            log_level = logging.INFO if action_entry["success"] else logging.ERROR
            self.logger.log(log_level, 
                f"Action: {action} | Success: {action_entry['success']} | Result: {result}")
                
        except Exception as e:
            self.logger.error(f"Failed to log action: {str(e)}")
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "WARNING"):
        security_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "session_id": self.session_timestamp,
            "event_type": event_type,
            "severity": severity,
            "details": details
        }
        
        security_file = self.log_dir / f"security_{self.session_timestamp}.jsonl"
        
        try:
            with open(security_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(security_entry, ensure_ascii=False) + '\n')
            
            # Log to main logger with appropriate level
            log_level = getattr(logging, severity.upper(), logging.WARNING)
            self.logger.log(log_level, f"SECURITY EVENT - {event_type}: {details}")
            
        except Exception as e:
            self.logger.error(f"Failed to log security event: {str(e)}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        summary = {
            "session_id": self.session_timestamp,
            "start_time": self.session_timestamp,
            "log_files": {
                "main_log": str(self.log_dir / f"organizer_{self.session_timestamp}.log"),
                "conversations": str(self.conversation_file),
                "actions": str(self.actions_file)
            }
        }
        
        # Count entries if files exist
        try:
            if self.conversation_file.exists():
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    summary["conversation_count"] = sum(1 for _ in f)
            else:
                summary["conversation_count"] = 0
                
            if self.actions_file.exists():
                with open(self.actions_file, 'r', encoding='utf-8') as f:
                    actions = [json.loads(line) for line in f]
                    summary["action_count"] = len(actions)
                    summary["successful_actions"] = sum(1 for a in actions if a.get("success", False))
                    summary["failed_actions"] = summary["action_count"] - summary["successful_actions"]
            else:
                summary["action_count"] = 0
                summary["successful_actions"] = 0
                summary["failed_actions"] = 0
                
        except Exception as e:
            self.logger.error(f"Error generating session summary: {str(e)}")
            summary["error"] = str(e)
        
        return summary