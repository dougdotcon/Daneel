# Agent Learning and Adaptation

This document describes the agent learning and adaptation functionality in the Parlant framework.

## Overview

The agent learning and adaptation module provides a comprehensive set of tools for enabling agents to learn from their interactions and adapt their behavior over time. It includes:

1. Interaction history tracking for recording agent interactions and outcomes
2. Performance metrics and evaluation for measuring agent effectiveness
3. Feedback-based learning for improving agent responses based on user feedback
4. Behavior adaptation mechanisms for adjusting agent behavior over time
5. Personalization based on user interactions to tailor agent responses to specific users

## Components

### Interaction History Tracking

The interaction history tracking component provides a way to record and analyze agent interactions:

- Different interaction types (user messages, agent messages, tool calls, etc.)
- Feedback collection (thumbs up/down, ratings, text feedback, corrections)
- Session-based tracking
- Filtering and querying capabilities

Example usage:

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

### Performance Metrics and Evaluation

The performance metrics and evaluation component enables measuring and analyzing agent performance:

- Different metric types (response time, feedback score, task completion, etc.)
- Statistical analysis of metrics
- Comprehensive evaluations combining multiple metrics
- Trend analysis over time

Example usage:

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

### Feedback-Based Learning

The feedback-based learning component enables agents to learn from user feedback:

- Different learning strategies (example-based, rule-based, model-based, hybrid)
- Pattern identification from feedback
- Feedback application to improve responses
- Confidence scoring for learned patterns

Example usage:

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

### Behavior Adaptation

The behavior adaptation component enables agents to adjust their behavior over time:

- Different adaptation types (prompt modification, parameter adjustment, response style, etc.)
- Adaptation generation based on feedback and metrics
- Adaptation application and tracking
- Confidence scoring for adaptations

Example usage:

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

### Personalization

The personalization component enables tailoring agent responses to specific users:

- Different preference types (communication style, response length, technical level, etc.)
- Preference inference from interactions
- Response personalization based on preferences
- Prompt personalization for more tailored responses

Example usage:

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

## Integration with Parlant

The agent learning and adaptation functionality is integrated with the Parlant framework:

1. **Agent System**: Learning and adaptation enhance the agent system with continuous improvement capabilities
2. **Knowledge Management**: Learned patterns and adaptations can be stored in the knowledge management system
3. **Models**: Learning and adaptation can modify model parameters and prompts for better performance
4. **Tools**: Adaptations can improve tool usage patterns and effectiveness

## Implementation Details

### Data Storage

The agent learning and adaptation module uses the document database for storing:

- Interaction history
- Performance metrics
- Feedback patterns
- Behavior adaptations
- User preferences

### Learning Process

The learning process follows these steps:

1. **Data Collection**: Interactions and feedback are collected and stored
2. **Analysis**: Collected data is analyzed to identify patterns and trends
3. **Learning**: Patterns are learned from the analyzed data
4. **Adaptation**: Behavior adaptations are generated based on learned patterns
5. **Application**: Adaptations are applied to improve agent behavior
6. **Evaluation**: The effects of adaptations are evaluated to ensure improvement

### Privacy Considerations

The agent learning and adaptation module includes privacy-preserving mechanisms:

- Data minimization: Only necessary data is stored
- Anonymization: Personal identifiers are removed when possible
- Retention policies: Data is retained only as long as needed
- Access controls: Access to learning data is restricted

## Future Enhancements

Potential future enhancements for the agent learning and adaptation module:

1. **Reinforcement Learning**: Add support for reinforcement learning to optimize agent behavior
2. **Multi-Agent Learning**: Enable learning from interactions between multiple agents
3. **Transfer Learning**: Allow transferring learned patterns between agents
4. **Explainable Adaptations**: Provide explanations for why adaptations were made
5. **User-Guided Learning**: Enable users to guide the learning process with explicit instructions
