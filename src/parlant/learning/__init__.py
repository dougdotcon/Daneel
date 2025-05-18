"""
Agent learning and adaptation module for Parlant.

This module provides functionality for agent learning and adaptation, including:
- Interaction history tracking
- Performance metrics and evaluation
- Feedback-based learning
- Behavior adaptation
- Personalization based on user interactions
"""

from parlant.learning.history import (
    InteractionHistoryTracker,
    Interaction,
    InteractionId,
    InteractionSessionId,
    InteractionType,
    FeedbackType,
    Feedback,
)

from parlant.learning.metrics import (
    PerformanceMetricsTracker,
    MetricType,
    MetricId,
    MetricValue,
    EvaluationId,
    Evaluation,
)

from parlant.learning.feedback import (
    FeedbackLearner,
    FeedbackPattern,
    FeedbackPatternId,
    LearningStrategy,
)

from parlant.learning.adaptation import (
    BehaviorAdapter,
    BehaviorAdaptation,
    AdaptationId,
    AdaptationType,
)

from parlant.learning.personalization import (
    PersonalizationManager,
    UserPreference,
    PreferenceId,
    PreferenceType,
)

__all__ = [
    # Interaction History
    "InteractionHistoryTracker",
    "Interaction",
    "InteractionId",
    "InteractionSessionId",
    "InteractionType",
    "FeedbackType",
    "Feedback",
    
    # Performance Metrics
    "PerformanceMetricsTracker",
    "MetricType",
    "MetricId",
    "MetricValue",
    "EvaluationId",
    "Evaluation",
    
    # Feedback Learning
    "FeedbackLearner",
    "FeedbackPattern",
    "FeedbackPatternId",
    "LearningStrategy",
    
    # Behavior Adaptation
    "BehaviorAdapter",
    "BehaviorAdaptation",
    "AdaptationId",
    "AdaptationType",
    
    # Personalization
    "PersonalizationManager",
    "UserPreference",
    "PreferenceId",
    "PreferenceType",
]
