#!/usr/bin/env python3
"""
Qwen LLM Integration for K8sGPT
Provides Qwen model configuration and management for K8sGPT backend
"""

import json
import os
import logging
import requests
import yaml
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path

class QwenIntegration:
    """Qwen LLM integration manager for K8sGPT"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.home() / '.k8sgpt'
        self.config_file = self.config_dir / 'qwen_config.yaml'
        
    def setup_qwen_backend(self, config: Dict[str, Any]) -> bool:
        """Setup Qwen backend for K8sGPT"""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(exist_ok=True)
            
            # Validate configuration
            validated_config = self._validate_qwen_config(config)
            
            # Save configuration
            self._save_qwen_config(validated_config)
            
            # Configure K8sGPT to use Qwen
            self._configure_k8sgpt_qwen(validated_config)
            
            # Test connection
            if self._test_qwen_connection(validated_config):
                self.logger.info("Qwen backend setup completed successfully")
                return True
            else:
                self.logger.error("Qwen backend connection test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Qwen backend setup failed: {e}")
            return False
    
    def _validate_qwen_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize Qwen configuration"""
        required_fields = ['model', 'baseurl']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        validated_config = {
            'model': config['model'],
            'baseurl': config['baseurl'].rstrip('/'),
            'api_key': config.get('api_key', os.getenv('QWEN_API_KEY', '')),
            'max_tokens': config.get('max_tokens', 4096),
            'temperature': config.get('temperature', 0.7),
            'timeout': config.get('timeout', 300),
            'retry_attempts': config.get('retry_attempts', 3),
            'backend_type': 'localai'  # Use LocalAI backend for OpenAI compatibility
        }
        
        # Validate model name
        valid_models = [
            'qwen2.5-7b-instruct',
            'qwen2.5-14b-instruct', 
            'qwen2.5-72b-instruct',
            'qwen2-7b-instruct',
            'qwen2-72b-instruct',
            'qwen1.5-7b-chat',
            'qwen1.5-14b-chat',
            'qwen1.5-72b-chat'
        ]
        
        if validated_config['model'] not in valid_models:
            self.logger.warning(f"Unknown model: {validated_config['model']}. Supported: {valid_models}")
        
        return validated_config
    
    def _save_qwen_config(self, config: Dict[str, Any]) -> None:
        """Save Qwen configuration to file"""
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Qwen configuration saved to {self.config_file}")
    
    def _configure_k8sgpt_qwen(self, config: Dict[str, Any]) -> None:
        """Configure K8sGPT to use Qwen backend"""
        try:
            # Remove existing Qwen configuration if present
            subprocess.run(['k8sgpt', 'auth', 'remove', '--backend', 'localai'], 
                         capture_output=True, check=False)
            
            # Add new Qwen configuration
            cmd = [
                'k8sgpt', 'auth', 'add',
                '--backend', config['backend_type'],
                '--model', config['model'],
                '--baseurl', f"{config['baseurl']}/v1"
            ]
            
            if config['api_key']:
                cmd.extend(['--password', config['api_key']])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("K8sGPT configured for Qwen backend")
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to configure K8sGPT for Qwen: {e.stderr}")
    
    def _test_qwen_connection(self, config: Dict[str, Any]) -> bool:
        """Test connection to Qwen LLM"""
        try:
            # Prepare test request
            url = f"{config['baseurl']}/v1/chat/completions"
            headers = {
                'Content-Type': 'application/json'
            }
            
            if config['api_key']:
                headers['Authorization'] = f"Bearer {config['api_key']}"
            
            payload = {
                'model': config['model'],
                'messages': [
                    {
                        'role': 'user',
                        'content': 'Hello, can you respond with "Qwen LLM is working"?'
                    }
                ],
                'max_tokens': 50,
                'temperature': 0.1
            }
            
            # Send test request
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    self.logger.info(f"Qwen connection test successful: {content}")
                    return True
                else:
                    self.logger.error(f"Invalid response format: {result}")
                    return False
            else:
                self.logger.error(f"Qwen connection failed with status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Qwen connection test failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during Qwen connection test: {e}")
            return False
    
    def get_qwen_models(self, baseurl: str) -> List[str]:
        """Get available Qwen models from the backend"""
        try:
            url = f"{baseurl.rstrip('/')}/v1/models"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return [model['id'] for model in data['data']]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get Qwen models: {e}")
            return []
    
    def setup_local_qwen(self, model_path: str, port: int = 8000) -> bool:
        """Setup local Qwen inference server"""
        try:
            # Check if required tools are available
            try:
                subprocess.run(['python3', '--version'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                raise RuntimeError("Python3 is required for local Qwen setup")
            
            # Install required packages
            packages = ['torch', 'transformers', 'accelerate', 'fastapi', 'uvicorn']
            for package in packages:
                subprocess.run(['pip3', 'install', package], check=True)
            
            # Create local server script
            server_script = self._create_local_server_script(model_path, port)
            
            # Start the server (in background for this example)
            self.logger.info(f"Local Qwen server setup completed. Start with: python3 {server_script}")
            return True
            
        except Exception as e:
            self.logger.error(f"Local Qwen setup failed: {e}")
            return False
    
    def _create_local_server_script(self, model_path: str, port: int) -> str:
        """Create local Qwen server script"""
        script_content = f'''#!/usr/bin/env python3
"""
Local Qwen LLM Server
OpenAI-compatible API for Qwen models
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import json

app = FastAPI(title="Qwen LLM Server")

# Load model
try:
    tokenizer = AutoTokenizer.from_pretrained("{model_path}", trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        "{model_path}", 
        trust_remote_code=True,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
    print("Qwen model loaded successfully")
except Exception as e:
    print(f"Failed to load Qwen model: {{e}}")
    exit(1)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: int = 1000
    temperature: float = 0.7
    stream: bool = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        # Convert messages to prompt
        messages = [{{"role": msg.role, "content": msg.content}} for msg in request.messages]
        
        # Generate response
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        outputs = pipe(
            prompt,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=True,
            top_p=0.95,
        )
        
        response_text = outputs[0]["generated_text"][len(prompt):]
        
        # Format response
        response = ChatCompletionResponse(
            id="chatcmpl-" + str(hash(request.model + str(request.messages))),
            created=1234567890,
            model=request.model,
            choices=[{{
                "index": 0,
                "message": {{
                    "role": "assistant",
                    "content": response_text
                }},
                "finish_reason": "stop"
            }}],
            usage={{
                "prompt_tokens": len(prompt),
                "completion_tokens": len(response_text),
                "total_tokens": len(prompt) + len(response_text)
            }}
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    return {{
        "object": "list",
        "data": [
            {{
                "id": "{model_path}",
                "object": "model",
                "created": 1234567890,
                "owned_by": "local"
            }}
        ]
    }}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port={port})
'''
        
        script_path = self.config_dir / 'local_qwen_server.py'
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        return str(script_path)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current Qwen integration status"""
        status = {
            'configured': False,
            'backend': None,
            'model': None,
            'connection_status': 'unknown',
            'config_file': str(self.config_file) if self.config_file.exists() else None
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    status.update({
                        'configured': True,
                        'backend': config.get('backend_type'),
                        'model': config.get('model'),
                        'baseurl': config.get('baseurl')
                    })
                
                # Test connection if configured
                if status['configured']:
                    if self._test_qwen_connection(config):
                        status['connection_status'] = 'connected'
                    else:
                        status['connection_status'] = 'disconnected'
            
            # Check K8sGPT authentication status
            try:
                result = subprocess.run(['k8sgpt', 'auth', 'list'], 
                                      capture_output=True, text=True, check=True)
                status['k8sgpt_auth'] = result.stdout.strip()
            except subprocess.CalledProcessError:
                status['k8sgpt_auth'] = 'Error checking auth status'
                
        except Exception as e:
            status['error'] = str(e)
        
        return status

def main():
    """CLI interface for Qwen integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Qwen LLM Integration for K8sGPT')
    parser.add_argument('action', choices=['setup', 'status', 'test', 'local-setup'],
                       help='Action to perform')
    parser.add_argument('--model', default='qwen2.5-7b-instruct',
                       help='Qwen model name')
    parser.add_argument('--baseurl', default='http://localhost:8000',
                       help='Qwen API base URL')
    parser.add_argument('--api-key', help='Qwen API key (if required)')
    parser.add_argument('--model-path', help='Local model path for local setup')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port for local server')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    qwen = QwenIntegration()
    
    if args.action == 'setup':
        config = {
            'model': args.model,
            'baseurl': args.baseurl,
            'api_key': args.api_key
        }
        
        success = qwen.setup_qwen_backend(config)
        if success:
            print("✅ Qwen backend setup completed successfully")
        else:
            print("❌ Qwen backend setup failed")
            exit(1)
    
    elif args.action == 'status':
        status = qwen.get_status()
        print(json.dumps(status, indent=2))
    
    elif args.action == 'test':
        if not qwen.config_file.exists():
            print("❌ Qwen configuration not found. Run 'setup' first.")
            exit(1)
        
        with open(qwen.config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        if qwen._test_qwen_connection(config):
            print("✅ Qwen connection test successful")
        else:
            print("❌ Qwen connection test failed")
            exit(1)
    
    elif args.action == 'local-setup':
        if not args.model_path:
            print("❌ --model-path required for local setup")
            exit(1)
        
        success = qwen.setup_local_qwen(args.model_path, args.port)
        if success:
            print(f"✅ Local Qwen server setup completed for port {args.port}")
        else:
            print("❌ Local Qwen server setup failed")
            exit(1)

if __name__ == "__main__":
    main()
