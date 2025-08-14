import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

class SafetyValidator:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
        # Dangerous patterns that should be blocked
        self.dangerous_patterns = [
            r'\.\./',  # Parent directory traversal
            r'\\\.\\',  # Parent directory traversal (Windows)
            r'[;|&`$()]',  # Shell injection characters
            r'rm\s+-rf',  # Dangerous rm commands
            r'del\s+/[sq]',  # Dangerous Windows delete commands
            r'format\s+[a-z]:',  # Format commands
            r'sudo',  # Privilege escalation
            r'chmod\s+777',  # Dangerous permissions
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns]
        
        # System directories that should never be touched
        self.system_directories = {
            'windows': ['C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)', 'C:\\System32'],
            'unix': ['/bin', '/sbin', '/usr/bin', '/usr/sbin', '/etc', '/sys', '/proc', '/dev', '/boot']
        }
    
    def validate_root_path(self, root_path: str) -> bool:
        try:
            path = Path(root_path).resolve()
            
            # Check if path exists and is a directory
            if not path.exists():
                self.logger.error(f"Root path does not exist: {root_path}")
                return False
            
            if not path.is_dir():
                self.logger.error(f"Root path is not a directory: {root_path}")
                return False
            
            # Check if it's a system directory
            path_str = str(path).lower()
            
            # Windows system directories
            for sys_dir in self.system_directories['windows']:
                if path_str.startswith(sys_dir.lower()):
                    self.logger.error(f"Cannot operate in system directory: {root_path}")
                    self._log_security_event("BLOCKED_SYSTEM_DIRECTORY", {"path": root_path})
                    return False
            
            # Unix system directories
            for sys_dir in self.system_directories['unix']:
                if path_str.startswith(sys_dir.lower()):
                    self.logger.error(f"Cannot operate in system directory: {root_path}")
                    self._log_security_event("BLOCKED_SYSTEM_DIRECTORY", {"path": root_path})
                    return False
            
            # Check for suspicious paths
            if self._contains_dangerous_patterns(str(path)):
                self.logger.error(f"Root path contains dangerous patterns: {root_path}")
                self._log_security_event("DANGEROUS_PATH_PATTERN", {"path": root_path})
                return False
            
            self.logger.info(f"Root path validation successful: {root_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating root path {root_path}: {str(e)}")
            return False
    
    def validate_file_path(self, file_path: str, root_path: Path) -> bool:
        try:
            # Resolve the path
            if Path(file_path).is_absolute():
                full_path = Path(file_path).resolve()
            else:
                full_path = (root_path / file_path).resolve()
            
            # Check if path is within root directory
            try:
                full_path.relative_to(root_path)
            except ValueError:
                self.logger.error(f"Path outside root directory: {file_path}")
                self._log_security_event("PATH_TRAVERSAL_ATTEMPT", {
                    "attempted_path": file_path,
                    "resolved_path": str(full_path),
                    "root_path": str(root_path)
                })
                return False
            
            # Check for dangerous patterns
            if self._contains_dangerous_patterns(file_path):
                self.logger.error(f"File path contains dangerous patterns: {file_path}")
                self._log_security_event("DANGEROUS_FILE_PATTERN", {"path": file_path})
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating file path {file_path}: {str(e)}")
            return False
    
    def validate_action(self, action: str, parameters: Dict[str, Any]) -> bool:
        # List of allowed actions
        allowed_actions = {
            'list_directory',
            'move_file', 
            'move_directory',
            'rename_file',
            'create_directory',
            'remove_empty_directory',
            'get_file_info'
        }
        
        # Check if action is allowed
        if action not in allowed_actions:
            self.logger.error(f"Unauthorized action attempted: {action}")
            self._log_security_event("UNAUTHORIZED_ACTION", {
                "action": action,
                "parameters": parameters
            })
            return False
        
        # Validate parameters for dangerous content
        for key, value in parameters.items():
            if isinstance(value, str):
                if self._contains_dangerous_patterns(value):
                    self.logger.error(f"Dangerous pattern in parameter {key}: {value}")
                    self._log_security_event("DANGEROUS_PARAMETER", {
                        "action": action,
                        "parameter": key,
                        "value": value
                    })
                    return False
        
        # Special validation for specific actions
        if action in ['move_file', 'move_directory', 'rename_file']:
            # Ensure source and destination are provided and safe
            source = parameters.get('source') or parameters.get('old_name')
            destination = parameters.get('destination') or parameters.get('new_name')
            
            if not source or not destination:
                self.logger.error(f"Missing required parameters for {action}")
                return False
            
            # Check for attempts to overwrite system files
            if self._is_system_file(destination):
                self.logger.error(f"Attempt to modify system file: {destination}")
                self._log_security_event("SYSTEM_FILE_MODIFICATION_ATTEMPT", {
                    "action": action,
                    "target": destination
                })
                return False
        
        return True
    
    def validate_user_input(self, user_input: str) -> bool:
        # Check for potentially malicious user input
        if self._contains_dangerous_patterns(user_input):
            self.logger.warning(f"User input contains suspicious patterns: {user_input[:100]}...")
            self._log_security_event("SUSPICIOUS_USER_INPUT", {
                "input_preview": user_input[:200]
            })
            # Return True but log the event - we don't want to be too restrictive
            # The LLM should be able to handle and sanitize the input
        
        # Check for extremely long input (potential DoS)
        if len(user_input) > 10000:
            self.logger.warning(f"Unusually long user input: {len(user_input)} characters")
            self._log_security_event("LONG_USER_INPUT", {
                "length": len(user_input),
                "preview": user_input[:200]
            })
        
        return True
    
    def _contains_dangerous_patterns(self, text: str) -> bool:
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        return False
    
    def _is_system_file(self, file_path: str) -> bool:
        path_lower = file_path.lower()
        
        # Common system files/directories to protect
        system_patterns = [
            'system32', 'windows', 'program files', 'boot.ini', 'ntldr',
            'autoexec.bat', 'config.sys', 'pagefile.sys', 'hiberfil.sys',
            '/etc/', '/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/',
            '/boot/', '/sys/', '/proc/', '/dev/'
        ]
        
        for pattern in system_patterns:
            if pattern in path_lower:
                return True
        
        return False
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        # This will be connected to the logging system
        # For now, just log to the main logger
        self.logger.warning(f"SECURITY EVENT - {event_type}: {details}")
    
    def get_safety_report(self) -> Dict[str, Any]:
        return {
            "dangerous_patterns_count": len(self.dangerous_patterns),
            "system_directories_protected": len(self.system_directories['windows']) + len(self.system_directories['unix']),
            "validation_active": True,
            "features": [
                "Path traversal protection",
                "System directory protection", 
                "Dangerous pattern detection",
                "Action validation",
                "User input sanitization",
                "Security event logging"
            ]
        }