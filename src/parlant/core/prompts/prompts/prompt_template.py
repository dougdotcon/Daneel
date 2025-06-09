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

"""Prompt templating system for Daneel."""

import re
import json
from typing import Any, Dict, List, Optional, Set, Union
from jinja2 import Environment, Template, meta, StrictUndefined

from Daneel.core.loggers import Logger
from Daneel.core.prompts.common import (
    Prompt, PromptMetadata, PromptVariable, 
    PromptType, PromptFormat, PromptCategory
)


class PromptTemplate:
    """Template for generating prompts.
    
    This class provides a more powerful templating system than the basic
    variable substitution in the Prompt class. It uses Jinja2 for templating.
    """
    
    def __init__(
        self,
        prompt: Prompt,
        logger: Logger = None,
    ):
        """Initialize the prompt template.
        
        Args:
            prompt: Prompt to use as a template
            logger: Logger instance
        """
        self.prompt = prompt
        self.logger = logger
        self._env = Environment(undefined=StrictUndefined)
        self._template = self._env.from_string(prompt.content)
        
        # Extract variables from the template
        self._extract_variables()
        
    def _extract_variables(self) -> None:
        """Extract variables from the template."""
        # Get variables from the template
        ast = self._env.parse(self.prompt.content)
        variables = meta.find_undeclared_variables(ast)
        
        # Update the prompt variables
        existing_vars = {v.name: v for v in self.prompt.variables}
        
        for var_name in variables:
            if var_name not in existing_vars:
                self.prompt.variables.append(
                    PromptVariable(
                        name=var_name,
                        description=f"Variable {var_name}",
                        required=True
                    )
                )
                
    def render(self, variables: Dict[str, Any] = None) -> str:
        """Render the template with variables.
        
        Args:
            variables: Dictionary of variable values
            
        Returns:
            Rendered template
            
        Raises:
            ValueError: If a required variable is missing
        """
        variables = variables or {}
        
        # Check for missing required variables
        missing_vars = []
        for var in self.prompt.variables:
            if var.required and var.name not in variables and var.default_value is None:
                missing_vars.append(var.name)
                
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
            
        # Add default values for missing variables
        for var in self.prompt.variables:
            if var.name not in variables and var.default_value is not None:
                variables[var.name] = var.default_value
                
        # Render the template
        try:
            return self._template.render(**variables)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to render template: {e}")
            raise
            
    def get_required_variables(self) -> List[str]:
        """Get the names of required variables.
        
        Returns:
            List of required variable names
        """
        return [v.name for v in self.prompt.variables if v.required]
        
    def get_all_variables(self) -> List[str]:
        """Get the names of all variables.
        
        Returns:
            List of all variable names
        """
        return [v.name for v in self.prompt.variables]


class PromptTemplateManager:
    """Manager for prompt templates.
    
    This class provides a way to create and manage prompt templates.
    """
    
    def __init__(
        self,
        logger: Logger = None,
    ):
        """Initialize the prompt template manager.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self._templates: Dict[str, PromptTemplate] = {}
        
    def create_template(self, prompt: Prompt) -> PromptTemplate:
        """Create a template from a prompt.
        
        Args:
            prompt: Prompt to use as a template
            
        Returns:
            The created template
        """
        template = PromptTemplate(prompt, self.logger)
        self._templates[prompt.metadata.id] = template
        return template
        
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID.
        
        Args:
            template_id: ID of the template
            
        Returns:
            The template, or None if not found
        """
        return self._templates.get(template_id)
        
    def list_templates(self) -> List[PromptTemplate]:
        """List all templates.
        
        Returns:
            List of templates
        """
        return list(self._templates.values())
        
    def render_template(self, template_id: str, variables: Dict[str, Any] = None) -> str:
        """Render a template with variables.
        
        Args:
            template_id: ID of the template
            variables: Dictionary of variable values
            
        Returns:
            Rendered template
            
        Raises:
            ValueError: If the template is not found or a required variable is missing
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
            
        return template.render(variables)
        
    def delete_template(self, template_id: str) -> bool:
        """Delete a template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            True if the template was deleted, False otherwise
        """
        if template_id not in self._templates:
            return False
            
        del self._templates[template_id]
        return True
