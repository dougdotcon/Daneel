# Sistema de Integração de Ferramentas

Este documento descreve o sistema de integração de ferramentas no framework Daneel.

## Visão Geral

O sistema de integração de ferramentas fornece uma maneira de criar, gerenciar e usar ferramentas no Daneel. Ele suporta:

1. Registro e descoberta de ferramentas
2. Categorização de ferramentas por funcionalidade
3. Chamada de ferramentas com argumentos
4. Tratamento de resultados de ferramentas
5. Gerenciamento de metadados de ferramentas

## Componentes

### ToolRegistry

A classe `ToolRegistry` é o componente central do sistema de integração de ferramentas. Ela gerencia o registro, descoberta e acesso de ferramentas. Ela fornece métodos para:

- Registro de ferramentas
- Obtenção de ferramentas por ID
- Listagem de ferramentas por categoria ou tags
- Chamada de ferramentas com argumentos
- Gerenciamento de metadados de ferramentas

Exemplo de uso:

```python
from Daneel.core.loggers import ConsoleLogger
from Daneel.core.tools import LocalToolService, ToolRegistry
from Daneel.core.tools.tool_registry import ToolCategory

# Create a tool registry
tool_service = LocalToolService()
registry = ToolRegistry(
    logger=ConsoleLogger(),
    tool_service=tool_service,
)

# Register a tool
tool = await registry.register_tool(
    tool_id="my_tool",
    module_path="my_module",
    name="My Tool",
    description="A custom tool",
    parameters={
        "param1": {
            "type": "string",
            "description": "Parameter 1",
        },
    },
    required=["param1"],
    category=ToolCategory.CUSTOM,
    tags=["custom", "example"],
)

# Get a tool
tool = await registry.get_tool("my_tool")

# List tools by category
tools = await registry.list_tools(category=ToolCategory.CUSTOM)

# Call a tool
result = await registry.call_tool(
    tool_id="my_tool",
    context=tool_context,
    arguments={"param1": "value1"},
)
```

### Decorador Tool

O decorador `tool` fornece uma maneira conveniente de definir ferramentas como funções Python. Ele lida automaticamente com a conversão de parâmetros de função para parâmetros de ferramenta e o registro da ferramenta no registro.

Exemplo de uso:

```python
from Daneel.core.tools import ToolResult
from Daneel.core.tools.tool_registry import ToolCategory, tool

@tool(
    id="my_tool",
    name="My Tool",
    description="A custom tool",
    parameters={
        "param1": {
            "type": "string",
            "description": "Parameter 1",
        },
        "param2": {
            "type": "integer",
            "description": "Parameter 2",
        },
    },
    required=["param1"],
    category=ToolCategory.CUSTOM,
    tags=["custom", "example"],
)
def my_tool(param1, param2=None):
    # Tool implementation
    return ToolResult(
        data={
            "result": "success",
            "param1": param1,
            "param2": param2,
        }
    )
```

### Categorias de Ferramentas

As ferramentas são organizadas em categorias baseadas em sua funcionalidade:

- `CODE`: Ferramentas para trabalhar com código (busca, edição, execução)
- `WEB`: Ferramentas para trabalhar com a web (busca, download)
- `FILESYSTEM`: Ferramentas para trabalhar com o sistema de arquivos (listar, criar, excluir)
- `UTILS`: Ferramentas utilitárias (tempo, aleatório, UUID)
- `CUSTOM`: Ferramentas personalizadas definidas pelo usuário

### Metadados de Ferramentas

Cada ferramenta tem metadados associados que descrevem seu propósito, parâmetros e outros atributos:

- `id`: Identificador único para a ferramenta
- `name`: Nome de exibição para a ferramenta
- `description`: Descrição do que a ferramenta faz
- `category`: Categoria da ferramenta
- `version`: Versão da ferramenta
- `author`: Autor da ferramenta
- `tags`: Tags para categorizar a ferramenta
- `documentation_url`: URL para a documentação da ferramenta

## Ferramentas Disponíveis

### Ferramentas de Código

#### Ferramentas de Busca

- `code_search`: Buscar código no workspace usando uma string de consulta
- `code_semantic_search`: Buscar código semanticamente usando linguagem natural
- `find_definition`: Encontrar a definição de um símbolo no código-fonte

#### Ferramentas de Edição

- `read_file`: Ler o conteúdo de um arquivo
- `write_file`: Escrever conteúdo em um arquivo
- `edit_file`: Editar uma parte específica de um arquivo
- `create_file`: Criar um novo arquivo com o conteúdo especificado
- `delete_file`: Excluir um arquivo

#### Ferramentas de Execução

- `execute_python`: Executar código Python e retornar o resultado
- `execute_shell`: Executar um comando shell e retornar o resultado
- `run_tests`: Executar testes para um projeto
- `execute_code_snippet`: Executar um trecho de código em uma linguagem específica

### Ferramentas Web

- `web_search`: Pesquisar informações na web
- `fetch_webpage`: Buscar o conteúdo de uma página web
- `search_wikipedia`: Pesquisar informações na Wikipedia

### Ferramentas de Sistema de Arquivos

- `list_directory`: Listar arquivos e diretórios em um diretório
- `create_directory`: Criar um novo diretório
- `delete_directory`: Excluir um diretório
- `copy_file`: Copiar um arquivo da origem para o destino
- `move_file`: Mover um arquivo da origem para o destino

### Ferramentas Utilitárias

- `get_current_time`: Obter a data e hora atual
- `generate_random_string`: Gerar uma string aleatória
- `generate_uuid`: Gerar um UUID
- `get_system_info`: Obter informações sobre o sistema
- `parse_json`: Analisar uma string JSON
- `format_json`: Formatar uma string JSON

## Integração com Daneel

O sistema de integração de ferramentas está integrado com o framework Daneel:

1. **Motor Principal**: O motor principal usa ferramentas para executar ações
2. **Agentes**: Os agentes usam ferramentas para interagir com o ambiente
3. **Sistema de Prompts**: O sistema de prompts inclui descrições e exemplos de ferramentas
4. **MCP**: O MCP usa ferramentas para executar ações

## Melhorias Futuras

Possíveis melhorias futuras para o sistema de integração de ferramentas:

1. **Versionamento de Ferramentas**: Rastrear mudanças nas ferramentas ao longo do tempo
2. **Teste de Ferramentas**: Testar ferramentas com diferentes argumentos
3. **Otimização de Ferramentas**: Otimizar ferramentas para diferentes ambientes
4. **Compartilhamento de Ferramentas**: Compartilhar ferramentas entre instâncias do Daneel
5. **Marketplace de Ferramentas**: Descobrir e usar ferramentas de um marketplace
