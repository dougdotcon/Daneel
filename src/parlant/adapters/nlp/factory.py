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

"""Factory for creating NLP services."""

from typing import Dict, Optional, Type

from parlant.adapters.nlp.local.model_manager import LocalModelManager, ModelType
from parlant.adapters.nlp.local.llama import LlamaService
from parlant.adapters.nlp.local.deepseek import DeepSeekService
from parlant.adapters.nlp.model_switcher import ModelSwitcher
from parlant.core.loggers import Logger
from parlant.core.nlp.service import NLPService


class NLPServiceFactory:
    """Factory for creating NLP services."""
    
    def __init__(self, logger: Logger) -> None:
        """Initialize the factory.
        
        Args:
            logger: Logger instance
        """
        self._logger = logger
        self._model_manager = LocalModelManager(logger=logger)
        self._model_manager_initialized = False
        
    async def initialize(self) -> None:
        """Initialize the factory."""
        if not self._model_manager_initialized:
            await self._model_manager.initialize()
            self._model_manager_initialized = True
        
    async def create_service(self, service_type: str, **kwargs) -> NLPService:
        """Create an NLP service.
        
        Args:
            service_type: Type of service to create
            **kwargs: Additional arguments for the service
            
        Returns:
            The created service
            
        Raises:
            ValueError: If the service type is not supported
        """
        await self.initialize()
        
        if service_type == "openai":
            from parlant.adapters.nlp.openai_service import OpenAIService
            return OpenAIService(logger=self._logger, **kwargs)
        elif service_type == "anthropic":
            from parlant.adapters.nlp.anthropic_service import AnthropicService
            return AnthropicService(logger=self._logger, **kwargs)
        elif service_type == "llama":
            return LlamaService(
                model_manager=self._model_manager,
                logger=self._logger,
                **kwargs
            )
        elif service_type == "deepseek":
            return DeepSeekService(
                model_manager=self._model_manager,
                logger=self._logger,
                **kwargs
            )
        elif service_type == "model_switcher":
            switcher = ModelSwitcher(
                logger=self._logger,
                model_manager=self._model_manager,
                **kwargs
            )
            await switcher.initialize()
            return switcher
        else:
            raise ValueError(f"Unsupported service type: {service_type}")
            
    async def create_default_service(self) -> NLPService:
        """Create a default NLP service.
        
        Returns:
            The default service
        """
        await self.initialize()
        
        # Try to create a model switcher
        try:
            switcher = ModelSwitcher(
                logger=self._logger,
                model_manager=self._model_manager
            )
            await switcher.initialize()
            return switcher
        except Exception as e:
            self._logger.warning(f"Failed to create model switcher: {e}")
            
        # Try to create a local model service
        try:
            # Check if we have any local models
            llama_models = self._model_manager.list_models(ModelType.LLAMA)
            if llama_models:
                return LlamaService(
                    model_manager=self._model_manager,
                    logger=self._logger
                )
                
            deepseek_models = self._model_manager.list_models(ModelType.DEEPSEEK)
            if deepseek_models:
                return DeepSeekService(
                    model_manager=self._model_manager,
                    logger=self._logger
                )
        except Exception as e:
            self._logger.warning(f"Failed to create local model service: {e}")
            
        # Fall back to OpenAI
        try:
            from parlant.adapters.nlp.openai_service import OpenAIService
            return OpenAIService(logger=self._logger)
        except Exception as e:
            self._logger.warning(f"Failed to create OpenAI service: {e}")
            
        # Fall back to Anthropic
        try:
            from parlant.adapters.nlp.anthropic_service import AnthropicService
            return AnthropicService(logger=self._logger)
        except Exception as e:
            self._logger.warning(f"Failed to create Anthropic service: {e}")
            
        # If all else fails, raise an error
        raise RuntimeError("Failed to create any NLP service")
