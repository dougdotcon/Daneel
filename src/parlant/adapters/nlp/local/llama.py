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

"""Llama model implementation for Daneel."""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Mapping, Optional, Tuple, TypeVar, cast
from typing_extensions import override
import aiohttp
import numpy as np

from Daneel.adapters.nlp.common import normalize_json_output
from Daneel.adapters.nlp.local.model_manager import LocalModel, LocalModelManager, ModelType
from Daneel.core.engines.alpha.prompt_builder import PromptBuilder
from Daneel.core.engines.alpha.tool_caller import ToolCallInferenceSchema
from Daneel.core.loggers import Logger
from Daneel.core.nlp.embedding import Embedder, EmbeddingResult
from Daneel.core.nlp.generation import T, SchematicGenerator, SchematicGenerationResult
from Daneel.core.nlp.generation_info import GenerationInfo, UsageInfo
from Daneel.core.nlp.moderation import ModerationCheck, ModerationService, ModerationTag
from Daneel.core.nlp.policies import policy, retry
from Daneel.core.nlp.service import NLPService
from Daneel.core.nlp.tokenization import EstimatingTokenizer


class LlamaEstimatingTokenizer(EstimatingTokenizer):
    """Tokenizer for Llama models."""
    
    def __init__(self) -> None:
        """Initialize the tokenizer."""
        pass
        
    @override
    async def estimate_token_count(self, prompt: str) -> int:
        """Estimate the number of tokens in a prompt.
        
        This is a rough estimate based on the number of characters.
        
        Args:
            prompt: The prompt to estimate
            
        Returns:
            Estimated number of tokens
        """
        # Rough estimate: 1 token ≈ 4 characters for English text
        return len(prompt) // 4


class LlamaSchematicGenerator(SchematicGenerator[T]):
    """Schematic generator for Llama models."""
    
    supported_hints = ["temperature", "max_tokens", "top_p", "top_k", "repeat_penalty"]
    
    def __init__(
        self,
        model: LocalModel,
        logger: Logger,
    ) -> None:
        """Initialize the generator.
        
        Args:
            model: The local model to use
            logger: Logger instance
        """
        self.model = model
        self._logger = logger
        self._tokenizer = LlamaEstimatingTokenizer()
        
        # Determine if this is an Ollama model
        self._is_ollama = model.path.startswith("ollama:")
        self._ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        
    @property
    @override
    def id(self) -> str:
        """Get the generator ID."""
        return self.model.id
        
    @property
    @override
    def tokenizer(self) -> LlamaEstimatingTokenizer:
        """Get the tokenizer."""
        return self._tokenizer
        
    @property
    @override
    def max_tokens(self) -> int:
        """Get the maximum number of tokens."""
        return self.model.context_length
        
    @policy(
        [
            retry(
                exceptions=(
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                ),
            ),
        ]
    )
    @override
    async def generate(
        self,
        prompt: str | PromptBuilder,
        hints: Mapping[str, Any] = {},
    ) -> SchematicGenerationResult[T]:
        """Generate a response from the model.
        
        Args:
            prompt: The prompt to generate from
            hints: Generation hints
            
        Returns:
            The generated response
        """
        with self._logger.scope("LlamaSchematicGenerator"):
            with self._logger.operation(f"LLM Request ({self.schema.__name__})"):
                return await self._do_generate(prompt, hints)
                
    async def _do_generate(
        self,
        prompt: str | PromptBuilder,
        hints: Mapping[str, Any] = {},
    ) -> SchematicGenerationResult[T]:
        """Generate a response from the model.
        
        Args:
            prompt: The prompt to generate from
            hints: Generation hints
            
        Returns:
            The generated response
        """
        if isinstance(prompt, PromptBuilder):
            prompt = prompt.build()
            
        # Filter hints
        filtered_hints = {k: v for k, v in hints.items() if k in self.supported_hints}
        
        # Generate response
        if self._is_ollama:
            return await self._generate_with_ollama(prompt, filtered_hints)
        else:
            return await self._generate_with_llama_cpp(prompt, filtered_hints)
            
    async def _generate_with_ollama(
        self,
        prompt: str,
        hints: Mapping[str, Any] = {},
    ) -> SchematicGenerationResult[T]:
        """Generate a response using Ollama.
        
        Args:
            prompt: The prompt to generate from
            hints: Generation hints
            
        Returns:
            The generated response
        """
        model_name = self.model.path.replace("ollama:", "")
        
        # Prepare request
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": hints.get("temperature", 0.7),
                "top_p": hints.get("top_p", 0.9),
                "top_k": hints.get("top_k", 40),
                "repeat_penalty": hints.get("repeat_penalty", 1.1),
            }
        }
        
        if "max_tokens" in hints:
            request_data["options"]["num_predict"] = hints["max_tokens"]
            
        # Send request
        t_start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._ollama_url}/api/generate",
                json=request_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self._logger.error(f"Ollama API error: {error_text}")
                    raise RuntimeError(f"Ollama API error: {error_text}")
                    
                result = await response.json()
                
        t_end = time.time()
        
        # Parse response
        raw_content = result.get("response", "{}")
        
        try:
            json_content = json.loads(normalize_json_output(raw_content))
        except json.JSONDecodeError:
            self._logger.warning(f"Invalid JSON returned by {self.model.name}:\n{raw_content}")
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'({.*})', raw_content, re.DOTALL)
            if json_match:
                try:
                    json_content = json.loads(json_match.group(1))
                    self._logger.warning("Found JSON content within model response; continuing...")
                except json.JSONDecodeError:
                    self._logger.error(f"Failed to extract valid JSON from response")
                    raise
            else:
                self._logger.error(f"Failed to extract JSON from response")
                raise
                
        try:
            content = self.schema.model_validate(json_content)
            
            # Estimate token usage
            input_tokens = await self.tokenizer.estimate_token_count(prompt)
            output_tokens = await self.tokenizer.estimate_token_count(raw_content)
            
            return SchematicGenerationResult(
                content=content,
                info=GenerationInfo(
                    schema_name=self.schema.__name__,
                    model=self.id,
                    duration=(t_end - t_start),
                    usage=UsageInfo(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        extra={},
                    ),
                ),
            )
            
        except Exception as e:
            self._logger.error(
                f"Error: {e}\nJSON content returned by {self.model.name} does not match expected schema:\n{raw_content}"
            )
            raise
            
    async def _generate_with_llama_cpp(
        self,
        prompt: str,
        hints: Mapping[str, Any] = {},
    ) -> SchematicGenerationResult[T]:
        """Generate a response using llama.cpp.
        
        Args:
            prompt: The prompt to generate from
            hints: Generation hints
            
        Returns:
            The generated response
        """
        # This is a placeholder for the llama.cpp implementation
        # In a real implementation, you would use the llama.cpp Python bindings
        # or a server like llama-cpp-python-server
        
        self._logger.error("llama.cpp implementation not available")
        raise NotImplementedError("llama.cpp implementation not available")


class LlamaEmbedder(Embedder):
    """Embedder for Llama models."""
    
    def __init__(
        self,
        model: LocalModel,
        logger: Logger,
    ) -> None:
        """Initialize the embedder.
        
        Args:
            model: The local model to use
            logger: Logger instance
        """
        self.model = model
        self._logger = logger
        self._tokenizer = LlamaEstimatingTokenizer()
        
        # Determine if this is an Ollama model
        self._is_ollama = model.path.startswith("ollama:")
        self._ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        
    @property
    @override
    def id(self) -> str:
        """Get the embedder ID."""
        return self.model.id
        
    @property
    @override
    def tokenizer(self) -> LlamaEstimatingTokenizer:
        """Get the tokenizer."""
        return self._tokenizer
        
    @property
    @override
    def max_tokens(self) -> int:
        """Get the maximum number of tokens."""
        return self.model.context_length
        
    @policy(
        [
            retry(
                exceptions=(
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                ),
            ),
        ]
    )
    @override
    async def embed(
        self,
        texts: list[str],
        hints: Mapping[str, Any] = {},
    ) -> EmbeddingResult:
        """Generate embeddings for texts.
        
        Args:
            texts: Texts to embed
            hints: Embedding hints
            
        Returns:
            The embeddings
        """
        if self._is_ollama:
            return await self._embed_with_ollama(texts, hints)
        else:
            return await self._embed_with_llama_cpp(texts, hints)
            
    async def _embed_with_ollama(
        self,
        texts: list[str],
        hints: Mapping[str, Any] = {},
    ) -> EmbeddingResult:
        """Generate embeddings using Ollama.
        
        Args:
            texts: Texts to embed
            hints: Embedding hints
            
        Returns:
            The embeddings
        """
        model_name = self.model.path.replace("ollama:", "")
        vectors = []
        
        async with aiohttp.ClientSession() as session:
            for text in texts:
                async with session.post(
                    f"{self._ollama_url}/api/embeddings",
                    json={"model": model_name, "prompt": text}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self._logger.error(f"Ollama API error: {error_text}")
                        raise RuntimeError(f"Ollama API error: {error_text}")
                        
                    result = await response.json()
                    vectors.append(result.get("embedding", []))
                    
        return EmbeddingResult(vectors=vectors)
        
    async def _embed_with_llama_cpp(
        self,
        texts: list[str],
        hints: Mapping[str, Any] = {},
    ) -> EmbeddingResult:
        """Generate embeddings using llama.cpp.
        
        Args:
            texts: Texts to embed
            hints: Embedding hints
            
        Returns:
            The embeddings
        """
        # This is a placeholder for the llama.cpp implementation
        # In a real implementation, you would use the llama.cpp Python bindings
        # or a server like llama-cpp-python-server
        
        self._logger.error("llama.cpp implementation not available")
        raise NotImplementedError("llama.cpp implementation not available")


class LlamaModerationService(ModerationService):
    """Moderation service for Llama models."""
    
    def __init__(
        self,
        model: LocalModel,
        logger: Logger,
    ) -> None:
        """Initialize the moderation service.
        
        Args:
            model: The local model to use
            logger: Logger instance
        """
        self.model = model
        self._logger = logger
        
    @override
    async def check(self, content: str) -> ModerationCheck:
        """Check content for moderation issues.
        
        Args:
            content: Content to check
            
        Returns:
            Moderation check result
        """
        # For local models, we'll use a simple keyword-based approach
        # In a real implementation, you would use a more sophisticated approach
        
        keywords = {
            "sexual": ["sex", "porn", "xxx", "adult"],
            "violence": ["kill", "murder", "attack", "bomb"],
            "hate": ["hate", "racist", "nazi"],
            "self-harm": ["suicide", "self-harm", "cut myself"],
            "illicit": ["illegal", "drugs", "cocaine", "heroin"],
            "harassment": ["harass", "bully", "stalk"],
        }
        
        content_lower = content.lower()
        detected_tags = []
        
        for tag, words in keywords.items():
            if any(word in content_lower for word in words):
                detected_tags.append(tag)
                
        return ModerationCheck(
            flagged=len(detected_tags) > 0,
            tags=detected_tags,
        )


class LlamaService(NLPService):
    """NLP service for Llama models."""
    
    def __init__(
        self,
        model_manager: LocalModelManager,
        model_id: str = None,
        logger: Logger = None,
    ) -> None:
        """Initialize the Llama service.
        
        Args:
            model_manager: Local model manager
            model_id: ID of the model to use
            logger: Logger instance
        """
        self.model_manager = model_manager
        self._logger = logger
        
        # If model_id is not provided, use the first available Llama model
        if not model_id:
            llama_models = model_manager.list_models(ModelType.LLAMA)
            if not llama_models:
                raise ValueError("No Llama models available")
            self.model = llama_models[0]
        else:
            self.model = model_manager.get_model(model_id)
            if not self.model:
                raise ValueError(f"Model {model_id} not found")
                
        self._logger.info(f"Initialized LlamaService with model {self.model.id}")
        
    @override
    async def get_schematic_generator(self, t: type[T]) -> LlamaSchematicGenerator[T]:
        """Get a schematic generator for the given type.
        
        Args:
            t: Type to generate
            
        Returns:
            Schematic generator
        """
        return LlamaSchematicGenerator[t](self.model, self._logger)  # type: ignore
        
    @override
    async def get_embedder(self) -> Embedder:
        """Get an embedder.
        
        Returns:
            Embedder
        """
        return LlamaEmbedder(self.model, self._logger)
        
    @override
    async def get_moderation_service(self) -> ModerationService:
        """Get a moderation service.
        
        Returns:
            Moderation service
        """
        return LlamaModerationService(self.model, self._logger)
