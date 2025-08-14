import json
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

class LLMInterface(ABC):
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        pass

class OpenAIInterface(LLMInterface):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class AnthropicInterface(LLMInterface):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("Anthropic library not installed. Run: pip install anthropic")
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        try:
            # Convert OpenAI format to Anthropic format
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message += msg["content"] + "\n"
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                system=system_message.strip(),
                messages=user_messages
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

class FilesystemLLM:
    def __init__(self, llm_interface: LLMInterface, filesystem_ops, logger: logging.Logger):
        self.llm = llm_interface
        self.fs_ops = filesystem_ops
        self.logger = logger
        self.conversation_history = []
        
        self.system_prompt = """You are a filesystem organization assistant. Your job is to help users organize and restructure their files and folders according to their instructions.

CRITICAL SAFETY RULES - YOU MUST NEVER VIOLATE THESE:
1. You can ONLY work within the specified root directory
2. You can MOVE files and folders
3. You can RENAME files and folders  
4. You can CREATE new folders
5. You can REMOVE folders ONLY if they are completely empty
6. You CANNOT DELETE or REMOVE files under any circumstances
7. You CANNOT work outside the designated folder
8. You MUST validate all paths are within the allowed directory

AVAILABLE FUNCTIONS:
- list_directory(path): Show contents of a directory
- move_file(source, destination): Move a file to new location
- move_directory(source, destination): Move a directory to new location
- rename_file(old_name, new_name): Rename a file or folder
- create_directory(path): Create a new directory
- remove_empty_directory(path): Remove an empty directory only
- get_file_info(path): Get detailed info about a file or folder

When you want to perform an action, respond with a JSON object in this format:
{
  "action": "function_name",
  "parameters": {"param1": "value1", "param2": "value2"},
  "reasoning": "Why you're taking this action"
}

For conversation/questions, respond normally without JSON.

Always explain what you're doing and ask for confirmation before making significant changes."""

    def _add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        # Keep only last 10 messages to manage context length
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def _parse_llm_response(self, response: str) -> tuple[Optional[Dict], Optional[str]]:
        response = response.strip()
        
        # Try to find JSON in the response
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                json_part = response[start_idx:end_idx+1]
                action_data = json.loads(json_part)
                
                # Extract any text before/after JSON as conversation
                conversation_part = (response[:start_idx] + response[end_idx+1:]).strip()
                conversation_part = conversation_part if conversation_part else None
                
                return action_data, conversation_part
            except json.JSONDecodeError:
                pass
        
        # No valid JSON found, treat as conversation
        return None, response
    
    def _execute_action(self, action_data: Dict) -> Dict[str, Any]:
        action = action_data.get("action")
        parameters = action_data.get("parameters", {})
        reasoning = action_data.get("reasoning", "No reasoning provided")
        
        self.logger.info(f"Executing action: {action} with parameters: {parameters}")
        self.logger.info(f"Reasoning: {reasoning}")
        
        # Map action names to filesystem operations
        action_map = {
            "list_directory": self.fs_ops.list_directory,
            "move_file": self.fs_ops.move_file,
            "move_directory": self.fs_ops.move_directory,
            "rename_file": self.fs_ops.rename_file,
            "create_directory": self.fs_ops.create_directory,
            "remove_empty_directory": self.fs_ops.remove_empty_directory,
            "get_file_info": self.fs_ops.get_file_info
        }
        
        if action not in action_map:
            error_msg = f"Unknown action: {action}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
        try:
            result = action_map[action](**parameters)
            self.logger.info(f"Action result: {result}")
            return result
        except Exception as e:
            error_msg = f"Error executing {action}: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def process_user_input(self, user_input: str) -> str:
        self._add_to_history("user", user_input)
        
        # Prepare messages for LLM
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        
        try:
            # Get LLM response
            llm_response = self.llm.generate_response(messages)
            self.logger.info(f"LLM response: {llm_response}")
            
            # Parse response for actions or conversation
            action_data, conversation = self._parse_llm_response(llm_response)
            
            response_parts = []
            
            # Add conversation part if present
            if conversation:
                response_parts.append(conversation)
            
            # Execute action if present
            if action_data:
                result = self._execute_action(action_data)
                if "error" in result:
                    response_parts.append(f"❌ Error: {result['error']}")
                elif "success" in result:
                    response_parts.append(f"✅ {result['message']}")
                else:
                    # For list_directory or get_file_info, format the output nicely
                    if action_data.get("action") == "list_directory" and "items" in result:
                        items_str = "\n".join([f"{'📁' if item['type'] == 'directory' else '📄'} {item['name']}" 
                                             for item in result["items"]])
                        response_parts.append(f"Directory contents:\n{items_str}")
                    else:
                        response_parts.append(f"Result: {json.dumps(result, indent=2)}")
            
            final_response = "\n\n".join(response_parts)
            self._add_to_history("assistant", final_response)
            
            return final_response
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.logger.error(error_msg)
            self._add_to_history("assistant", error_msg)
            return error_msg