# Integração MCP (Protocolo de Contexto do Modelo)

Este documento descreve a integração do Protocolo de Contexto do Modelo (MCP) no framework Parlant.

## Visão Geral

O Protocolo de Contexto do Modelo (MCP) é um protocolo padronizado para comunicação entre IDEs e agentes de IA. Ele permite o compartilhamento de contexto e uso de ferramentas, permitindo que agentes de IA realizem tarefas complexas aproveitando ferramentas e serviços externos.

O Parlant agora inclui uma implementação completa do MCP, permitindo:

1. Conectar-se a servidores MCP externos para usar suas ferramentas e capacidades
2. Expor suas próprias capacidades como um servidor MCP para uso por outras aplicações
3. Implementar servidores MCP especializados como o Pensamento Sequencial para melhor raciocínio

## Componentes

### MCPClient

A classe `MCPClient` permite que o Parlant se conecte a servidores MCP externos e use suas ferramentas. Ela lida com:

- Gerenciamento de conexão WebSocket
- Descoberta e registro de ferramentas
- Envio e recebimento de mensagens
- Execução de chamadas de ferramentas

Exemplo de uso:

```python
from parlant.adapters.mcp import MCPClient
from parlant.core.loggers import ConsoleLogger

# Create a client
client = MCPClient(
    server_url="ws://localhost:8080",
    logger=ConsoleLogger()
)

# Connect to the server
await client.connect()

# Send a message
message = MCPMessage.user("Hello!")
response = await client.send_message(message)

# Disconnect
await client.disconnect()
```

### MCPServer

A classe `MCPServer` permite que o Parlant exponha suas capacidades como um servidor MCP. Ela lida com:

- Gerenciamento de servidor WebSocket
- Registro e descoberta de ferramentas
- Manipulação de mensagens
- Execução de chamadas de ferramentas

Exemplo de uso:

```python
from parlant.adapters.mcp import MCPServer, MCPTool
from parlant.core.loggers import ConsoleLogger

# Create a server
server = MCPServer(
    host="localhost",
    port=8080,
    logger=ConsoleLogger()
)

# Register a tool
server.register_tool(
    MCPTool(
        name="echo",
        description="Echo the input",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to echo"
                }
            },
            "required": ["text"]
        },
        required_parameters=["text"]
    ),
    lambda args: {"echo": args["text"]}
)

# Set a message handler
server.set_message_handler(async_message_handler)

# Start the server
await server.start()
```

### SequentialThinkingMCP

A classe `SequentialThinkingMCP` implementa um servidor MCP especializado para pensamento sequencial. Ela permite que os modelos:

- Gerem uma sequência de pensamentos
- Revisem e refinem esses pensamentos
- Ramifiquem hipóteses
- Tomem decisões baseadas em raciocínio estruturado

Exemplo de uso:

```python
from parlant.adapters.mcp import SequentialThinkingMCP
from parlant.core.loggers import ConsoleLogger
from parlant.adapters.nlp import OpenAIService

# Create a sequential thinking MCP
sequential_thinking = SequentialThinkingMCP(
    nlp_service=OpenAIService(...),
    logger=ConsoleLogger(),
    host="localhost",
    port=8081
)

# Start the server
await sequential_thinking.start()
```

## Integração com Parlant

A integração MCP foi projetada para funcionar perfeitamente com a arquitetura existente do Parlant:

1. **Camada de Adaptadores**: A implementação MCP reside na camada de adaptadores, permitindo que seja usada pelos componentes principais.
2. **Integração de Ferramentas**: Ferramentas MCP podem ser registradas e usadas pelo sistema de ferramentas do Parlant.
3. **Serviços NLP**: O MCP pode ser usado com qualquer um dos serviços NLP do Parlant.
4. **Gerenciamento de Sessão**: Sessões MCP podem ser integradas com o gerenciamento de sessão do Parlant.

## Melhorias Futuras

Melhorias futuras para a integração MCP podem incluir:

1. **Encadeamento de Ferramentas**: Permitir que ferramentas sejam encadeadas para fluxos de trabalho complexos.
2. **Versionamento de Ferramentas**: Suporte para ferramentas versionadas e compatibilidade retroativa.
3. **Autenticação**: Adicionar autenticação e autorização para conexões MCP.
4. **Streaming**: Suporte para respostas em streaming de ferramentas.
5. **Suporte Multimodal**: Adicionar suporte para entradas e saídas multimodais.

## Referências

- [Especificação do Protocolo de Contexto do Modelo](https://github.com/modelcontextprotocol/servers)
- [MCP de Pensamento Sequencial](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)
- [Modo Agente do VSCode com MCP](https://code.visualstudio.com/blogs/2025/04/07/agentMode)
