# Prompt Management System

This document describes the prompt management system in the Parlant framework.

## Overview

The prompt management system provides a way to create, manage, and use prompts in Parlant. It supports:

1. Loading and saving prompts in various formats (JSON, YAML, text)
2. Managing prompt metadata and variables
3. Rendering prompts with variable substitution
4. Advanced templating with Jinja2
5. Organizing prompts by category and type

## Components

### Prompt

The `Prompt` class represents a prompt with metadata and content. It supports:

- Basic variable substitution with `{variable_name}` syntax
- Metadata for tracking prompt information
- Variables with descriptions and default values

Example usage:

```python
from parlant.core.prompts import Prompt, PromptMetadata, PromptVariable, PromptType

# Create a prompt
prompt = Prompt(
    metadata=PromptMetadata(
        id="greeting_prompt",
        name="Greeting Prompt",
        description="A prompt for greeting users",
        version="1.0.0",
        author="Parlant",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
        prompt_type=PromptType.SYSTEM
    ),
    content="Hello, {name}! Welcome to {service}.",
    variables=[
        PromptVariable(
            name="name",
            description="User's name",
            required=True
        ),
        PromptVariable(
            name="service",
            description="Service name",
            default_value="Parlant",
            required=False
        )
    ]
)

# Render the prompt
rendered = prompt.render({"name": "John"})
print(rendered)  # Output: Hello, John! Welcome to Parlant.
```

### PromptManager

The `PromptManager` class handles loading, saving, and managing prompts. It supports:

- Loading prompts from files in various formats
- Saving prompts to files
- Creating, updating, and deleting prompts
- Listing prompts by type, category, or tags

Example usage:

```python
from parlant.core.prompts import PromptManager, PromptType, PromptCategory
from parlant.core.loggers import ConsoleLogger

# Create a prompt manager
manager = PromptManager(logger=ConsoleLogger())

# Load prompts from files
manager.load_prompts()

# Create a new prompt
prompt = manager.create_prompt(
    content="Hello, {name}! Welcome to {service}.",
    name="Greeting Prompt",
    description="A prompt for greeting users",
    prompt_type=PromptType.SYSTEM,
    prompt_category=PromptCategory.GENERAL,
    tags=["greeting", "welcome"]
)

# Save the prompt
manager.save_prompt(prompt, format="json")

# Get a prompt by ID
prompt = manager.get_prompt("greeting_prompt")

# List prompts by category
prompts = manager.list_prompts(prompt_category=PromptCategory.GENERAL)

# Delete a prompt
manager.delete_prompt("greeting_prompt")
```

### PromptTemplate

The `PromptTemplate` class provides advanced templating using Jinja2. It supports:

- Conditional logic with `{% if %}` statements
- Loops with `{% for %}` statements
- Filters and functions
- Variable substitution with `{{ variable_name }}` syntax

Example usage:

```python
from parlant.core.prompts import Prompt, PromptMetadata, PromptTemplate
from parlant.core.loggers import ConsoleLogger

# Create a prompt
prompt = Prompt(
    metadata=PromptMetadata(
        id="greeting_template",
        name="Greeting Template",
        description="A template for greeting users",
        version="1.0.0",
        author="Parlant",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z"
    ),
    content="Hello, {{ name }}! {% if show_service %}Welcome to {{ service }}.{% endif %}"
)

# Create a template
template = PromptTemplate(prompt, logger=ConsoleLogger())

# Render the template
rendered = template.render({
    "name": "John",
    "show_service": True,
    "service": "Parlant"
})
print(rendered)  # Output: Hello, John! Welcome to Parlant.
```

### PromptTemplateManager

The `PromptTemplateManager` class manages prompt templates. It supports:

- Creating templates from prompts
- Getting templates by ID
- Listing templates
- Rendering templates with variables

Example usage:

```python
from parlant.core.prompts import PromptTemplateManager
from parlant.core.loggers import ConsoleLogger

# Create a template manager
manager = PromptTemplateManager(logger=ConsoleLogger())

# Create a template from a prompt
template = manager.create_template(prompt)

# Get a template by ID
template = manager.get_template("greeting_template")

# List templates
templates = manager.list_templates()

# Render a template
rendered = manager.render_template("greeting_template", {
    "name": "John",
    "show_service": True,
    "service": "Parlant"
})
```

## Prompt Organization

Prompts are organized by category and type:

### Categories

- `general`: General-purpose prompts
- `coding`: Prompts for coding tasks
- `reasoning`: Prompts for reasoning tasks
- `conversation`: Prompts for conversation
- `tool_use`: Prompts for tool use
- `agent`: Prompts for agents
- `custom`: Custom prompts

### Types

- `system`: System prompts
- `user`: User prompts
- `assistant`: Assistant prompts
- `tool`: Tool prompts
- `template`: Template prompts

## File Formats

Prompts can be stored in various formats:

### JSON

```json
{
  "metadata": {
    "id": "greeting_prompt",
    "name": "Greeting Prompt",
    "description": "A prompt for greeting users",
    "version": "1.0.0",
    "author": "Parlant",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "prompt_type": "system",
    "prompt_format": "text",
    "prompt_category": "general"
  },
  "content": "Hello, {name}! Welcome to {service}.",
  "variables": [
    {
      "name": "name",
      "description": "User's name",
      "required": true
    },
    {
      "name": "service",
      "description": "Service name",
      "default_value": "Parlant",
      "required": false
    }
  ]
}
```

### YAML

```yaml
metadata:
  id: greeting_prompt
  name: Greeting Prompt
  description: A prompt for greeting users
  version: 1.0.0
  author: Parlant
  created_at: '2025-01-01T00:00:00Z'
  updated_at: '2025-01-01T00:00:00Z'
  prompt_type: system
  prompt_format: text
  prompt_category: general
content: 'Hello, {name}! Welcome to {service}.'
variables:
- name: name
  description: User's name
  required: true
- name: service
  description: Service name
  default_value: Parlant
  required: false
```

### Text with YAML Frontmatter

```
---
id: greeting_prompt
name: Greeting Prompt
description: A prompt for greeting users
version: 1.0.0
author: Parlant
created_at: '2025-01-01T00:00:00Z'
updated_at: '2025-01-01T00:00:00Z'
prompt_type: system
prompt_format: text
prompt_category: general
---

Hello, {name}! Welcome to {service}.
```

## Integration with Parlant

The prompt management system is integrated with the Parlant framework:

1. **Core Engine**: The core engine uses prompts for generating responses
2. **Agents**: Agents use prompts for their behavior
3. **Tools**: Tools use prompts for their instructions
4. **Adapters**: Adapters use prompts for connecting to external systems

## Future Enhancements

Future enhancements to the prompt management system may include:

1. **Prompt Versioning**: Track changes to prompts over time
2. **Prompt Testing**: Test prompts with different variables
3. **Prompt Optimization**: Optimize prompts for different models
4. **Prompt Sharing**: Share prompts between Parlant instances
5. **Prompt Marketplace**: Discover and use prompts from a marketplace
