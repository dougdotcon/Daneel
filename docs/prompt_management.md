# Sistema de Gerenciamento de Prompts

Este documento descreve o sistema de gerenciamento de prompts no framework Daneel.

## Visão Geral

O sistema de gerenciamento de prompts fornece uma maneira de criar, gerenciar e usar prompts no Daneel. Ele suporta:

1. Carregamento e salvamento de prompts em vários formatos (JSON, YAML, texto)
2. Gerenciamento de metadados e variáveis de prompts
3. Renderização de prompts com substituição de variáveis
4. Templating avançado com Jinja2
5. Organização de prompts por categoria e tipo

## Componentes

### Prompt

A classe `Prompt` representa um prompt com metadados e conteúdo. Ela suporta:

- Substituição básica de variáveis com sintaxe `{variable_name}`
- Metadados para rastrear informações do prompt
- Variáveis com descrições e valores padrão

Exemplo de uso:

```python
from Daneel.core.prompts import Prompt, PromptMetadata, PromptVariable, PromptType

# Create a prompt
prompt = Prompt(
    metadata=PromptMetadata(
        id="greeting_prompt",
        name="Greeting Prompt",
        description="A prompt for greeting users",
        version="1.0.0",
        author="Daneel",
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
            default_value="Daneel",
            required=False
        )
    ]
)

# Render the prompt
rendered = prompt.render({"name": "John"})
print(rendered)  # Output: Hello, John! Welcome to Daneel.
```

### PromptManager

A classe `PromptManager` lida com o carregamento, salvamento e gerenciamento de prompts. Ela suporta:

- Carregamento de prompts de arquivos em vários formatos
- Salvamento de prompts em arquivos
- Criação, atualização e exclusão de prompts
- Listagem de prompts por tipo, categoria ou tags

Exemplo de uso:

```python
from Daneel.core.prompts import PromptManager, PromptType, PromptCategory
from Daneel.core.loggers import ConsoleLogger

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

A classe `PromptTemplate` fornece templating avançado usando Jinja2. Ela suporta:

- Lógica condicional com declarações `{% if %}`
- Loops com declarações `{% for %}`
- Filtros e funções
- Substituição de variáveis com sintaxe `{{ variable_name }}`

Exemplo de uso:

```python
from Daneel.core.prompts import Prompt, PromptMetadata, PromptTemplate
from Daneel.core.loggers import ConsoleLogger

# Create a prompt
prompt = Prompt(
    metadata=PromptMetadata(
        id="greeting_template",
        name="Greeting Template",
        description="A template for greeting users",
        version="1.0.0",
        author="Daneel",
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
    "service": "Daneel"
})
print(rendered)  # Output: Hello, John! Welcome to Daneel.
```

### PromptTemplateManager

A classe `PromptTemplateManager` gerencia templates de prompt. Ela suporta:

- Criação de templates a partir de prompts
- Obtenção de templates por ID
- Listagem de templates
- Renderização de templates com variáveis

Exemplo de uso:

```python
from Daneel.core.prompts import PromptTemplateManager
from parlat.core.loggers import ConsoleLogger

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
    "service": "Daneel"
})
```

## Organização de Prompts

Os prompts são organizados por categoria e tipo:

### Categorias

- `general`: Prompts de propósito geral
- `coding`: Prompts para tarefas de codificação
- `reasoning`: Prompts para tarefas de raciocínio
- `conversation`: Prompts para conversação
- `tool_use`: Prompts para uso de ferramentas
- `agent`: Prompts para agentes
- `custom`: Prompts personalizados

### Tipos

- `system`: Prompts do sistema
- `user`: Prompts do usuário
- `assistant`: Prompts do assistente
- `tool`: Prompts de ferramentas
- `template`: Prompts de template

## Formatos de Arquivo

Os prompts podem ser armazenados em vários formatos:

### JSON

```json
{
  "metadata": {
    "id": "greeting_prompt",
    "name": "Greeting Prompt",
    "description": "A prompt for greeting users",
    "version": "1.0.0",
    "author": "Daneel",
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
      "default_value": "Daneel",
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
  author: Daneel
  created_at: 2025-01-01T00:00:00Z
  updated_at: 2025-01-01T00:00:00Z
  prompt_type: system
  prompt_format: text
  prompt_category: general
content: "Hello, {name}! Welcome to {service}."
variables:
  - name: name
    description: User's name
    required: true
  - name: service
    description: Service name
    default_value: Daneel
    required: false
```

## Integração com Daneel

O sistema de gerenciamento de prompts está integrado com o framework Daneel:

1. **Modelos**: Os prompts são usados para guiar o comportamento dos modelos
2. **Agentes**: Os agentes usam prompts para suas interações
3. **Ferramentas**: As ferramentas podem ter prompts associados
4. **Conversas**: As conversas são estruturadas usando prompts

## Detalhes de Implementação

### Gerenciamento de Estado

O sistema gerencia:

- Carregamento e recarregamento de prompts
- Cache de prompts e templates
- Validação de variáveis
- Histórico de versões

### Segurança

O sistema inclui:

- Validação de entrada
- Escape de variáveis
- Controle de acesso
- Registro de uso

### Desempenho

O sistema otimiza:

- Cache de templates
- Compilação de templates
- Carregamento sob demanda
- Reutilização de prompts

## Melhorias Futuras

Possíveis melhorias futuras para o sistema de gerenciamento de prompts:

1. **Versionamento**: Melhor controle de versão de prompts
2. **Validação**: Validação mais avançada de prompts
3. **Personalização**: Mais opções de personalização
4. **Internacionalização**: Suporte para múltiplos idiomas
5. **Análise**: Ferramentas para análise de uso de prompts
