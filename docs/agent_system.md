# Sistema de Agentes

Este documento descreve o sistema de agentes no framework Parlant.

## Visão Geral

O sistema de agentes fornece uma maneira de criar, gerenciar e usar agentes no Parlant. Ele suporta:

1. Diferentes tipos de agentes (CLI, terminal, web)
2. Configuração e contexto de agentes
3. Gerenciamento de estado de agentes
4. Execução segura de código através de sandboxing
5. Manipulação e formatação de mensagens

## Componentes

### AgentSystem

A classe `AgentSystem` é a classe base para todas as implementações de agentes. Ela fornece funcionalidade comum para:

- Inicialização de agentes
- Execução de agentes com instruções
- Gerenciamento de estado de agentes (em execução, pausado, parado)
- Tratamento de interrupções
- Limpeza de recursos

Exemplo de uso:

```python
from parlant.core.agents import AgentConfig, AgentType
from parlant.core.agents.cli import CLIAgent
from semblant.core.loggers import ConsoleLogger

# Create an agent configuration
config = AgentConfig(
    agent_type=AgentType.CLI,
    name="My CLI Agent",
    description="A CLI agent for coding tasks",
    model_id="gpt-4",
    tools=["code_search", "read_file", "write_file"],
    prompts=["cli_agent_prompt"],
)

# Create a CLI agent
agent = CLIAgent(
    agent_id="agent1",
    config=config,
    logger=ConsoleLogger(),
    model_manager=model_manager,
    prompt_manager=prompt_manager,
    tool_registry=tool_registry,
    agent_store=agent_store,
)

# Initialize the agent
await agent.initialize()

# Run the agent with an instruction
result = await agent.run("Find all functions in the codebase that handle user authentication")

# Stop the agent
await agent.stop()

# Clean up resources
await agent.cleanup()
```

### AgentSystemFactory

A classe `AgentSystemFactory` fornece uma maneira de criar agentes de diferentes tipos. Ela suporta:

- Registro de tipos de sistema de agentes
- Criação de agentes com configurações
- Gerenciamento de dependências de agentes

Exemplo de uso:

```python
from parlat.core.agents import AgentConfig, AgentSystemFactory, AgentType
from parlat.core.agents.cli import CLIAgent
from parlat.core.agents.terminal import TerminalAgent
from parlat.core.loggers import ConsoleLogger

# Create a factory
factory = AgentSystemFactory(
    logger=ConsoleLogger(),
    model_manager=model_manager,
    prompt_manager=prompt_manager,
    tool_registry=tool_registry,
    agent_store=agent_store,
)

# Register agent system types
factory.register_agent_system_type(AgentType.CLI, CLIAgent)
factory.register_agent_system_type(AgentType.TERMINAL, TerminalAgent)

# Create a CLI agent
cli_config = AgentConfig(
    agent_type=AgentType.CLI,
    name="My CLI Agent",
    description="A CLI agent for coding tasks",
    model_id="gpt-4",
)
cli_agent = await factory.create_agent_system("agent1", cli_config)

# Create a terminal agent
terminal_config = AgentConfig(
    agent_type=AgentType.TERMINAL,
    name="My Terminal Agent",
    description="A terminal agent for shell tasks",
    model_id="gpt-4",
)
terminal_agent = await factory.create_agent_system("agent2", terminal_config)
```

### CLIAgent

A classe `CLIAgent` implementa um agente de interface de linha de comando. Ela suporta:

- Processamento de instruções do usuário
- Chamada de ferramentas para executar ações
- Geração de respostas
- Gerenciamento de histórico de conversas

Exemplo de uso:

```python
from parlat.core.agents import AgentConfig, AgentType
from parlat.core.agents.cli import CLIAgent
from parlat.core.loggers import ConsoleLogger

# Create a CLI agent
agent = CLIAgent(
    agent_id="agent1",
    config=AgentConfig(
        agent_type=AgentType.CLI,
        name="My CLI Agent",
        description="A CLI agent for coding tasks",
        model_id="gpt-4",
    ),
    logger=ConsoleLogger(),
    model_manager=model_manager,
    prompt_manager=prompt_manager,
    tool_registry=tool_registry,
    agent_store=agent_store,
)

# Initialize the agent
await agent.initialize()

# Run the agent with an instruction
result = await agent.run("Find all functions in the codebase that handle user authentication")
print(result)
```

### TerminalAgent

A classe `TerminalAgent` implementa um agente baseado em terminal. Ela suporta:

- Interação com uma sessão de terminal
- Execução de comandos no terminal
- Leitura de saída do terminal
- Gerenciamento de estado do terminal

Exemplo de uso:

```python
from parlat.core.agents import AgentConfig, AgentType
from parlat.core.agents.terminal import TerminalAgent
from parlat.core.loggers import ConsoleLogger

# Create a terminal agent
agent = TerminalAgent(
    agent_id="agent1",
    config=AgentConfig(
        agent_type=AgentType.TERMINAL,
        name="My Terminal Agent",
        description="A terminal agent for shell tasks",
        model_id="gpt-4",
    ),
    logger=ConsoleLogger(),
    model_manager=model_manager,
    prompt_manager=prompt_manager,
    tool_registry=tool_registry,
    agent_store=agent_store,
)

# Initialize the agent
await agent.initialize()

# Run the agent with an instruction
result = await agent.run("List all files in the current directory and find the largest one")
print(result)
```

### Sandbox

A classe `Sandbox` fornece um ambiente seguro para execução de código. Ela suporta:

- Sandboxes locais e baseadas em Docker
- Execução de comandos
- Execução de arquivos
- Limpeza de recursos

Exemplo de uso:

```python
from parlat.core.agents.sandbox import SandboxConfig, SandboxFactory
from parlat.core.loggers import ConsoleLogger

# Create a sandbox factory
factory = SandboxFactory(logger=ConsoleLogger())

# Create a sandbox configuration
config = SandboxConfig(
    workspace_dir="/path/to/workspace",
    allowed_commands=["echo", "ls", "cat"],
    blocked_commands=["rm", "mv", "cp"],
    timeout_seconds=5,
    max_output_size=1000,
)

# Create a local sandbox
sandbox = await factory.create_sandbox(config, "local")

# Execute a command
exit_code, stdout, stderr = await sandbox.execute_command("echo 'Hello, world!'")
print(f"Exit code: {exit_code}")
print(f"Output: {stdout}")
print(f"Error: {stderr}")

# Execute a file
exit_code, stdout, stderr = await sandbox.execute_file("script.py")
print(f"Exit code: {exit_code}")
print(f"Output: {stdout}")
print(f"Error: {stderr}")

# Clean up the sandbox
await sandbox.cleanup()
```

### MessageHandler

A classe `MessageHandler` fornece utilitários para manipulação de mensagens em sistemas de agentes. Ela suporta:

- Análise de mensagens
- Formatação de mensagens
- Extração de blocos de código
- Extração de chamadas de ferramentas
- Extração de comandos

## Integração com Parlant

O sistema de agentes está integrado com o framework Parlant:

1. **Modelos**: Os agentes usam modelos para gerar respostas
2. **Ferramentas**: Os agentes podem usar ferramentas registradas
3. **Prompts**: Os agentes usam prompts para guiar seu comportamento
4. **Armazenamento**: Os agentes podem persistir seu estado

## Detalhes de Implementação

### Gerenciamento de Estado

O sistema de agentes gerencia:

- Estado de execução do agente
- Histórico de conversas
- Contexto do agente
- Recursos do sistema

### Segurança

O sistema inclui:

- Execução segura de código
- Controle de acesso a recursos
- Validação de entrada
- Registro de atividades

### Desempenho

O sistema otimiza:

- Uso de memória
- Tempo de resposta
- Uso de CPU
- Uso de rede

## Melhorias Futuras

Possíveis melhorias futuras para o sistema de agentes:

1. **Agentes Distribuídos**: Suporte para execução distribuída de agentes
2. **Aprendizado**: Capacidade de aprender com interações passadas
3. **Personalização**: Mais opções de personalização de agentes
4. **Monitoramento**: Melhores ferramentas de monitoramento
5. **Integração**: Mais integrações com ferramentas externas
