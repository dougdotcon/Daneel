"""
Knowledge management module for Parlant.

This module provides functionality for storing, retrieving, and reasoning over knowledge.
"""

from parlant.knowledge.base import (
    KnowledgeBase,
    KnowledgeItem,
    KnowledgeItemId,
    KnowledgeItemType,
    KnowledgeItemSource,
)
from parlant.knowledge.graph import KnowledgeGraph
from parlant.knowledge.reasoning import KnowledgeReasoner, ReasoningResult
from parlant.knowledge.manager import KnowledgeManager

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
