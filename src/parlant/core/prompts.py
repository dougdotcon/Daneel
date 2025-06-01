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


@dataclass
class Prompt:
    """Prompt configuration."""
    id: str
    name: str
    template: str
    variables: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []
        if self.metadata is None:
            self.metadata = {}


class PromptManager(ABC):
    """Base class for prompt managers."""
    
    @abstractmethod
    async def get_prompt(self, prompt_id: str) -> Prompt:
        """Get a prompt by ID.
        
        Args:
            prompt_id: ID of the prompt
            
        Returns:
            Prompt instance
        """
        pass
        
    @abstractmethod
    async def list_prompts(self) -> List[Prompt]:
        """List all available prompts.
        
        Returns:
            List of available prompts
        """
        pass
        
    @abstractmethod
    async def render_prompt(self, prompt_id: str, variables: Dict[str, Any]) -> str:
        """Render a prompt with variables.
        
        Args:
            prompt_id: ID of the prompt
            variables: Variables to substitute
            
        Returns:
            Rendered prompt
        """
        pass


class SimplePromptManager(PromptManager):
    """Simple implementation of prompt manager."""
    
    def __init__(self):
        self._prompts: Dict[str, Prompt] = {
            "system": Prompt(
                id="system",
                name="System Prompt",
                template="You are a helpful AI assistant.",
                variables=[]
            ),
            "user": Prompt(
                id="user",
                name="User Prompt", 
                template="User: {message}",
                variables=["message"]
            ),
        }
        
    async def get_prompt(self, prompt_id: str) -> Prompt:
        """Get a prompt by ID."""
        if prompt_id not in self._prompts:
            raise ValueError(f"Prompt not found: {prompt_id}")
        return self._prompts[prompt_id]
        
    async def list_prompts(self) -> List[Prompt]:
        """List all available prompts."""
        return list(self._prompts.values())
        
    async def render_prompt(self, prompt_id: str, variables: Dict[str, Any]) -> str:
        """Render a prompt with variables."""
        prompt = await self.get_prompt(prompt_id)
        return prompt.template.format(**variables)
