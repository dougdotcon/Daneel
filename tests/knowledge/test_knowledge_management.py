"""
Tests for the knowledge management functionality.
"""

import os
import pytest
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, AsyncMock

from parlant.core.loggers import ConsoleLogger
from parlant.core.nlp.service import NLPService
from parlant.core.nlp.embedding import Embedder, EmbedderFactory
from parlant.core.persistence.document_database import DocumentDatabase
from parlant.core.persistence.vector_database import VectorDatabase
from parlant.adapters.db.transient import TransientDocumentDatabase
from parlant.adapters.vector_db.transient import TransientVectorDatabase

from parlant.knowledge import (
    KnowledgeManager,
    KnowledgeItem,
    KnowledgeItemId,
    KnowledgeItemType,
    KnowledgeItemSource,
)


class MockEmbedder(Embedder):
    """Mock embedder for testing."""
    
    @property
    def dimensions(self) -> int:
        return 384
        
    async def embed(self, texts: List[str]) -> Any:
        # Return mock embeddings
        import numpy as np
        vectors = np.random.rand(len(texts), self.dimensions).tolist()
        return type("EmbeddingResult", (), {"vectors": vectors})


class MockEmbedderFactory(EmbedderFactory):
    """Mock embedder factory for testing."""
    
    def create_embedder(self, embedder_type: type[Embedder]) -> Embedder:
        return MockEmbedder()


class MockNLPService(NLPService):
    """Mock NLP service for testing."""
    
    async def get_embedder(self) -> Embedder:
        return MockEmbedder()
        
    async def get_generator(self) -> Any:
        generator = AsyncMock()
        generator.generate = AsyncMock(return_value=type("GenerationResult", (), {
            "text": "Answer: This is a test answer\nConfidence: 0.8\nReasoning:\n- Step 1\n- Step 2",
            "generation_info": None,
        }))
        return generator


@pytest.fixture
def logger():
    return ConsoleLogger()


@pytest.fixture
def nlp_service():
    return MockNLPService()


@pytest.fixture
def embedder_factory():
    return MockEmbedderFactory(None)


@pytest.fixture
def document_db():
    return TransientDocumentDatabase()


@pytest.fixture
def vector_db(logger, embedder_factory):
    return TransientVectorDatabase(logger, embedder_factory)


@pytest.fixture
async def knowledge_manager(logger, vector_db, document_db, embedder_factory, nlp_service):
    async with KnowledgeManager(
        vector_db=vector_db,
        document_db=document_db,
        embedder_type=MockEmbedder,
        embedder_factory=embedder_factory,
        nlp_service=nlp_service,
        logger=logger,
    ) as manager:
        yield manager


async def test_add_text_knowledge(knowledge_manager):
    """Test adding text knowledge."""
    # Add text knowledge
    item = await knowledge_manager.add_text_knowledge(
        title="Test Knowledge",
        content="This is a test knowledge item.",
        source=KnowledgeItemSource.USER,
        metadata={"key": "value"},
        tags=["test", "knowledge"],
    )
    
    # Check that the item was created correctly
    assert item.id is not None
    assert item.title == "Test Knowledge"
    assert item.content == "This is a test knowledge item."
    assert item.type == KnowledgeItemType.TEXT
    assert item.source == KnowledgeItemSource.USER
    assert item.metadata == {"key": "value"}
    assert item.tags == ["test", "knowledge"]
    
    # Retrieve the item
    retrieved_item = await knowledge_manager.base.read_item(item.id)
    
    # Check that the retrieved item matches
    assert retrieved_item.id == item.id
    assert retrieved_item.title == item.title
    assert retrieved_item.content == item.content
    assert retrieved_item.type == item.type
    assert retrieved_item.source == item.source
    assert retrieved_item.metadata == item.metadata
    assert retrieved_item.tags == item.tags


async def test_add_code_knowledge(knowledge_manager):
    """Test adding code knowledge."""
    # Add code knowledge
    item = await knowledge_manager.add_code_knowledge(
        title="Test Code",
        code="def test():\n    return 'Hello, World!'",
        language="python",
        source=KnowledgeItemSource.USER,
        tags=["test", "code", "python"],
    )
    
    # Check that the item was created correctly
    assert item.id is not None
    assert item.title == "Test Code"
    assert item.content == "def test():\n    return 'Hello, World!'"
    assert item.type == KnowledgeItemType.CODE
    assert item.source == KnowledgeItemSource.USER
    assert item.metadata == {"language": "python"}
    assert item.tags == ["test", "code", "python"]


async def test_add_structured_knowledge(knowledge_manager):
    """Test adding structured knowledge."""
    # Add structured knowledge
    data = {
        "name": "Test",
        "value": 42,
        "nested": {
            "key": "value",
        },
    }
    
    item = await knowledge_manager.add_structured_knowledge(
        title="Test Structured Data",
        data=data,
        source=KnowledgeItemSource.USER,
        tags=["test", "structured"],
    )
    
    # Check that the item was created correctly
    assert item.id is not None
    assert item.title == "Test Structured Data"
    assert item.type == KnowledgeItemType.STRUCTURED
    assert item.source == KnowledgeItemSource.USER
    assert item.tags == ["test", "structured"]
    
    # Check that the content is JSON
    import json
    parsed_data = json.loads(item.content)
    assert parsed_data == data


async def test_relate_knowledge(knowledge_manager):
    """Test relating knowledge items."""
    # Add two knowledge items
    item1 = await knowledge_manager.add_text_knowledge(
        title="Item 1",
        content="This is the first item.",
    )
    
    item2 = await knowledge_manager.add_text_knowledge(
        title="Item 2",
        content="This is the second item.",
    )
    
    # Relate the items
    await knowledge_manager.relate_knowledge(
        source_id=item1.id,
        target_id=item2.id,
        relationship_type="related_to",
    )
    
    # Get neighbors of item1
    neighbors = await knowledge_manager.graph.get_neighbors(
        item_id=item1.id,
        direction="outgoing",
    )
    
    # Check that item2 is a neighbor of item1
    assert len(neighbors) == 1
    assert neighbors[0].id == item2.id


async def test_search_knowledge(knowledge_manager):
    """Test searching for knowledge items."""
    # Add some knowledge items
    await knowledge_manager.add_text_knowledge(
        title="Python Programming",
        content="Python is a high-level programming language.",
        tags=["programming", "python"],
    )
    
    await knowledge_manager.add_text_knowledge(
        title="JavaScript Programming",
        content="JavaScript is a scripting language for web development.",
        tags=["programming", "javascript"],
    )
    
    await knowledge_manager.add_text_knowledge(
        title="Machine Learning",
        content="Machine learning is a subset of artificial intelligence.",
        tags=["ai", "ml"],
    )
    
    # Search for programming-related items
    results = await knowledge_manager.search_knowledge(
        query="programming language",
        k=2,
    )
    
    # Check the results
    assert len(results) == 2
    assert results[0][0].title in ["Python Programming", "JavaScript Programming"]
    assert results[1][0].title in ["Python Programming", "JavaScript Programming"]
    
    # Search with tag filter
    results = await knowledge_manager.search_knowledge(
        query="programming",
        tags=["python"],
    )
    
    # Check the results
    assert len(results) == 1
    assert results[0][0].title == "Python Programming"


async def test_answer_question(knowledge_manager):
    """Test answering questions using the knowledge base."""
    # Add some knowledge items
    await knowledge_manager.add_text_knowledge(
        title="Solar System",
        content="The solar system consists of the Sun and eight planets.",
    )
    
    await knowledge_manager.add_text_knowledge(
        title="Earth",
        content="Earth is the third planet from the Sun and the only astronomical object known to harbor life.",
    )
    
    # Ask a question
    result = await knowledge_manager.answer_question(
        question="What is the third planet from the Sun?",
    )
    
    # Check the result
    assert result.answer == "This is a test answer"
    assert result.confidence == 0.8
    assert len(result.reasoning_steps) == 2
    assert result.reasoning_steps[0] == "Step 1"
    assert result.reasoning_steps[1] == "Step 2"
    assert len(result.supporting_items) > 0
