"""
Knowledge manager module for Daneel.

This module provides a unified interface for knowledge management.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union, cast
from dataclasses import dataclass

from Daneel.core.loggers import Logger
from Daneel.core.nlp.service import NLPService
from Daneel.core.nlp.embedding import Embedder, EmbedderFactory
from Daneel.core.persistence.document_database import DocumentDatabase
from Daneel.core.persistence.vector_database import VectorDatabase

from Daneel.knowledge.base import (
    KnowledgeBase,
    KnowledgeItem,
    KnowledgeItemId,
    KnowledgeItemType,
    KnowledgeItemSource,
)
from Daneel.knowledge.graph import KnowledgeGraph
from Daneel.knowledge.reasoning import KnowledgeReasoner, ReasoningResult


class KnowledgeManager:
    """Manager for knowledge base, graph, and reasoning."""
    
    def __init__(
        self,
        vector_db: VectorDatabase,
        document_db: DocumentDatabase,
        embedder_type: type[Embedder],
        embedder_factory: EmbedderFactory,
        nlp_service: NLPService,
        logger: Logger,
    ):
        """Initialize the knowledge manager.
        
        Args:
            vector_db: Vector database
            document_db: Document database
            embedder_type: Type of embedder to use
            embedder_factory: Factory for creating embedders
            nlp_service: NLP service
            logger: Logger instance
        """
        self._vector_db = vector_db
        self._document_db = document_db
        self._embedder_type = embedder_type
        self._embedder_factory = embedder_factory
        self._nlp_service = nlp_service
        self._logger = logger
        
        self._knowledge_base: Optional[KnowledgeBase] = None
        self._knowledge_graph: Optional[KnowledgeGraph] = None
        self._knowledge_reasoner: Optional[KnowledgeReasoner] = None
        
    async def __aenter__(self) -> KnowledgeManager:
        """Enter the context manager."""
        self._knowledge_base = KnowledgeBase(
            vector_db=self._vector_db,
            document_db=self._document_db,
            embedder_type=self._embedder_type,
            embedder_factory=self._embedder_factory,
            logger=self._logger,
        )
        await self._knowledge_base.__aenter__()
        
        self._knowledge_graph = KnowledgeGraph(
            knowledge_base=self._knowledge_base,
            logger=self._logger,
        )
        
        self._knowledge_reasoner = KnowledgeReasoner(
            knowledge_base=self._knowledge_base,
            knowledge_graph=self._knowledge_graph,
            nlp_service=self._nlp_service,
            logger=self._logger,
        )
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        if self._knowledge_base:
            await self._knowledge_base.__aexit__(exc_type, exc_val, exc_tb)
            
    @property
    def base(self) -> KnowledgeBase:
        """Get the knowledge base."""
        if not self._knowledge_base:
            raise RuntimeError("Knowledge base not initialized")
        return self._knowledge_base
        
    @property
    def graph(self) -> KnowledgeGraph:
        """Get the knowledge graph."""
        if not self._knowledge_graph:
            raise RuntimeError("Knowledge graph not initialized")
        return self._knowledge_graph
        
    @property
    def reasoner(self) -> KnowledgeReasoner:
        """Get the knowledge reasoner."""
        if not self._knowledge_reasoner:
            raise RuntimeError("Knowledge reasoner not initialized")
        return self._knowledge_reasoner
        
    async def add_text_knowledge(
        self,
        title: str,
        content: str,
        source: KnowledgeItemSource = KnowledgeItemSource.USER,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> KnowledgeItem:
        """Add text knowledge to the knowledge base.
        
        Args:
            title: Knowledge title
            content: Knowledge content
            source: Knowledge source
            metadata: Additional metadata
            tags: Tags for categorization
            
        Returns:
            Created knowledge item
        """
        return await self.base.create_item(
            title=title,
            content=content,
            type=KnowledgeItemType.TEXT,
            source=source,
            metadata=metadata,
            tags=tags,
        )
        
    async def add_code_knowledge(
        self,
        title: str,
        code: str,
        language: str,
        source: KnowledgeItemSource = KnowledgeItemSource.USER,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> KnowledgeItem:
        """Add code knowledge to the knowledge base.
        
        Args:
            title: Knowledge title
            code: Code content
            language: Programming language
            source: Knowledge source
            metadata: Additional metadata
            tags: Tags for categorization
            
        Returns:
            Created knowledge item
        """
        metadata = metadata or {}
        metadata["language"] = language
        
        return await self.base.create_item(
            title=title,
            content=code,
            type=KnowledgeItemType.CODE,
            source=source,
            metadata=metadata,
            tags=tags,
        )
        
    async def add_structured_knowledge(
        self,
        title: str,
        data: Dict[str, Any],
        source: KnowledgeItemSource = KnowledgeItemSource.USER,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> KnowledgeItem:
        """Add structured knowledge to the knowledge base.
        
        Args:
            title: Knowledge title
            data: Structured data
            source: Knowledge source
            metadata: Additional metadata
            tags: Tags for categorization
            
        Returns:
            Created knowledge item
        """
        import json
        
        return await self.base.create_item(
            title=title,
            content=json.dumps(data, indent=2),
            type=KnowledgeItemType.STRUCTURED,
            source=source,
            metadata=metadata,
            tags=tags,
        )
        
    async def relate_knowledge(
        self,
        source_id: KnowledgeItemId,
        target_id: KnowledgeItemId,
        relationship_type: str,
    ) -> None:
        """Relate two knowledge items.
        
        Args:
            source_id: Source item ID
            target_id: Target item ID
            relationship_type: Type of relationship
        """
        await self.graph.add_relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
        )
        
    async def answer_question(
        self,
        question: str,
        max_items: int = 5,
    ) -> ReasoningResult:
        """Answer a question using the knowledge base.
        
        Args:
            question: Question to answer
            max_items: Maximum number of knowledge items to consider
            
        Returns:
            Reasoning result
        """
        return await self.reasoner.answer_question(
            question=question,
            max_items=max_items,
        )
        
    async def search_knowledge(
        self,
        query: str,
        k: int = 5,
        type: Optional[KnowledgeItemType] = None,
        source: Optional[KnowledgeItemSource] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Tuple[KnowledgeItem, float]]:
        """Search for knowledge items.
        
        Args:
            query: Search query
            k: Number of results to return
            type: Filter by type
            source: Filter by source
            tags: Filter by tags
            
        Returns:
            List of knowledge items with similarity scores
        """
        return await self.base.search_items(
            query=query,
            k=k,
            type=type,
            source=source,
            tags=tags,
        )
        
    async def get_knowledge_network(
        self,
        item_ids: Optional[List[KnowledgeItemId]] = None,
        include_neighbors: bool = True,
    ) -> Dict[str, Any]:
        """Get a network representation of knowledge items.
        
        Args:
            item_ids: Item IDs to include (if None, include all items)
            include_neighbors: Whether to include neighbors of the specified items
            
        Returns:
            Dictionary representation of the knowledge network
        """
        if item_ids is None:
            # Get all items
            items = await self.base.list_items()
            item_ids = [item.id for item in items]
            
        return await self.graph.get_subgraph(
            item_ids=item_ids,
            include_neighbors=include_neighbors,
        )
