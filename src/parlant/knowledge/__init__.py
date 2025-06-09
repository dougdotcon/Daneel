"""
Knowledge management module for Daneel.

This module provides functionality for storing, retrieving, and reasoning over knowledge.
"""

from Daneel.knowledge.base import (
    KnowledgeBase,
    KnowledgeItem,
    KnowledgeItemId,
    KnowledgeItemType,
    KnowledgeItemSource,
)
from Daneel.knowledge.graph import KnowledgeGraph
from Daneel.knowledge.reasoning import KnowledgeReasoner, ReasoningResult
from Daneel.knowledge.manager import KnowledgeManager

__all__ = [
    # Knowledge base
    "KnowledgeBase",
    "KnowledgeItem",
    "KnowledgeItemId",
    "KnowledgeItemType",
    "KnowledgeItemSource",

    # Knowledge graph
    "KnowledgeGraph",

    # Knowledge reasoning
    "KnowledgeReasoner",
    "ReasoningResult",

    # Knowledge manager
    "KnowledgeManager",
]
