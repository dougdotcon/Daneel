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

"""Prompt management system for Parlant."""

import os
import json
import glob
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import yaml

from parlant.core.loggers import Logger
from parlant.core.prompts.common import (
    Prompt, PromptMetadata, PromptVariable, 
    PromptType, PromptFormat, PromptCategory,
    extract_variables_from_template
)


class PromptManager:
    """Manager for prompts in Parlant.
    
    This class handles loading, saving, and managing prompts.
    It supports prompts from various sources and formats.
    """
    
    def __init__(
        self,
        prompts_dir: str = None,
        logger: Logger = None,
    ):
        """Initialize the prompt manager.
        
        Args:
            prompts_dir: Directory to store prompts
            logger: Logger instance
        """
        self.prompts_dir = prompts_dir or os.path.join(os.path.dirname(__file__), "prompts")
        self.logger = logger
        self._prompts: Dict[str, Prompt] = {}
        
        # Create prompts directory if it doesn't exist
        os.makedirs(self.prompts_dir, exist_ok=True)
        
        # Create subdirectories for different prompt categories
        for category in PromptCategory:
            os.makedirs(os.path.join(self.prompts_dir, category.value), exist_ok=True)
            
    def load_prompts(self) -> None:
        """Load all prompts from the prompts directory."""
        # Load JSON prompts
        json_files = glob.glob(os.path.join(self.prompts_dir, "**", "*.json"), recursive=True)
        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    prompt = Prompt.from_dict(data)
                    self._prompts[prompt.metadata.id] = prompt
                    if self.logger:
                        self.logger.info(f"Loaded prompt: {prompt.metadata.id}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to load prompt from {file_path}: {e}")
                    
        # Load YAML prompts
        yaml_files = glob.glob(os.path.join(self.prompts_dir, "**", "*.yaml"), recursive=True)
        yaml_files.extend(glob.glob(os.path.join(self.prompts_dir, "**", "*.yml"), recursive=True))
        for file_path in yaml_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    prompt = Prompt.from_dict(data)
                    self._prompts[prompt.metadata.id] = prompt
                    if self.logger:
                        self.logger.info(f"Loaded prompt: {prompt.metadata.id}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to load prompt from {file_path}: {e}")
                    
        # Load text prompts
        text_files = glob.glob(os.path.join(self.prompts_dir, "**", "*.txt"), recursive=True)
        for file_path in text_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Try to extract metadata from the first few lines
                metadata = self._extract_metadata_from_text(content, file_path)
                
                # Create prompt
                prompt = Prompt(
                    metadata=metadata,
                    content=content,
                    variables=[]
                )
                
                # Extract variables
                variable_names = extract_variables_from_template(content)
                for name in variable_names:
                    prompt.variables.append(
                        PromptVariable(
                            name=name,
                            description=f"Variable {name}",
                            required=True
                        )
                    )
                    
                self._prompts[prompt.metadata.id] = prompt
                if self.logger:
                    self.logger.info(f"Loaded prompt: {prompt.metadata.id}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to load prompt from {file_path}: {e}")
                    
    def _extract_metadata_from_text(self, content: str, file_path: str) -> PromptMetadata:
        """Extract metadata from text content.
        
        Args:
            content: Text content
            file_path: Path to the file
            
        Returns:
            Extracted metadata
        """
        # Default metadata
        file_name = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_name)[0]
        
        # Try to extract YAML frontmatter
        yaml_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if yaml_match:
            try:
                yaml_content = yaml_match.group(1)
                metadata_dict = yaml.safe_load(yaml_content)
                
                return PromptMetadata(
                    id=metadata_dict.get("id", file_name_without_ext),
                    name=metadata_dict.get("name", file_name_without_ext),
                    description=metadata_dict.get("description", ""),
                    version=metadata_dict.get("version", "1.0.0"),
                    author=metadata_dict.get("author", "Unknown"),
                    created_at=metadata_dict.get("created_at", datetime.now().isoformat()),
                    updated_at=metadata_dict.get("updated_at", datetime.now().isoformat()),
                    tags=metadata_dict.get("tags", []),
                    source=metadata_dict.get("source"),
                    license=metadata_dict.get("license"),
                    model_compatibility=metadata_dict.get("model_compatibility", []),
                    prompt_type=PromptType(metadata_dict.get("prompt_type", PromptType.SYSTEM)),
                    prompt_format=PromptFormat(metadata_dict.get("prompt_format", PromptFormat.TEXT)),
                    prompt_category=PromptCategory(metadata_dict.get("prompt_category", PromptCategory.GENERAL)),
                )
            except Exception:
                pass
                
        # Default metadata if extraction failed
        return PromptMetadata(
            id=file_name_without_ext,
            name=file_name_without_ext,
            description="",
            version="1.0.0",
            author="Unknown",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            prompt_type=PromptType.SYSTEM,
            prompt_format=PromptFormat.TEXT,
            prompt_category=PromptCategory.GENERAL,
        )
        
    def save_prompt(self, prompt: Prompt, format: str = "json") -> str:
        """Save a prompt to a file.
        
        Args:
            prompt: Prompt to save
            format: Format to save in (json, yaml, txt)
            
        Returns:
            Path to the saved file
        """
        # Create directory for the prompt category
        category_dir = os.path.join(self.prompts_dir, prompt.metadata.prompt_category)
        os.makedirs(category_dir, exist_ok=True)
        
        # Determine file path
        if format == "json":
            file_path = os.path.join(category_dir, f"{prompt.metadata.id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(prompt.to_dict(), f, indent=2)
        elif format == "yaml":
            file_path = os.path.join(category_dir, f"{prompt.metadata.id}.yaml")
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(prompt.to_dict(), f, default_flow_style=False)
        elif format == "txt":
            file_path = os.path.join(category_dir, f"{prompt.metadata.id}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                # Write YAML frontmatter
                f.write("---\n")
                yaml.dump(prompt.metadata.to_dict(), f, default_flow_style=False)
                f.write("---\n\n")
                f.write(prompt.content)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        # Add to prompts dictionary
        self._prompts[prompt.metadata.id] = prompt
        
        if self.logger:
            self.logger.info(f"Saved prompt: {prompt.metadata.id}")
            
        return file_path
        
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by ID.
        
        Args:
            prompt_id: ID of the prompt
            
        Returns:
            The prompt, or None if not found
        """
        return self._prompts.get(prompt_id)
        
    def list_prompts(
        self,
        prompt_type: Optional[PromptType] = None,
        prompt_category: Optional[PromptCategory] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Prompt]:
        """List prompts.
        
        Args:
            prompt_type: Filter by prompt type
            prompt_category: Filter by prompt category
            tags: Filter by tags
            
        Returns:
            List of prompts
        """
        prompts = list(self._prompts.values())
        
        if prompt_type:
            prompts = [p for p in prompts if p.metadata.prompt_type == prompt_type]
            
        if prompt_category:
            prompts = [p for p in prompts if p.metadata.prompt_category == prompt_category]
            
        if tags:
            prompts = [p for p in prompts if all(tag in p.metadata.tags for tag in tags)]
            
        return prompts
        
    def create_prompt(
        self,
        content: str,
        name: str,
        description: str,
        prompt_type: PromptType = PromptType.SYSTEM,
        prompt_format: PromptFormat = PromptFormat.TEXT,
        prompt_category: PromptCategory = PromptCategory.GENERAL,
        tags: List[str] = None,
        variables: List[PromptVariable] = None,
    ) -> Prompt:
        """Create a new prompt.
        
        Args:
            content: Prompt content
            name: Prompt name
            description: Prompt description
            prompt_type: Prompt type
            prompt_format: Prompt format
            prompt_category: Prompt category
            tags: Prompt tags
            variables: Prompt variables
            
        Returns:
            The created prompt
        """
        # Generate ID from name
        prompt_id = name.lower().replace(" ", "_")
        
        # Create metadata
        metadata = PromptMetadata(
            id=prompt_id,
            name=name,
            description=description,
            version="1.0.0",
            author="Parlant",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            tags=tags or [],
            prompt_type=prompt_type,
            prompt_format=prompt_format,
            prompt_category=prompt_category,
        )
        
        # Extract variables if not provided
        if variables is None:
            variable_names = extract_variables_from_template(content)
            variables = [
                PromptVariable(
                    name=name,
                    description=f"Variable {name}",
                    required=True
                )
                for name in variable_names
            ]
            
        # Create prompt
        prompt = Prompt(
            metadata=metadata,
            content=content,
            variables=variables,
        )
        
        # Add to prompts dictionary
        self._prompts[prompt_id] = prompt
        
        return prompt
        
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt.
        
        Args:
            prompt_id: ID of the prompt
            
        Returns:
            True if the prompt was deleted, False otherwise
        """
        if prompt_id not in self._prompts:
            return False
            
        # Get the prompt
        prompt = self._prompts[prompt_id]
        
        # Delete files
        for ext in ["json", "yaml", "yml", "txt"]:
            file_path = os.path.join(
                self.prompts_dir, 
                prompt.metadata.prompt_category,
                f"{prompt_id}.{ext}"
            )
            if os.path.exists(file_path):
                os.remove(file_path)
                
        # Remove from prompts dictionary
        del self._prompts[prompt_id]
        
        if self.logger:
            self.logger.info(f"Deleted prompt: {prompt_id}")
            
        return True
        
    def update_prompt(self, prompt: Prompt) -> bool:
        """Update a prompt.
        
        Args:
            prompt: Updated prompt
            
        Returns:
            True if the prompt was updated, False otherwise
        """
        if prompt.metadata.id not in self._prompts:
            return False
            
        # Update the prompt
        self._prompts[prompt.metadata.id] = prompt
        
        # Update the updated_at timestamp
        prompt.metadata.updated_at = datetime.now().isoformat()
        
        # Save the prompt
        self.save_prompt(prompt)
        
        return True
