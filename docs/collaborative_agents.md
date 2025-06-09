# Agentes Colaborativos

Este documento descreve a funcionalidade de agentes colaborativos no framework Daneel.

## Visão Geral

O módulo de agentes colaborativos fornece um conjunto abrangente de ferramentas para permitir que os agentes trabalhem juntos para resolver problemas complexos. Inclui:

1. Protocolo de comunicação entre agentes para troca estruturada de mensagens
2. Gerenciamento de equipe para organizar agentes em equipes com objetivos específicos
3. Especialização de agentes baseada em papéis para permitir divisão de trabalho
4. Mecanismos de delegação e coordenação de tarefas para resolução de problemas complexos
5. Mecanismos de consenso para tomada de decisão colaborativa
6. Conhecimento e contexto compartilhados entre agentes

## Componentes

### Protocolo de Comunicação entre Agentes

O protocolo de comunicação entre agentes fornece uma maneira estruturada para os agentes trocarem mensagens:

- Diferentes tipos de mensagem para diferentes propósitos (texto, comandos, tarefas, etc.)
- Níveis de prioridade de mensagem
- Suporte para mensagens direcionadas e em broadcast
- Barramento de mensagens para roteamento entre agentes

Exemplo de uso:

```python
from parlat.collaborative import AgentCommunicator, MessageBus, MessageType, MessagePriority

# Create a message bus
message_bus = MessageBus()

# Create communicators for agents
agent1_communicator = AgentCommunicator(agent_id="agent1", message_bus=message_bus)
agent2_communicator = AgentCommunicator(agent_id="agent2", message_bus=message_bus)

# Register a message handler for agent2
async def handle_text_message(message):
    print(f"Received message: {message.content}")
    
agent2_communicator.register_handler(MessageType.TEXT, handle_text_message)

# Send a message from agent1 to agent2
await agent1_communicator.send_text(
    receiver_id="agent2",
    text="Hello, agent2!",
    priority=MessagePriority.NORMAL,
)

# Broadcast a message from agent1 to all agents
await agent1_communicator.broadcast(
    message_type=MessageType.SYSTEM,
    content="System announcement",
    priority=MessagePriority.HIGH,
)
```

### Gerenciamento de Equipe

O componente de gerenciamento de equipe permite organizar agentes em equipes:

- Criação e gerenciamento de equipes
- Adição de agentes a equipes com papéis específicos
- Comunicação baseada em equipe
- Permissões e responsabilidades baseadas em papéis

Exemplo de uso:

```python
from parlat.collaborative import TeamManager, TeamRole

# Create a team manager
team_manager = TeamManager(agent_store, message_bus, logger)

# Create a team
team = await team_manager.create_team(
    name="Development Team",
    description="A team for software development",
)

# Add agents to the team with specific roles
await team_manager.add_member(
    team_id=team.id,
    agent_id="agent1",
    roles=[TeamRole.LEADER],
)

await team_manager.add_member(
    team_id=team.id,
    agent_id="agent2",
    roles=[TeamRole.SPECIALIST],
)

# Get team members with a specific role
specialists = await team_manager.get_team_by_role(
    team_id=team.id,
    role=TeamRole.SPECIALIST,
)

# Broadcast a message to all team members
await team_manager.broadcast_to_team(
    sender_id="agent1",
    team_id=team.id,
    message_type=MessageType.TEXT,
    content="Team meeting at 10 AM",
)
```

### Delegação e Coordenação de Tarefas

O componente de delegação e coordenação de tarefas permite que os agentes atribuam e coordenem tarefas:

- Criação e gerenciamento de tarefas
- Atribuição de tarefas a agentes
- Rastreamento de status e progresso de tarefas
- Tratamento de dependências de tarefas
- Relatório de resultados de tarefas

Exemplo de uso:

```python
from parlat.collaborative import TaskManager, TaskStatus, TaskPriority

# Create a task manager
task_manager = TaskManager(agent_store, team_manager, message_bus, logger)

# Create a task
task = await task_manager.create_task(
    title="Implement Feature X",
    description="Implement the new feature X according to the specifications",
    creator_id="agent1",
    priority=TaskPriority.HIGH,
    team_id=team.id,
    deadline=datetime.now(timezone.utc) + timedelta(days=3),
)

# Assign the task to an agent
await task_manager.assign_task(
    task_id=task.id,
    agent_id="agent2",
)

# Update task status
await task_manager.update_task_status(
    task_id=task.id,
    agent_id="agent2",
    status=TaskStatus.IN_PROGRESS,
    progress=0.5,
)

# Complete the task
await task_manager.update_task_status(
    task_id=task.id,
    agent_id="agent2",
    status=TaskStatus.COMPLETED,
    progress=1.0,
    result="Feature X has been implemented successfully",
)
```

### Mecanismos de Consenso

O componente de mecanismos de consenso permite a tomada de decisão colaborativa:

- Diferentes tipos de consenso (maioria, super maioria, unânime, ponderado)
- Votação em propostas
- Rastreamento de status de consenso
- Notificação de participantes sobre resultados

Exemplo de uso:

```python
from parlat.collaborative import ConsensusManager, ConsensusType, VoteOption

# Create a consensus manager
consensus_manager = ConsensusManager(agent_store, team_manager, message_bus, logger)

# Create a consensus process
consensus = await consensus_manager.create_consensus(
    title="Feature Prioritization",
    description="Vote on which feature to implement next",
    creator_id="agent1",
    type=ConsensusType.MAJORITY,
    team_id=team.id,
)

# Agents vote on the consensus
await consensus_manager.vote(
    consensus_id=consensus.id,
    agent_id="agent2",
    option=VoteOption.YES,
    reason="Feature X is more important for our users",
)

await consensus_manager.vote(
    consensus_id=consensus.id,
    agent_id="agent3",
    option=VoteOption.NO,
    reason="Feature Y should be prioritized instead",
)

# Close the consensus process
await consensus_manager.close_consensus(
    consensus_id=consensus.id,
    closer_id="agent1",
)
```

### Conhecimento Compartilhado

O componente de conhecimento compartilhado permite que os agentes compartilhem conhecimento entre si:

- Diferentes níveis de acesso (leitura, escrita, administração)
- Compartilhamento de conhecimento com agentes individuais ou equipes
- Rastreamento de permissões
- Notificação de agentes sobre conhecimento compartilhado

Exemplo de uso:

```python
from parlat.collaborative import SharedKnowledgeManager, SharedKnowledgeAccess

# Create a shared knowledge manager
shared_knowledge_manager = SharedKnowledgeManager(
    agent_store, team_manager, knowledge_manager, message_bus, logger
)

# Share knowledge with an agent
await shared_knowledge_manager.share_knowledge(
    knowledge_id="knowledge1",
    owner_id="agent1",
    recipient_id="agent2",
    access=SharedKnowledgeAccess.READ,
)

# Share knowledge with a team
await shared_knowledge_manager.share_with_team(
    knowledge_id="knowledge1",
    owner_id="agent1",
    team_id=team.id,
    access=SharedKnowledgeAccess.WRITE,
)

# Check if an agent has access to knowledge
has_access = await shared_knowledge_manager.check_access(
    knowledge_id="knowledge1",
    agent_id="agent2",
    required_access=SharedKnowledgeAccess.WRITE,
)
```

## Integração com Daneel

A funcionalidade de agentes colaborativos está integrada com o framework Daneel:

1. **Sistema de Agente**: Os agentes colaborativos estendem o sistema base de agentes
2. **Gerenciamento de Conhecimento**: O conhecimento compartilhado é armazenado no sistema de gerenciamento de conhecimento
3. **Prompts**: O contexto colaborativo pode ser incluído em prompts para melhor compreensão
4. **Ferramentas**: Ferramentas colaborativas permitem que os agentes trabalhem juntos

## Detalhes de Implementação

### Armazenamento de Dados

O módulo de agentes colaborativos usa o banco de dados de documentos para armazenar:

- Mensagens entre agentes
- Informações de equipe e membros
- Tarefas e seu estado
- Processos de consenso
- Permissões de conhecimento compartilhado

### Processo Colaborativo

O processo colaborativo segue estas etapas:

1. **Formação de Equipe**: Agentes são organizados em equipes com papéis específicos
2. **Comunicação**: Agentes trocam mensagens para coordenar atividades
3. **Delegação**: Tarefas são atribuídas a agentes apropriados
4. **Execução**: Agentes trabalham em suas tarefas atribuídas
5. **Coordenação**: O progresso é rastreado e ajustes são feitos conforme necessário
6. **Consenso**: Decisões importantes são tomadas através de processos de consenso
7. **Compartilhamento**: Conhecimento e resultados são compartilhados entre agentes

### Considerações de Privacidade

O módulo de agentes colaborativos inclui mecanismos de preservação de privacidade:

- Controle de acesso granular para conhecimento compartilhado
- Registro de todas as ações colaborativas
- Proteção de informações sensíveis
- Isolamento de dados entre equipes

## Melhorias Futuras

Possíveis melhorias futuras para o módulo de agentes colaborativos:

1. **Aprendizado Colaborativo**: Permitir que agentes aprendam uns com os outros
2. **Negociação Avançada**: Implementar protocolos mais sofisticados de negociação
3. **Otimização de Equipe**: Melhorar a formação e composição de equipes
4. **Resolução de Conflitos**: Adicionar mecanismos para resolver conflitos entre agentes
5. **Colaboração Multi-Equipe**: Suportar colaboração entre múltiplas equipes
