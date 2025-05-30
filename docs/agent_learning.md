# Aprendizado e Adaptação de Agentes

Este documento descreve a funcionalidade de aprendizado e adaptação de agentes no framework Parlant.

## Visão Geral

O módulo de aprendizado e adaptação de agentes fornece um conjunto abrangente de ferramentas para permitir que os agentes aprendam com suas interações e adaptem seu comportamento ao longo do tempo. Inclui:

1. Rastreamento de histórico de interações para registrar interações e resultados dos agentes
2. Métricas de desempenho e avaliação para medir a eficácia dos agentes
3. Aprendizado baseado em feedback para melhorar as respostas dos agentes com base no feedback do usuário
4. Mecanismos de adaptação de comportamento para ajustar o comportamento do agente ao longo do tempo
5. Personalização baseada em interações do usuário para adaptar as respostas do agente a usuários específicos

## Componentes

### Rastreamento de Histórico de Interações

O componente de rastreamento de histórico de interações fornece uma maneira de registrar e analisar as interações dos agentes:

- Diferentes tipos de interação (mensagens do usuário, mensagens do agente, chamadas de ferramentas, etc.)
- Coleta de feedback (positivo/negativo, avaliações, feedback em texto, correções)
- Rastreamento baseado em sessão
- Capacidades de filtragem e consulta

Exemplo de uso:

```python
from parlant.learning import InteractionHistoryTracker, InteractionType, FeedbackType

# Create an interaction tracker
tracker = InteractionHistoryTracker(document_db, agent_store, logger)

# Track an interaction
interaction = await tracker.track_interaction(
    session_id="session123",
    agent_id="agent456",
    type=InteractionType.AGENT_MESSAGE,
    content="Hello, how can I help you today?",
)

# Add feedback to the interaction
await tracker.add_feedback(
    interaction_id=interaction.id,
    feedback_type=FeedbackType.THUMBS_UP,
    value=True,
    source="user",
)

# Get interactions for a session
interactions = await tracker.get_session_interactions("session123")

# Get feedback statistics for an agent
stats = await tracker.get_feedback_stats("agent456")
```

### Métricas de Desempenho e Avaliação

O componente de métricas de desempenho e avaliação permite medir e analisar o desempenho dos agentes:

- Diferentes tipos de métricas (tempo de resposta, pontuação de feedback, conclusão de tarefas, etc.)
- Análise estatística de métricas
- Avaliações abrangentes combinando múltiplas métricas
- Análise de tendências ao longo do tempo

Exemplo de uso:

```python
from parlant.learning import PerformanceMetricsTracker, MetricType

# Create a metrics tracker
tracker = PerformanceMetricsTracker(document_db, agent_store, interaction_tracker, logger)

# Track a metric
metric = await tracker.track_metric(
    agent_id="agent456",
    type=MetricType.RESPONSE_TIME,
    value=1.5,  # seconds
)

# Get metric statistics
stats = await tracker.get_metric_stats(
    agent_id="agent456",
    type=MetricType.RESPONSE_TIME,
)

# Create an evaluation
evaluation = await tracker.create_evaluation(
    agent_id="agent456",
    metrics=[metric1, metric2, metric3],
    summary="Monthly performance evaluation",
    score=0.85,
)

# List evaluations for an agent
evaluations = await tracker.list_evaluations("agent456")
```

### Aprendizado Baseado em Feedback

O componente de aprendizado baseado em feedback permite que os agentes aprendam com o feedback do usuário:

- Diferentes estratégias de aprendizado (baseado em exemplos, baseado em regras, baseado em modelo, híbrido)
- Identificação de padrões a partir do feedback
- Aplicação de feedback para melhorar respostas
- Pontuação de confiança para padrões aprendidos

Exemplo de uso:

```python
from parlant.learning import FeedbackLearner, LearningStrategy

# Create a feedback learner
learner = FeedbackLearner(
    document_db, agent_store, interaction_tracker, nlp_service, logger,
    strategy=LearningStrategy.HYBRID,
)

# Learn patterns from feedback
patterns = await learner.learn_from_feedback(
    agent_id="agent456",
    days=30,  # Analyze last 30 days of feedback
)

# Apply patterns to improve a response
improved_text = await learner.apply_patterns(
    agent_id="agent456",
    text="Hello, how can I help?",
    min_confidence=0.7,
)

# List patterns for an agent
patterns = await learner.list_patterns(
    agent_id="agent456",
    min_confidence=0.8,
)
```

### Adaptação de Comportamento

O componente de adaptação de comportamento permite que os agentes ajustem seu comportamento ao longo do tempo:

- Diferentes tipos de adaptação (modificação de prompt, ajuste de parâmetros, estilo de resposta, etc.)
- Geração de adaptação baseada em feedback e métricas
- Aplicação e rastreamento de adaptação
- Pontuação de confiança para adaptações

Exemplo de uso:

```python
from parlant.learning import BehaviorAdapter, AdaptationType

# Create a behavior adapter
adapter = BehaviorAdapter(
    document_db, agent_store, interaction_tracker, metrics_tracker,
    feedback_learner, prompt_manager, nlp_service, logger,
)

# Generate adaptations
adaptations = await adapter.generate_adaptations(
    agent_id="agent456",
    days=30,  # Analyze last 30 days of data
)

# Apply an adaptation
success = await adapter.apply_adaptation(adaptation.id)

# List adaptations for an agent
adaptations = await adapter.list_adaptations(
    agent_id="agent456",
    type=AdaptationType.PROMPT_MODIFICATION,
    applied=False,
    min_confidence=0.7,
)
```

### Personalização

O componente de personalização permite adaptar as respostas do agente a usuários específicos:

- Diferentes tipos de preferências (estilo de comunicação, comprimento da resposta, nível técnico, etc.)
- Inferência de preferências a partir de interações
- Personalização de resposta baseada em preferências
- Personalização de prompt para respostas mais adaptadas

Exemplo de uso:

```python
from parlant.learning import PersonalizationManager, PreferenceType

# Create a personalization manager
manager = PersonalizationManager(
    document_db, agent_store, customer_store, interaction_tracker, nlp_service, logger,
)

# Infer user preferences
preferences = await manager.infer_preferences(
    customer_id="customer789",
    days=60,  # Analyze last 60 days of interactions
)

# Get a specific preference
preference = await manager.get_preference(
    customer_id="customer789",
    type=PreferenceType.COMMUNICATION_STYLE,
)

# Personalize a response
personalized = await manager.personalize_response(
    customer_id="customer789",
    text="Here is the information you requested.",
)

# Create a personalized prompt
personalized_prompt = await manager.create_personalized_prompt(
    customer_id="customer789",
    prompt_template="You are an AI assistant.",
)
```

## Integração com Parlant

A funcionalidade de aprendizado e adaptação de agentes está integrada com o framework Parlant:

1. **Sistema de Agente**: O aprendizado e adaptação aprimoram o sistema de agentes com capacidades de melhoria contínua
2. **Gerenciamento de Conhecimento**: Padrões aprendidos e adaptações podem ser armazenados no sistema de gerenciamento de conhecimento
3. **Modelos**: O aprendizado e adaptação podem modificar parâmetros e prompts do modelo para melhor desempenho
4. **Ferramentas**: Adaptações podem melhorar padrões de uso e eficácia das ferramentas

## Detalhes de Implementação

### Armazenamento de Dados

O módulo de aprendizado e adaptação de agentes usa o banco de dados de documentos para armazenar:

- Histórico de interações
- Métricas de desempenho
- Padrões de feedback
- Adaptações de comportamento
- Preferências do usuário

### Processo de Aprendizado

O processo de aprendizado segue estas etapas:

1. **Coleta de Dados**: Interações e feedback são coletados e armazenados
2. **Análise**: Os dados coletados são analisados para identificar padrões e tendências
3. **Aprendizado**: Padrões são aprendidos a partir dos dados analisados
4. **Adaptação**: Adaptações de comportamento são geradas com base nos padrões aprendidos
5. **Aplicação**: Adaptações são aplicadas para melhorar o comportamento do agente
6. **Avaliação**: Os efeitos das adaptações são avaliados para garantir melhoria

### Considerações de Privacidade

O módulo de aprendizado e adaptação de agentes inclui mecanismos de preservar privacidade:

- Minimização de dados: Apenas dados necessários são armazenados
- Anonimização: Identificadores pessoais são removidos quando possível
- Políticas de retenção: Dados são retidos apenas enquanto necessário
- Controles de acesso: Acesso a dados de aprendizado é restrito

## Melhorias Futuras

Possíveis melhorias futuras para o módulo de aprendizado e adaptação de agentes:

1. **Aprendizado de Reforço**: Adicionar suporte para aprendizado de reforço para otimizar o comportamento do agente
2. **Aprendizado Multi-Agente**: Permitir aprendizado a partir de interações entre múltiplos agentes
3. **Aprendizado de Transferência**: Permitir transferência de padrões aprendidos entre agentes
4. **Adaptações Explicáveis**: Fornecer explicações para por que adaptações foram feitas
5. **Aprendizado Guiado pelo Usuário**: Permitir que usuários guiem o processo de aprendizado com instruções explícitas
