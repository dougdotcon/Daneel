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

"""Tests for the prompt management system."""

import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock
from datetime import datetime

from parlant.core.prompts.common import (
    Prompt, PromptMetadata, PromptVariable, 
    PromptType, PromptFormat, PromptCategory,
    extract_variables_from_template
)
from parlant.core.prompts.prompt_manager import PromptManager
from parlant.core.prompts.prompt_template import PromptTemplate, PromptTemplateManager


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    return logger


@pytest.fixture
def temp_prompts_dir():
    """Create a temporary directory for prompts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_extract_variables_from_template():
    """Test extracting variables from a template."""
    template = "Hello, {name}! Welcome to {service}."
    variables = extract_variables_from_template(template)
    assert set(variables) == {"name", "service"}


def test_prompt_metadata():
    """Test prompt metadata."""
    metadata = PromptMetadata(
        id="test_prompt",
        name="Test Prompt",
        description="A test prompt",
        version="1.0.0",
        author="Test Author",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
        tags=["test", "prompt"],
        source="Test Source",
        license="MIT",
        model_compatibility=["gpt-4", "claude-3"],
        prompt_type=PromptType.SYSTEM,
        prompt_format=PromptFormat.TEXT,
        prompt_category=PromptCategory.GENERAL,
    )
    
    # Test to_dict
    metadata_dict = metadata.to_dict()
    assert metadata_dict["id"] == "test_prompt"
    assert metadata_dict["name"] == "Test Prompt"
    assert metadata_dict["tags"] == ["test", "prompt"]
    
    # Test from_dict
    metadata2 = PromptMetadata.from_dict(metadata_dict)
    assert metadata2.id == metadata.id
    assert metadata2.name == metadata.name
    assert metadata2.tags == metadata.tags


def test_prompt_variable():
    """Test prompt variable."""
    variable = PromptVariable(
        name="test_var",
        description="A test variable",
        default_value="default",
        required=True,
    )
    
    # Test to_dict
    variable_dict = variable.to_dict()
    assert variable_dict["name"] == "test_var"
    assert variable_dict["description"] == "A test variable"
    assert variable_dict["default_value"] == "default"
    assert variable_dict["required"] is True
    
    # Test from_dict
    variable2 = PromptVariable.from_dict(variable_dict)
    assert variable2.name == variable.name
    assert variable2.description == variable.description
    assert variable2.default_value == variable.default_value
    assert variable2.required == variable.required


def test_prompt():
    """Test prompt."""
    metadata = PromptMetadata(
        id="test_prompt",
        name="Test Prompt",
        description="A test prompt",
        version="1.0.0",
        author="Test Author",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    
    variables = [
        PromptVariable(
            name="name",
            description="User's name",
            required=True,
        ),
        PromptVariable(
            name="service",
            description="Service name",
            default_value="Parlant",
            required=False,
        ),
    ]
    
    prompt = Prompt(
        metadata=metadata,
        content="Hello, {name}! Welcome to {service}.",
        variables=variables,
    )
    
    # Test to_dict
    prompt_dict = prompt.to_dict()
    assert prompt_dict["metadata"]["id"] == "test_prompt"
    assert prompt_dict["content"] == "Hello, {name}! Welcome to {service}."
    assert len(prompt_dict["variables"]) == 2
    
    # Test from_dict
    prompt2 = Prompt.from_dict(prompt_dict)
    assert prompt2.metadata.id == prompt.metadata.id
    assert prompt2.content == prompt.content
    assert len(prompt2.variables) == len(prompt.variables)
    
    # Test render
    rendered = prompt.render({"name": "John"})
    assert rendered == "Hello, John! Welcome to Parlant."
    
    # Test render with all variables
    rendered = prompt.render({"name": "John", "service": "TestService"})
    assert rendered == "Hello, John! Welcome to TestService."
    
    # Test render with missing required variable
    with pytest.raises(ValueError):
        prompt.render({})


def test_prompt_manager(temp_prompts_dir, mock_logger):
    """Test prompt manager."""
    manager = PromptManager(prompts_dir=temp_prompts_dir, logger=mock_logger)
    
    # Test creating a prompt
    prompt = manager.create_prompt(
        content="Hello, {name}! Welcome to {service}.",
        name="Test Prompt",
        description="A test prompt",
        prompt_type=PromptType.SYSTEM,
        prompt_format=PromptFormat.TEXT,
        prompt_category=PromptCategory.GENERAL,
        tags=["test", "prompt"],
    )
    
    assert prompt.metadata.id == "test_prompt"
    assert prompt.content == "Hello, {name}! Welcome to {service}."
    assert len(prompt.variables) == 2
    
    # Test saving a prompt
    file_path = manager.save_prompt(prompt, format="json")
    assert os.path.exists(file_path)
    
    # Test loading prompts
    manager = PromptManager(prompts_dir=temp_prompts_dir, logger=mock_logger)
    manager.load_prompts()
    
    # Test getting a prompt
    prompt2 = manager.get_prompt("test_prompt")
    assert prompt2 is not None
    assert prompt2.metadata.id == "test_prompt"
    
    # Test listing prompts
    prompts = manager.list_prompts()
    assert len(prompts) == 1
    assert prompts[0].metadata.id == "test_prompt"
    
    # Test updating a prompt
    prompt.content = "Updated content: {name}, {service}"
    manager.update_prompt(prompt)
    
    # Test getting the updated prompt
    prompt3 = manager.get_prompt("test_prompt")
    assert prompt3 is not None
    assert prompt3.content == "Updated content: {name}, {service}"
    
    # Test deleting a prompt
    result = manager.delete_prompt("test_prompt")
    assert result is True
    
    # Test getting a deleted prompt
    prompt4 = manager.get_prompt("test_prompt")
    assert prompt4 is None


def test_prompt_template(mock_logger):
    """Test prompt template."""
    metadata = PromptMetadata(
        id="test_template",
        name="Test Template",
        description="A test template",
        version="1.0.0",
        author="Test Author",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    
    prompt = Prompt(
        metadata=metadata,
        content="Hello, {{ name }}! {% if show_service %}Welcome to {{ service }}.{% endif %}",
        variables=[],
    )
    
    template = PromptTemplate(prompt, mock_logger)
    
    # Test get_required_variables
    required_vars = template.get_required_variables()
    assert "name" in required_vars
    assert "show_service" in required_vars
    assert "service" in required_vars
    
    # Test render
    rendered = template.render({
        "name": "John",
        "show_service": True,
        "service": "Parlant"
    })
    assert rendered == "Hello, John! Welcome to Parlant."
    
    # Test render with show_service=False
    rendered = template.render({
        "name": "John",
        "show_service": False,
        "service": "Parlant"
    })
    assert rendered == "Hello, John! "
    
    # Test render with missing required variable
    with pytest.raises(ValueError):
        template.render({"name": "John"})


def test_prompt_template_manager(mock_logger):
    """Test prompt template manager."""
    manager = PromptTemplateManager(logger=mock_logger)
    
    # Create a prompt
    metadata = PromptMetadata(
        id="test_template",
        name="Test Template",
        description="A test template",
        version="1.0.0",
        author="Test Author",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    
    prompt = Prompt(
        metadata=metadata,
        content="Hello, {{ name }}! {% if show_service %}Welcome to {{ service }}.{% endif %}",
        variables=[],
    )
    
    # Test creating a template
    template = manager.create_template(prompt)
    assert template is not None
    
    # Test getting a template
    template2 = manager.get_template("test_template")
    assert template2 is not None
    
    # Test listing templates
    templates = manager.list_templates()
    assert len(templates) == 1
    assert templates[0].prompt.metadata.id == "test_template"
    
    # Test rendering a template
    rendered = manager.render_template("test_template", {
        "name": "John",
        "show_service": True,
        "service": "Parlant"
    })
    assert rendered == "Hello, John! Welcome to Parlant."
    
    # Test deleting a template
    result = manager.delete_template("test_template")
    assert result is True
    
    # Test getting a deleted template
    template3 = manager.get_template("test_template")
    assert template3 is None
