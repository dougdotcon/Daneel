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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# from parlant.core.nlp.generation import SchematicGenerator


@dataclass
class Model:
    """Model configuration."""
    id: str
    name: str
    provider: str
    max_tokens: int = 4096
    temperature: float = 0.7
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ModelManager(ABC):
    """Base class for model managers."""

    @abstractmethod
    async def get_model(self, model_id: str) -> Model:
        """Get a model by ID.

        Args:
            model_id: ID of the model

        Returns:
            Model instance
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[Model]:
        """List all available models.

        Returns:
            List of available models
        """
        pass

    @abstractmethod
    async def create_generator(self, model_id: str) -> Any:  # SchematicGenerator:
        """Create a generator for a model.

        Args:
            model_id: ID of the model

        Returns:
            Generator instance
        """
        pass


class SimpleModelManager(ModelManager):
    """Simple implementation of model manager."""

    def __init__(self):
        self._models: Dict[str, Model] = {
            "gpt-4": Model(
                id="gpt-4",
                name="GPT-4",
                provider="openai",
                max_tokens=8192,
                temperature=0.7
            ),
            "gpt-3.5-turbo": Model(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="openai",
                max_tokens=4096,
                temperature=0.7
            ),
        }

    async def get_model(self, model_id: str) -> Model:
        """Get a model by ID."""
        if model_id not in self._models:
            raise ValueError(f"Model not found: {model_id}")
        return self._models[model_id]

    async def list_models(self) -> List[Model]:
        """List all available models."""
        return list(self._models.values())

    async def create_generator(self, model_id: str) -> Any:  # SchematicGenerator:
        """Create a generator for a model."""
        # This would normally create a real generator
        # For now, return a placeholder
        raise NotImplementedError("Generator creation not implemented")
