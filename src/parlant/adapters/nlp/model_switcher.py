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

"""Model switching service for Parlant."""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple, Type, TypeVar, cast
from typing_extensions import override

from parlant.adapters.nlp.local.model_manager import LocalModelManager
from parlant.adapters.nlp.local.llama import LlamaService
from parlant.adapters.nlp.local.deepseek import DeepSeekService
from parlant.core.loggers import Logger
from parlant.core.nlp.embedding import Embedder, EmbeddingResult
from parlant.core.nlp.generation import T, SchematicGenerator, SchematicGenerationResult
from parlant.core.nlp.moderation import ModerationCheck, ModerationService, ModerationTag
from parlant.core.nlp.service import NLPService


class ModelTier(str, Enum):
    """Tiers of models based on capability and cost."""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class ModelLocation(str, Enum):
    """Location of models."""
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


@dataclass
class ModelConfig:
    """Configuration for a model."""
    id: str
    service_class: Type[NLPService]
    tier: ModelTier
    location: ModelLocation
    context_length: int
    parameters: Optional[int] = None
    capabilities: Set[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = set()


class ModelSwitcher(NLPService):
    """Model switching service for Parlant.
    
    This service allows switching between different models based on requirements.
    It can use local models when possible and fall back to cloud models when needed.
    """
    
    def __init__(
        self,
        logger: Logger,
        model_manager: LocalModelManager = None,
        default_model_id: str = None,
        fallback_model_id: str = None,
    ) -> None:
        """Initialize the model switcher.
        
        Args:
            logger: Logger instance
            model_manager: Local model manager
            default_model_id: ID of the default model
            fallback_model_id: ID of the fallback model
        """
        self._logger = logger
        self.model_manager = model_manager or LocalModelManager(logger=logger)
        
        # Initialize model manager if needed
        self._model_manager_initialized = False
        
        # Available models
        self._models: Dict[str, ModelConfig] = {}
        
        # Current model
        self._current_model_id = default_model_id
        self._fallback_model_id = fallback_model_id
        
        # Model instances
        self._model_instances: Dict[str, NLPService] = {}
        
        # Register built-in models
        self._register_builtin_models()
        
        self._logger.info("Initialized ModelSwitcher")
        
    async def initialize(self) -> None:
        """Initialize the model switcher."""
        if not self._model_manager_initialized:
            await self.model_manager.initialize()
            self._model_manager_initialized = True
            
            # Register local models
            await self._register_local_models()
            
            # Set default model if not set
            if not self._current_model_id:
                # Try to use a local model first
                local_models = [
                    model_id for model_id, model in self._models.items()
                    if model.location == ModelLocation.LOCAL
                ]
                
                if local_models:
                    self._current_model_id = local_models[0]
                elif self._models:
                    self._current_model_id = next(iter(self._models.keys()))
                    
            # Set fallback model if not set
            if not self._fallback_model_id:
                # Try to use a cloud model as fallback
                cloud_models = [
                    model_id for model_id, model in self._models.items()
                    if model.location == ModelLocation.CLOUD
                ]
                
                if cloud_models:
                    self._fallback_model_id = cloud_models[0]
                elif self._models and self._current_model_id:
                    # Use a different model than the current one if possible
                    for model_id in self._models.keys():
                        if model_id != self._current_model_id:
                            self._fallback_model_id = model_id
                            break
                    else:
                        # If only one model is available, use it as fallback too
                        self._fallback_model_id = self._current_model_id
                        
            self._logger.info(f"Using default model: {self._current_model_id}")
            self._logger.info(f"Using fallback model: {self._fallback_model_id}")
        
    def _register_builtin_models(self) -> None:
        """Register built-in models."""
        # Register OpenAI models
        self._models["openai/gpt-4o"] = ModelConfig(
            id="openai/gpt-4o",
            service_class=None,  # Will be loaded on demand
            tier=ModelTier.PREMIUM,
            location=ModelLocation.CLOUD,
            context_length=128000,
            parameters=1500000000000,  # 1.5T
            capabilities={"chat", "code", "reasoning", "tool_use", "embeddings", "moderation"}
        )
        
        self._models["openai/gpt-4o-mini"] = ModelConfig(
            id="openai/gpt-4o-mini",
            service_class=None,  # Will be loaded on demand
            tier=ModelTier.STANDARD,
            location=ModelLocation.CLOUD,
            context_length=128000,
            parameters=0,  # Unknown
            capabilities={"chat", "code", "reasoning", "tool_use", "embeddings", "moderation"}
        )
        
        # Register Anthropic models
        self._models["anthropic/claude-3-opus"] = ModelConfig(
            id="anthropic/claude-3-opus",
            service_class=None,  # Will be loaded on demand
            tier=ModelTier.PREMIUM,
            location=ModelLocation.CLOUD,
            context_length=200000,
            parameters=0,  # Unknown
            capabilities={"chat", "code", "reasoning", "tool_use", "moderation"}
        )
        
        self._models["anthropic/claude-3-sonnet"] = ModelConfig(
            id="anthropic/claude-3-sonnet",
            service_class=None,  # Will be loaded on demand
            tier=ModelTier.STANDARD,
            location=ModelLocation.CLOUD,
            context_length=200000,
            parameters=0,  # Unknown
            capabilities={"chat", "code", "reasoning", "tool_use", "moderation"}
        )
        
    async def _register_local_models(self) -> None:
        """Register local models."""
        # Register Llama models
        for model in self.model_manager.list_models(ModelType.LLAMA):
            model_id = model.id
            self._models[model_id] = ModelConfig(
                id=model_id,
                service_class=LlamaService,
                tier=ModelTier.BASIC,
                location=ModelLocation.LOCAL,
                context_length=model.context_length,
                parameters=model.parameters,
                capabilities={"chat", "code", "reasoning"}
            )
            
        # Register DeepSeek models
        for model in self.model_manager.list_models(ModelType.DEEPSEEK):
            model_id = model.id
            self._models[model_id] = ModelConfig(
                id=model_id,
                service_class=DeepSeekService,
                tier=ModelTier.BASIC,
                location=ModelLocation.LOCAL,
                context_length=model.context_length,
                parameters=model.parameters,
                capabilities={"chat", "code", "reasoning"}
            )
            
    async def _get_model_instance(self, model_id: str) -> NLPService:
        """Get a model instance.
        
        Args:
            model_id: ID of the model
            
        Returns:
            Model instance
            
        Raises:
            ValueError: If the model is not found
        """
        if model_id not in self._models:
            raise ValueError(f"Model {model_id} not found")
            
        if model_id not in self._model_instances:
            model_config = self._models[model_id]
            
            if model_config.location == ModelLocation.LOCAL:
                # Local model
                if model_config.service_class == LlamaService:
                    self._model_instances[model_id] = LlamaService(
                        model_manager=self.model_manager,
                        model_id=model_id,
                        logger=self._logger
                    )
                elif model_config.service_class == DeepSeekService:
                    self._model_instances[model_id] = DeepSeekService(
                        model_manager=self.model_manager,
                        model_id=model_id,
                        logger=self._logger
                    )
                else:
                    raise ValueError(f"Unsupported service class for model {model_id}")
            else:
                # Cloud model - import the appropriate service
                if model_id.startswith("openai/"):
                    from parlant.adapters.nlp.openai_service import OpenAIService
                    self._model_instances[model_id] = OpenAIService(logger=self._logger)
                elif model_id.startswith("anthropic/"):
                    from parlant.adapters.nlp.anthropic_service import AnthropicService
                    self._model_instances[model_id] = AnthropicService(logger=self._logger)
                else:
                    raise ValueError(f"Unsupported cloud model {model_id}")
                    
        return self._model_instances[model_id]
        
    def set_model(self, model_id: str) -> None:
        """Set the current model.
        
        Args:
            model_id: ID of the model
            
        Raises:
            ValueError: If the model is not found
        """
        if model_id not in self._models:
            raise ValueError(f"Model {model_id} not found")
            
        self._current_model_id = model_id
        self._logger.info(f"Switched to model {model_id}")
        
    def get_current_model_id(self) -> str:
        """Get the current model ID.
        
        Returns:
            Current model ID
        """
        return self._current_model_id
        
    def list_available_models(self) -> List[ModelConfig]:
        """List available models.
        
        Returns:
            List of available models
        """
        return list(self._models.values())
        
    @override
    async def get_schematic_generator(self, t: type[T]) -> SchematicGenerator[T]:
        """Get a schematic generator for the given type.
        
        Args:
            t: Type to generate
            
        Returns:
            Schematic generator
        """
        try:
            # Try with the current model
            model = await self._get_model_instance(self._current_model_id)
            return await model.get_schematic_generator(t)
        except Exception as e:
            self._logger.warning(f"Failed to get schematic generator from {self._current_model_id}: {e}")
            
            # Try with the fallback model
            if self._fallback_model_id and self._fallback_model_id != self._current_model_id:
                try:
                    model = await self._get_model_instance(self._fallback_model_id)
                    return await model.get_schematic_generator(t)
                except Exception as fallback_e:
                    self._logger.error(f"Failed to get schematic generator from fallback model {self._fallback_model_id}: {fallback_e}")
                    
            # If all else fails, raise the original exception
            raise
            
    @override
    async def get_embedder(self) -> Embedder:
        """Get an embedder.
        
        Returns:
            Embedder
        """
        try:
            # Try with the current model
            model = await self._get_model_instance(self._current_model_id)
            return await model.get_embedder()
        except Exception as e:
            self._logger.warning(f"Failed to get embedder from {self._current_model_id}: {e}")
            
            # Try with the fallback model
            if self._fallback_model_id and self._fallback_model_id != self._current_model_id:
                try:
                    model = await self._get_model_instance(self._fallback_model_id)
                    return await model.get_embedder()
                except Exception as fallback_e:
                    self._logger.error(f"Failed to get embedder from fallback model {self._fallback_model_id}: {fallback_e}")
                    
            # If all else fails, raise the original exception
            raise
            
    @override
    async def get_moderation_service(self) -> ModerationService:
        """Get a moderation service.
        
        Returns:
            Moderation service
        """
        try:
            # Try with the current model
            model = await self._get_model_instance(self._current_model_id)
            return await model.get_moderation_service()
        except Exception as e:
            self._logger.warning(f"Failed to get moderation service from {self._current_model_id}: {e}")
            
            # Try with the fallback model
            if self._fallback_model_id and self._fallback_model_id != self._current_model_id:
                try:
                    model = await self._get_model_instance(self._fallback_model_id)
                    return await model.get_moderation_service()
                except Exception as fallback_e:
                    self._logger.error(f"Failed to get moderation service from fallback model {self._fallback_model_id}: {fallback_e}")
                    
            # If all else fails, raise the original exception
            raise
