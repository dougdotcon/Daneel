# Copyright 2025 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Local model manager for Daneel."""

import os
import json
import asyncio
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import aiohttp
import requests

from Daneel.core.loggers import Logger


class ModelType(str, Enum):
    """Types of local models."""
    LLAMA = "llama"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    GEMMA = "gemma"
    OTHER = "other"


@dataclass
class LocalModel:
    """Information about a local model."""
    name: str
    path: str
    type: ModelType
    parameters: int
    context_length: int
    quantization: Optional[str] = None
    metadata: Dict[str, str] = None
    
    @property
    def id(self) -> str:
        """Get the model ID."""
        return f"local/{self.type}/{self.name}"


class LocalModelManager:
    """Manager for local models.
    
    This class handles downloading, listing, and managing local models.
    It supports models from Hugging Face, GGUF format, and other sources.
    """
    
    def __init__(
        self, 
        models_dir: str = None,
        logger: Logger = None,
    ):
        """Initialize the local model manager.
        
        Args:
            models_dir: Directory to store local models
            logger: Logger instance
        """
        self.models_dir = models_dir or os.path.expanduser("~/.Daneel/models")
        self.logger = logger
        self._models: Dict[str, LocalModel] = {}
        self._ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        
        # Create models directory if it doesn't exist
        os.makedirs(self.models_dir, exist_ok=True)
        
    async def initialize(self) -> None:
        """Initialize the model manager and scan for local models."""
        await self._scan_models()
        
    async def _scan_models(self) -> None:
        """Scan for local models in the models directory and from Ollama."""
        # Scan local model files
        for model_type in os.listdir(self.models_dir):
            type_dir = os.path.join(self.models_dir, model_type)
            if os.path.isdir(type_dir):
                for model_name in os.listdir(type_dir):
                    model_path = os.path.join(type_dir, model_name)
                    if os.path.isfile(model_path) and (model_path.endswith(".gguf") or model_path.endswith(".bin")):
                        # Try to load metadata
                        metadata_path = f"{model_path}.json"
                        metadata = {}
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, "r") as f:
                                    metadata = json.load(f)
                            except json.JSONDecodeError:
                                self.logger.warning(f"Failed to parse metadata for {model_path}")
                        
                        # Determine model type
                        model_type_enum = ModelType.OTHER
                        try:
                            model_type_enum = ModelType(model_type.lower())
                        except ValueError:
                            pass
                        
                        # Create model entry
                        model = LocalModel(
                            name=model_name,
                            path=model_path,
                            type=model_type_enum,
                            parameters=metadata.get("parameters", 0),
                            context_length=metadata.get("context_length", 4096),
                            quantization=metadata.get("quantization"),
                            metadata=metadata
                        )
                        
                        self._models[model.id] = model
                        self.logger.info(f"Found local model: {model.id}")
        
        # Scan Ollama models
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self._ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        for model_info in data.get("models", []):
                            model_name = model_info.get("name")
                            if model_name:
                                # Determine model type based on name
                                model_type = ModelType.OTHER
                                if "llama" in model_name.lower():
                                    model_type = ModelType.LLAMA
                                elif "deepseek" in model_name.lower():
                                    model_type = ModelType.DEEPSEEK
                                elif "mistral" in model_name.lower():
                                    model_type = ModelType.MISTRAL
                                elif "gemma" in model_name.lower():
                                    model_type = ModelType.GEMMA
                                
                                # Create model entry
                                model = LocalModel(
                                    name=model_name,
                                    path=f"ollama:{model_name}",
                                    type=model_type,
                                    parameters=0,  # Unknown from Ollama API
                                    context_length=model_info.get("details", {}).get("context_length", 4096),
                                    metadata=model_info.get("details", {})
                                )
                                
                                self._models[model.id] = model
                                self.logger.info(f"Found Ollama model: {model.id}")
        except Exception as e:
            self.logger.warning(f"Failed to scan Ollama models: {e}")
    
    async def download_model(
        self, 
        model_name: str, 
        model_type: ModelType,
        source: str = "huggingface",
        quantization: Optional[str] = None
    ) -> Optional[LocalModel]:
        """Download a model from a source.
        
        Args:
            model_name: Name of the model
            model_type: Type of the model
            source: Source of the model (huggingface, ollama)
            quantization: Quantization level (Q4_K_M, Q5_K_M, etc.)
            
        Returns:
            The downloaded model, or None if download failed
        """
        if source == "huggingface":
            return await self._download_from_huggingface(model_name, model_type, quantization)
        elif source == "ollama":
            return await self._download_from_ollama(model_name, model_type)
        else:
            self.logger.error(f"Unsupported model source: {source}")
            return None
    
    async def _download_from_huggingface(
        self, 
        model_name: str, 
        model_type: ModelType,
        quantization: Optional[str] = None
    ) -> Optional[LocalModel]:
        """Download a model from Hugging Face.
        
        Args:
            model_name: Name of the model
            model_type: Type of the model
            quantization: Quantization level
            
        Returns:
            The downloaded model, or None if download failed
        """
        # Create directory for model type if it doesn't exist
        type_dir = os.path.join(self.models_dir, model_type.value)
        os.makedirs(type_dir, exist_ok=True)
        
        # Determine file name and path
        file_name = f"{model_name.replace('/', '_')}"
        if quantization:
            file_name += f"-{quantization}"
        file_name += ".gguf"
        file_path = os.path.join(type_dir, file_name)
        
        # Check if model already exists
        if os.path.exists(file_path):
            self.logger.info(f"Model {model_name} already exists at {file_path}")
            
            # Load metadata if available
            metadata_path = f"{file_path}.json"
            metadata = {}
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse metadata for {file_path}")
            
            # Create and return model
            model = LocalModel(
                name=file_name,
                path=file_path,
                type=model_type,
                parameters=metadata.get("parameters", 0),
                context_length=metadata.get("context_length", 4096),
                quantization=quantization,
                metadata=metadata
            )
            
            self._models[model.id] = model
            return model
        
        # Download model
        self.logger.info(f"Downloading model {model_name} to {file_path}")
        
        # Use huggingface-cli to download the model
        try:
            # This is a simplified example - in a real implementation, you would use
            # the Hugging Face Hub API to download the model
            process = await asyncio.create_subprocess_exec(
                "huggingface-cli", "download", model_name, "--local-dir", type_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"Failed to download model {model_name}: {stderr.decode()}")
                return None
            
            # Create metadata
            metadata = {
                "source": "huggingface",
                "model_name": model_name,
                "quantization": quantization
            }
            
            # Save metadata
            metadata_path = f"{file_path}.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            # Create and return model
            model = LocalModel(
                name=file_name,
                path=file_path,
                type=model_type,
                parameters=0,  # Unknown at this point
                context_length=4096,  # Default
                quantization=quantization,
                metadata=metadata
            )
            
            self._models[model.id] = model
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to download model {model_name}: {e}")
            return None
    
    async def _download_from_ollama(
        self, 
        model_name: str, 
        model_type: ModelType
    ) -> Optional[LocalModel]:
        """Download a model using Ollama.
        
        Args:
            model_name: Name of the model
            model_type: Type of the model
            
        Returns:
            The downloaded model, or None if download failed
        """
        self.logger.info(f"Pulling Ollama model {model_name}")
        
        try:
            # Pull the model using Ollama API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._ollama_url}/api/pull",
                    json={"name": model_name}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Failed to pull Ollama model {model_name}: {error_text}")
                        return None
            
            # Create model entry
            model = LocalModel(
                name=model_name,
                path=f"ollama:{model_name}",
                type=model_type,
                parameters=0,  # Unknown from Ollama API
                context_length=4096,  # Default
                metadata={}
            )
            
            self._models[model.id] = model
            self.logger.info(f"Successfully pulled Ollama model: {model.id}")
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to pull Ollama model {model_name}: {e}")
            return None
    
    def get_model(self, model_id: str) -> Optional[LocalModel]:
        """Get a model by ID.
        
        Args:
            model_id: ID of the model
            
        Returns:
            The model, or None if not found
        """
        return self._models.get(model_id)
    
    def list_models(self, model_type: Optional[ModelType] = None) -> List[LocalModel]:
        """List available models.
        
        Args:
            model_type: Optional filter by model type
            
        Returns:
            List of available models
        """
        if model_type:
            return [model for model in self._models.values() if model.type == model_type]
        return list(self._models.values())
