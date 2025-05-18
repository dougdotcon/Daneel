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

"""Tests for the model integration."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Optional

from parlant.adapters.nlp.local.model_manager import LocalModelManager, ModelType, LocalModel
from parlant.adapters.nlp.local.llama import LlamaService, LlamaSchematicGenerator
from parlant.adapters.nlp.local.deepseek import DeepSeekService, DeepSeekSchematicGenerator
from parlant.adapters.nlp.model_switcher import ModelSwitcher, ModelTier, ModelLocation
from parlant.adapters.nlp.factory import NLPServiceFactory
from parlant.core.nlp.service import NLPService


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.scope = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
    logger.operation = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
    return logger


@pytest.fixture
def mock_model_manager():
    """Create a mock model manager."""
    manager = MagicMock(spec=LocalModelManager)
    manager.initialize = AsyncMock()
    
    # Create mock models
    llama_model = LocalModel(
        name="llama-7b-q4",
        path="ollama:llama-7b-q4",
        type=ModelType.LLAMA,
        parameters=7000000000,
        context_length=4096,
        quantization="q4"
    )
    
    deepseek_model = LocalModel(
        name="deepseek-coder-7b-q4",
        path="ollama:deepseek-coder-7b-q4",
        type=ModelType.DEEPSEEK,
        parameters=7000000000,
        context_length=4096,
        quantization="q4"
    )
    
    # Set up the mock to return these models
    manager.list_models = MagicMock(side_effect=lambda model_type=None: {
        ModelType.LLAMA: [llama_model],
        ModelType.DEEPSEEK: [deepseek_model],
        None: [llama_model, deepseek_model]
    }[model_type])
    
    manager.get_model = MagicMock(side_effect=lambda model_id: {
        "local/llama/llama-7b-q4": llama_model,
        "local/deepseek/deepseek-coder-7b-q4": deepseek_model
    }.get(model_id))
    
    return manager


@pytest.mark.asyncio
async def test_model_manager_initialization(mock_logger):
    """Test initializing the model manager."""
    with patch("aiohttp.ClientSession") as mock_session:
        # Mock the response from Ollama API
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "models": [
                {"name": "llama-7b-q4", "details": {"context_length": 4096}},
                {"name": "deepseek-coder-7b-q4", "details": {"context_length": 4096}}
            ]
        })
        
        # Set up the mock session to return the mock response
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.get.return_value = mock_session_instance
        
        # Create the model manager
        manager = LocalModelManager(logger=mock_logger)
        
        # Initialize the manager
        await manager.initialize()
        
        # Check that the logger was called
        mock_logger.info.assert_called()


@pytest.mark.asyncio
async def test_llama_service(mock_logger, mock_model_manager):
    """Test the Llama service."""
    # Create the service
    service = LlamaService(
        model_manager=mock_model_manager,
        model_id="local/llama/llama-7b-q4",
        logger=mock_logger
    )
    
    # Check that the service was initialized correctly
    assert service.model.name == "llama-7b-q4"
    assert service.model.type == ModelType.LLAMA
    
    # Mock the schematic generator
    with patch("parlant.adapters.nlp.local.llama.LlamaSchematicGenerator") as mock_generator:
        # Set up the mock generator
        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance
        
        # Get a schematic generator
        generator = await service.get_schematic_generator(Dict)
        
        # Check that the generator was created correctly
        mock_generator.assert_called_once()
        assert generator == mock_generator_instance


@pytest.mark.asyncio
async def test_deepseek_service(mock_logger, mock_model_manager):
    """Test the DeepSeek service."""
    # Create the service
    service = DeepSeekService(
        model_manager=mock_model_manager,
        model_id="local/deepseek/deepseek-coder-7b-q4",
        logger=mock_logger
    )
    
    # Check that the service was initialized correctly
    assert service.model.name == "deepseek-coder-7b-q4"
    assert service.model.type == ModelType.DEEPSEEK
    
    # Mock the schematic generator
    with patch("parlant.adapters.nlp.local.deepseek.DeepSeekSchematicGenerator") as mock_generator:
        # Set up the mock generator
        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance
        
        # Get a schematic generator
        generator = await service.get_schematic_generator(Dict)
        
        # Check that the generator was created correctly
        mock_generator.assert_called_once()
        assert generator == mock_generator_instance


@pytest.mark.asyncio
async def test_model_switcher(mock_logger, mock_model_manager):
    """Test the model switcher."""
    # Create the switcher
    switcher = ModelSwitcher(
        logger=mock_logger,
        model_manager=mock_model_manager
    )
    
    # Initialize the switcher
    await switcher.initialize()
    
    # Check that the switcher was initialized correctly
    assert switcher._model_manager_initialized is True
    
    # Check that the default model was set
    assert switcher._current_model_id is not None
    assert switcher._fallback_model_id is not None
    
    # Test switching models
    model_id = "local/llama/llama-7b-q4"
    switcher.set_model(model_id)
    assert switcher.get_current_model_id() == model_id
    
    # Test listing available models
    models = switcher.list_available_models()
    assert len(models) > 0
    
    # Mock the model instance
    with patch.object(switcher, "_get_model_instance") as mock_get_instance:
        # Set up the mock instance
        mock_instance = MagicMock(spec=NLPService)
        mock_instance.get_schematic_generator = AsyncMock()
        mock_get_instance.return_value = mock_instance
        
        # Get a schematic generator
        await switcher.get_schematic_generator(Dict)
        
        # Check that the correct model was used
        mock_get_instance.assert_called_once_with(model_id)
        mock_instance.get_schematic_generator.assert_called_once_with(Dict)


@pytest.mark.asyncio
async def test_nlp_service_factory(mock_logger, mock_model_manager):
    """Test the NLP service factory."""
    # Create the factory
    factory = NLPServiceFactory(logger=mock_logger)
    
    # Mock the model manager
    factory._model_manager = mock_model_manager
    
    # Initialize the factory
    await factory.initialize()
    
    # Test creating a Llama service
    with patch("parlant.adapters.nlp.local.llama.LlamaService") as mock_llama_service:
        # Set up the mock service
        mock_service = MagicMock(spec=NLPService)
        mock_llama_service.return_value = mock_service
        
        # Create the service
        service = await factory.create_service("llama")
        
        # Check that the service was created correctly
        mock_llama_service.assert_called_once()
        assert service == mock_service
        
    # Test creating a DeepSeek service
    with patch("parlant.adapters.nlp.local.deepseek.DeepSeekService") as mock_deepseek_service:
        # Set up the mock service
        mock_service = MagicMock(spec=NLPService)
        mock_deepseek_service.return_value = mock_service
        
        # Create the service
        service = await factory.create_service("deepseek")
        
        # Check that the service was created correctly
        mock_deepseek_service.assert_called_once()
        assert service == mock_service
        
    # Test creating a model switcher
    with patch("parlant.adapters.nlp.model_switcher.ModelSwitcher") as mock_switcher:
        # Set up the mock switcher
        mock_service = MagicMock(spec=NLPService)
        mock_service.initialize = AsyncMock()
        mock_switcher.return_value = mock_service
        
        # Create the service
        service = await factory.create_service("model_switcher")
        
        # Check that the service was created correctly
        mock_switcher.assert_called_once()
        mock_service.initialize.assert_called_once()
        assert service == mock_service
        
    # Test creating a default service
    with patch("parlant.adapters.nlp.model_switcher.ModelSwitcher") as mock_switcher:
        # Set up the mock switcher
        mock_service = MagicMock(spec=NLPService)
        mock_service.initialize = AsyncMock()
        mock_switcher.return_value = mock_service
        
        # Create the service
        service = await factory.create_default_service()
        
        # Check that the service was created correctly
        mock_switcher.assert_called_once()
        mock_service.initialize.assert_called_once()
        assert service == mock_service
