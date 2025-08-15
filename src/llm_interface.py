import json
import logging
import requests
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

class OllamaInterface(LLMInterface):
    def __init__(self, model: str = "auto", base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        
        # Test connection to Ollama and get available models
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise Exception(f"Ollama server not responding. Status: {response.status_code}")
            
            # Get available models
            models_data = response.json()
            available_models = [m.get("name", "") for m in models_data.get("models", [])]
            
            if not available_models:
                raise Exception("No models available in Ollama. Please install a model first: ollama pull llama3.2")
            
            # Auto-select model if not specified
            if model == "auto" or model == "llama3.2":
                # Prefer specific models in order of preference
                preferred_models = ["llama3.2:3b", "llama3.2:1b", "llama3.2", "llama3.1", "mistral", "codellama"]
                
                self.model = None
                for preferred in preferred_models:
                    for available in available_models:
                        if preferred in available:
                            self.model = available
                            break
                    if self.model:
                        break
                
                # If no preferred model found, use the first available
                if not self.model:
                    self.model = available_models[0]
                
                print(f"Auto-selected Ollama model: {self.model}")
            else:
                # Use specified model
                self.model = model
                # Verify the model exists
                if not any(model in available for available in available_models):
                    raise Exception(f"Model '{model}' not found. Available models: {', '.join(available_models)}")
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Cannot connect to Ollama at {self.base_url}. Make sure Ollama is running. Error: {str(e)}")
    
    def generate_response(self, messages: List[Dict[str, str]], retry_count: int = 2) -> str:
        import time
        
        for attempt in range(retry_count + 1):
            try:
                # Convert messages to Ollama format
                prompt = self._messages_to_prompt(messages)
                
                # Optimize payload for better performance
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 800,  # Reduced for faster responses
                        "top_p": 0.9,
                        "stop": ["\n\nUser:", "\n\nHuman:"]  # Stop tokens to prevent overgeneration
                    }
                }
                
                # Use progressive timeout: shorter for first attempts, longer for final
                timeout = 60 if attempt < retry_count else 120
                
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=timeout
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
                result = response.json()
                response_text = result.get("response", "").strip()
                
                if response_text:
                    return response_text
                else:
                    raise Exception("Empty response from Ollama")
                    
            except requests.exceptions.Timeout as e:
                if attempt < retry_count:
                    print(f"Ollama timeout (attempt {attempt + 1}/{retry_count + 1}), retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                else:
                    raise Exception(f"Ollama timeout after {retry_count + 1} attempts. Try a simpler query or restart Ollama.")
                    
            except requests.exceptions.ConnectionError as e:
                raise Exception(f"Cannot connect to Ollama. Is it running? Try: ollama serve")
                
            except Exception as e:
                if attempt < retry_count and "timeout" in str(e).lower():
                    print(f"Ollama error (attempt {attempt + 1}/{retry_count + 1}), retrying...")
                    time.sleep(1)
                    continue
                else:
                    raise Exception(f"Ollama API error: {str(e)}")
        
        # Should never reach here, but just in case
        raise Exception("All retry attempts failed")
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        prompt_parts = []
        
        # Optimize: Keep only essential parts to reduce prompt length
        system_content = ""
        recent_messages = messages[-6:]  # Only keep last 6 messages for context
        
        for msg in recent_messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # Compress system prompt for faster processing
                system_content = content[:500] + "..." if len(content) > 500 else content
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                # Keep assistant responses shorter in context
                short_content = content[:200] + "..." if len(content) > 200 else content
                prompt_parts.append(f"Assistant: {short_content}")
        
        # Build optimized prompt
        if system_content:
            final_prompt = f"System: {system_content}\n\n" + "\n\n".join(prompt_parts) + "\n\nAssistant:"
        else:
            final_prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
        
        return final_prompt

class LMStudioInterface(LLMInterface):
    def __init__(self, model: str = "local-model", base_url: str = "http://localhost:1234"):
        self.model = model
        self.base_url = base_url.rstrip('/')
        
        # Test connection to LM Studio
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code != 200:
                raise Exception(f"LM Studio server not responding. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Cannot connect to LM Studio at {self.base_url}. Make sure LM Studio is running with local server enabled. Error: {str(e)}")
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"LM Studio API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            raise Exception(f"LM Studio API error: {str(e)}")

class HuggingFaceLocalInterface(LLMInterface):
    def __init__(self, model: str = "microsoft/DialoGPT-medium"):
        self.model_name = model
        self.model = None
        self.tokenizer = None
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            print(f"Loading model {model}... This may take a few minutes on first run.")
            self.tokenizer = AutoTokenizer.from_pretrained(model)
            self.model = AutoModelForCausalLM.from_pretrained(model)
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            print("Model loaded successfully!")
            
        except ImportError:
            raise ImportError("Transformers library not installed. Run: pip install transformers torch")
        except Exception as e:
            raise Exception(f"Failed to load HuggingFace model {model}: {str(e)}")
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        try:
            import torch
            
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)
            
            # Tokenize
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=512, truncation=True)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new part
            response = response[len(prompt):].strip()
            
            return response if response else "I understand, but I need more context to provide a specific response."
            
        except Exception as e:
            raise Exception(f"HuggingFace local model error: {str(e)}")
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        prompt_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n".join(prompt_parts) + "\nAssistant:"

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
- move_file(source, destination): Move a file to new location (auto-renames if destination exists)
- move_directory(source, destination): Move a directory to new location (auto-renames if destination exists)
- rename_file(old_name, new_name): Rename a file or folder
- create_directory(path): Create a new directory
- remove_empty_directory(path): Remove an empty directory only
- get_file_info(path): Get detailed info about a file or folder
- get_move_preview(source, destination): Preview what would happen in a move operation
- bulk_move_files(patterns, destination): Move multiple files matching patterns safely

When you want to perform an action, respond with a JSON object in this format:
{
  "action": "function_name",
  "parameters": {"param1": "value1", "param2": "value2"},
  "reasoning": "Why you're taking this action"
}

For conversation/questions, respond normally without JSON.

IMPORTANT BEHAVIORAL NOTES:
- When users ask about filesystem structure, current contents, or "what's here", immediately use list_directory to show them
- For informational queries (like "show me", "what files", "structure"), no confirmation needed
- Only ask for confirmation before making changes (moving, renaming, creating, deleting)
- Be helpful and proactive with safe informational actions
- For date-based queries (like "files in 2016" or "what files from 2020"), immediately list directory contents first, then analyze the file names for date patterns
- Keep responses concise and focused to avoid timeout issues
- When users ask about specific years/dates, be proactive and show them what files exist"""

    def _add_to_history(self, role: str, content: str):
        # Truncate very long content to prevent timeouts
        if len(content) > 1000:
            content = content[:1000] + "... [truncated for performance]"
        
        self.conversation_history.append({"role": role, "content": content})
        # Keep only last 6 messages to manage context length and improve performance
        if len(self.conversation_history) > 6:
            self.conversation_history = self.conversation_history[-6:]
    
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
            "get_file_info": self.fs_ops.get_file_info,
            "get_move_preview": self.fs_ops.get_move_preview,
            "bulk_move_files": self.fs_ops.bulk_move_files
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
                    response_parts.append(f"[ERROR] {result['error']}")
                elif "success" in result:
                    response_parts.append(f"[OK] {result['message']}")
                else:
                    # For list_directory or get_file_info, format the output nicely
                    if action_data.get("action") == "list_directory" and "items" in result:
                        items_str = "\n".join([f"{'[DIR]' if item['type'] == 'directory' else '[FILE]'} {item['name']}" 
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