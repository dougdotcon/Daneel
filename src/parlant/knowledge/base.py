"""
Knowledge base module for Daneel.

This module provides a knowledge base for storing and retrieving knowledge items.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union, cast
from dataclasses import dataclass, field
from uuid import uuid4

from Daneel.core.common import JSONSerializable, Version, generate_id, md5_checksum
from Daneel.core.async_utils import ReaderWriterLock
from Daneel.core.loggers import Logger
from Daneel.core.nlp.embedding import Embedder, EmbedderFactory
from Daneel.core.persistence.common import ItemNotFoundError, ObjectId, UniqueId, Where
from Daneel.core.persistence.document_database import DocumentCollection, DocumentDatabase
from Daneel.core.persistence.vector_database import (
    BaseDocument,
    SimilarDocumentResult,
    VectorCollection,
    VectorDatabase,
)


class KnowledgeItemId(str):
    """Knowledge item ID."""
    pass


class KnowledgeItemType(str, Enum):
    """Types of knowledge items."""
    
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED = "structured"
    GRAPH = "graph"


class KnowledgeItemSource(str, Enum):
    """Sources of knowledge items."""
    
    USER = "user"
    SYSTEM = "system"
    AGENT = "agent"
    EXTERNAL = "external"


@dataclass
class KnowledgeItem:
    """Knowledge item."""
    
    id: KnowledgeItemId
    creation_utc: datetime
    title: str
    content: str
    type: KnowledgeItemType
    source: KnowledgeItemSource
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    relationships: List[Tuple[KnowledgeItemId, str]] = field(default_factory=list)


class _KnowledgeItemDocument(BaseDocument):
    """Knowledge item document for storage."""
    
    id: KnowledgeItemId
    version: str
    creation_utc: str
    title: str
    content: str
    type: str
    source: str
    metadata: Dict[str, JSONSerializable]
    tags: List[str]
    checksum: str


class _KnowledgeRelationshipDocument(BaseDocument):
    """Knowledge relationship document for storage."""
    
    id: ObjectId
    version: str
    creation_utc: str
    source_id: KnowledgeItemId
    target_id: KnowledgeItemId
    relationship_type: str


class KnowledgeBase:
    """Knowledge base for storing and retrieving knowledge items."""
    
    VERSION = Version.from_string("0.1.0")
    
    def __init__(
        self,
        vector_db: VectorDatabase,
        document_db: DocumentDatabase,
        embedder_type: type[Embedder],
        embedder_factory: EmbedderFactory,
        logger: Logger,
    ):
        """Initialize the knowledge base.
        
        Args:
            vector_db: Vector database for storing knowledge items
            document_db: Document database for storing relationships
            embedder_type: Type of embedder to use
            embedder_factory: Factory for creating embedders
            logger: Logger instance
        """
        self._vector_db = vector_db
        self._document_db = document_db
        self._embedder_type = embedder_type
        self._embedder = embedder_factory.create_embedder(embedder_type)
        self._logger = logger
        
        self._collection: VectorCollection[_KnowledgeItemDocument]
        self._relationship_collection: DocumentCollection[_KnowledgeRelationshipDocument]
        
        self._lock = ReaderWriterLock()
        
    async def __aenter__(self) -> KnowledgeBase:
        """Enter the context manager."""
        self._collection = await self._vector_db.get_or_create_collection(
            name="knowledge_items",
            schema=_KnowledgeItemDocument,
            embedder_type=self._embedder_type,
            document_loader=self._document_loader,
        )
        
        self._relationship_collection = await self._document_db.get_or_create_collection(
            name="knowledge_relationships",
            schema=_KnowledgeRelationshipDocument,
            document_loader=self._relationship_document_loader,
        )
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass
        
    async def _document_loader(self, doc: BaseDocument) -> Optional[_KnowledgeItemDocument]:
        """Load a knowledge item document.
        
        Args:
            doc: Base document
            
        Returns:
            Knowledge item document
        """
        return cast(_KnowledgeItemDocument, doc)
        
    async def _relationship_document_loader(self, doc: BaseDocument) -> Optional[_KnowledgeRelationshipDocument]:
        """Load a knowledge relationship document.
        
        Args:
            doc: Base document
            
        Returns:
            Knowledge relationship document
        """
        return cast(_KnowledgeRelationshipDocument, doc)
        
    def _serialize(self, item: KnowledgeItem, checksum: str) -> _KnowledgeItemDocument:
        """Serialize a knowledge item.
        
        Args:
            item: Knowledge item
            checksum: Content checksum
            
        Returns:
            Knowledge item document
        """
        return {
            "id": item.id,
            "version": self.VERSION.to_string(),
            "creation_utc": item.creation_utc.isoformat(),
            "title": item.title,
            "content": item.content,
            "type": item.type.value,
            "source": item.source.value,
            "metadata": item.metadata,
            "tags": item.tags,
            "checksum": checksum,
        }
        
    async def _deserialize(self, document: _KnowledgeItemDocument) -> KnowledgeItem:
        """Deserialize a knowledge item document.
        
        Args:
            document: Knowledge item document
            
        Returns:
            Knowledge item
        """
        # Get relationships for this item
        relationships = []
        relationship_docs = await self._relationship_collection.find(
            filters={"source_id": {"$eq": document["id"]}}
        )
        
        for rel_doc in relationship_docs:
            relationships.append((rel_doc["target_id"], rel_doc["relationship_type"]))
        
        return KnowledgeItem(
            id=document["id"],
            creation_utc=datetime.fromisoformat(document["creation_utc"]),
            title=document["title"],
            content=document["content"],
            type=KnowledgeItemType(document["type"]),
            source=KnowledgeItemSource(document["source"]),
            metadata=document["metadata"],
            tags=document["tags"],
            relationships=relationships,
        )
        
    async def create_item(
        self,
        title: str,
        content: str,
        type: KnowledgeItemType,
        source: KnowledgeItemSource,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
        tags: Optional[List[str]] = None,
        creation_utc: Optional[datetime] = None,
    ) -> KnowledgeItem:
        """Create a knowledge item.
        
        Args:
            title: Item title
            content: Item content
            type: Item type
            source: Item source
            metadata: Item metadata
            tags: Item tags
            creation_utc: Creation timestamp
            
        Returns:
            Created knowledge item
        """
        async with self._lock.writer_lock:
            creation_utc = creation_utc or datetime.now(timezone.utc)
            
            item = KnowledgeItem(
                id=KnowledgeItemId(generate_id()),
                creation_utc=creation_utc,
                title=title,
                content=content,
                type=type,
                source=source,
                metadata=metadata or {},
                tags=tags or [],
                relationships=[],
            )
            
            await self._collection.insert_one(
                document=self._serialize(
                    item=item,
                    checksum=md5_checksum(content),
                )
            )
            
        return item
        
    async def read_item(self, item_id: KnowledgeItemId) -> KnowledgeItem:
        """Read a knowledge item.
        
        Args:
            item_id: Item ID
            
        Returns:
            Knowledge item
            
        Raises:
            ItemNotFoundError: If the item is not found
        """
        async with self._lock.reader_lock:
            document = await self._collection.find_one(filters={"id": {"$eq": item_id}})
            
        if not document:
            raise ItemNotFoundError(item_id=UniqueId(item_id))
            
        return await self._deserialize(document)
        
    async def update_item(
        self,
        item_id: KnowledgeItemId,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
        tags: Optional[List[str]] = None,
    ) -> KnowledgeItem:
        """Update a knowledge item.
        
        Args:
            item_id: Item ID
            title: New title
            content: New content
            metadata: New metadata
            tags: New tags
            
        Returns:
            Updated knowledge item
            
        Raises:
            ItemNotFoundError: If the item is not found
        """
        async with self._lock.writer_lock:
            document = await self._collection.find_one(filters={"id": {"$eq": item_id}})
            
            if not document:
                raise ItemNotFoundError(item_id=UniqueId(item_id))
                
            params: Dict[str, Any] = {}
            
            if title is not None:
                params["title"] = title
                
            if content is not None:
                params["content"] = content
                params["checksum"] = md5_checksum(content)
                
            if metadata is not None:
                params["metadata"] = metadata
                
            if tags is not None:
                params["tags"] = tags
                
            if params:
                await self._collection.update_one(
                    filters={"id": {"$eq": item_id}},
                    params=params,
                )
                
            # Get the updated document
            document = await self._collection.find_one(filters={"id": {"$eq": item_id}})
            
        return await self._deserialize(document)
        
    async def delete_item(self, item_id: KnowledgeItemId) -> None:
        """Delete a knowledge item.
        
        Args:
            item_id: Item ID
            
        Raises:
            ItemNotFoundError: If the item is not found
        """
        async with self._lock.writer_lock:
            # Delete the item
            result = await self._collection.delete_one(filters={"id": {"$eq": item_id}})
            
            if not result.deleted_count:
                raise ItemNotFoundError(item_id=UniqueId(item_id))
                
            # Delete relationships
            await self._relationship_collection.delete_many(
                filters={"$or": [
                    {"source_id": {"$eq": item_id}},
                    {"target_id": {"$eq": item_id}},
                ]}
            )
            
    async def list_items(
        self,
        type: Optional[KnowledgeItemType] = None,
        source: Optional[KnowledgeItemSource] = None,
        tags: Optional[List[str]] = None,
    ) -> List[KnowledgeItem]:
        """List knowledge items.
        
        Args:
            type: Filter by type
            source: Filter by source
            tags: Filter by tags
            
        Returns:
            List of knowledge items
        """
        async with self._lock.reader_lock:
            filters: Dict[str, Any] = {}
            
            if type is not None:
                filters["type"] = {"$eq": type.value}
                
            if source is not None:
                filters["source"] = {"$eq": source.value}
                
            if tags is not None and tags:
                # Match items that have all the specified tags
                filters["tags"] = {"$all": tags}
                
            documents = await self._collection.find(filters=filters)
            
        return [await self._deserialize(doc) for doc in documents]
        
    async def search_items(
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
        async with self._lock.reader_lock:
            filters: Dict[str, Any] = {}
            
            if type is not None:
                filters["type"] = {"$eq": type.value}
                
            if source is not None:
                filters["source"] = {"$eq": source.value}
                
            if tags is not None and tags:
                # Match items that have all the specified tags
                filters["tags"] = {"$all": tags}
                
            results = await self._collection.find_similar_documents(
                filters=filters,
                query=query,
                k=k,
            )
            
        return [(await self._deserialize(result.document), result.score) for result in results]
