# Knowledge Management

This document describes the knowledge management functionality in the Parlant framework.

## Overview

The knowledge management module provides a comprehensive set of tools for storing, retrieving, and reasoning over knowledge. It includes:

1. A knowledge base for storing structured and unstructured knowledge
2. A knowledge graph for representing relationships between knowledge items
3. A reasoning engine for answering questions and generating inferences
4. Support for multi-modal knowledge (text, code, structured data, etc.)

## Components

### Knowledge Base

The `KnowledgeBase` class provides functionality for storing and retrieving knowledge items:

- Creating knowledge items of different types
- Updating and deleting knowledge items
- Searching for knowledge items using vector similarity
- Filtering knowledge items by type, source, and tags

Example usage:

```python
from parlant.knowledge import KnowledgeBase, KnowledgeItemType, KnowledgeItemSource
from parlant.core.loggers import ConsoleLogger
from parlant.adapters.vector_db.chroma import ChromaDatabase
from parlant.adapters.db.transient import TransientDocumentDatabase
from parlant.core.nlp.embedding import EmbedderFactory

# Create a knowledge base
async with KnowledgeBase(
    vector_db=chroma_db,
    document_db=document_db,
    embedder_type=embedder_type,
    embedder_factory=embedder_factory,
    logger=ConsoleLogger(),
) as kb:
    # Create a knowledge item
    item = await kb.create_item(
        title="Python Programming",
        content="Python is a high-level programming language.",
        type=KnowledgeItemType.TEXT,
        source=KnowledgeItemSource.USER,
        metadata={"author": "John Doe"},
        tags=["programming", "python"],
    )
    
    # Retrieve a knowledge item
    item = await kb.read_item(item.id)
    
    # Update a knowledge item
    item = await kb.update_item(
        item_id=item.id,
        title="Python Programming Language",
        content="Python is a high-level, interpreted programming language.",
    )
    
    # Search for knowledge items
    results = await kb.search_items(
        query="programming language",
        k=5,
        type=KnowledgeItemType.TEXT,
        tags=["python"],
    )
```

### Knowledge Graph

The `KnowledgeGraph` class provides functionality for representing relationships between knowledge items:

- Adding and removing relationships
- Getting neighbors of a knowledge item
- Finding paths between knowledge items
- Extracting subgraphs for visualization

Example usage:

```python
from parlant.knowledge import KnowledgeGraph
from parlant.core.loggers import ConsoleLogger

# Create a knowledge graph
graph = KnowledgeGraph(
    knowledge_base=kb,
    logger=ConsoleLogger(),
)

# Initialize the graph
await graph.initialize()

# Add a relationship
await graph.add_relationship(
    source_id=item1.id,
    target_id=item2.id,
    relationship_type="related_to",
)

# Get neighbors of a knowledge item
neighbors = await graph.get_neighbors(
    item_id=item1.id,
    relationship_type="related_to",
    direction="outgoing",
)

# Get a path between knowledge items
path = await graph.get_path(
    source_id=item1.id,
    target_id=item3.id,
)

# Get a subgraph for visualization
subgraph = await graph.get_subgraph(
    item_ids=[item1.id, item2.id, item3.id],
    include_neighbors=True,
)
```

### Knowledge Reasoner

The `KnowledgeReasoner` class provides functionality for reasoning over the knowledge base:

- Answering questions using relevant knowledge items
- Generating inferences about knowledge items
- Validating relationships between knowledge items

Example usage:

```python
from parlant.knowledge import KnowledgeReasoner
from parlant.core.loggers import ConsoleLogger

# Create a knowledge reasoner
reasoner = KnowledgeReasoner(
    knowledge_base=kb,
    knowledge_graph=graph,
    nlp_service=nlp_service,
    logger=ConsoleLogger(),
)

# Answer a question
result = await reasoner.answer_question(
    question="What is Python used for?",
    max_items=5,
)

# Generate an inference
result = await reasoner.generate_inference(
    item_id=item.id,
    max_related_items=3,
)

# Validate a relationship
result = await reasoner.validate_relationship(
    source_id=item1.id,
    target_id=item2.id,
    relationship_type="related_to",
)
```

### Knowledge Manager

The `KnowledgeManager` class provides a unified interface for knowledge management:

- Adding different types of knowledge (text, code, structured data)
- Relating knowledge items
- Searching for knowledge
- Answering questions
- Getting knowledge networks for visualization

Example usage:

```python
from parlant.knowledge import KnowledgeManager
from parlant.core.loggers import ConsoleLogger

# Create a knowledge manager
async with KnowledgeManager(
    vector_db=vector_db,
    document_db=document_db,
    embedder_type=embedder_type,
    embedder_factory=embedder_factory,
    nlp_service=nlp_service,
    logger=ConsoleLogger(),
) as manager:
    # Add text knowledge
    item1 = await manager.add_text_knowledge(
        title="Python Programming",
        content="Python is a high-level programming language.",
        tags=["programming", "python"],
    )
    
    # Add code knowledge
    item2 = await manager.add_code_knowledge(
        title="Hello World",
        code="print('Hello, World!')",
        language="python",
        tags=["python", "example"],
    )
    
    # Add structured knowledge
    item3 = await manager.add_structured_knowledge(
        title="Python Features",
        data={
            "name": "Python",
            "version": "3.9",
            "features": ["dynamic typing", "garbage collection"],
        },
        tags=["python", "features"],
    )
    
    # Relate knowledge items
    await manager.relate_knowledge(
        source_id=item1.id,
        target_id=item2.id,
        relationship_type="has_example",
    )
    
    # Search for knowledge
    results = await manager.search_knowledge(
        query="python programming",
        k=5,
        tags=["python"],
    )
    
    # Answer a question
    result = await manager.answer_question(
        question="What is Python?",
        max_items=5,
    )
    
    # Get a knowledge network for visualization
    network = await manager.get_knowledge_network(
        item_ids=[item1.id, item2.id, item3.id],
        include_neighbors=True,
    )
```

## Knowledge Item Types

The knowledge management module supports different types of knowledge items:

- `TEXT`: Textual knowledge (articles, notes, etc.)
- `CODE`: Code snippets with language metadata
- `IMAGE`: Image data with metadata
- `AUDIO`: Audio data with metadata
- `VIDEO`: Video data with metadata
- `STRUCTURED`: Structured data (JSON, etc.)
- `GRAPH`: Graph data (nodes and edges)

## Knowledge Item Sources

Knowledge items can come from different sources:

- `USER`: Created by the user
- `SYSTEM`: Created by the system
- `AGENT`: Created by an agent
- `EXTERNAL`: Imported from an external source

## Integration with Parlant

The knowledge management functionality is integrated with the Parlant framework:

1. **Agent Tools**: The knowledge management components can be used as tools for agents
2. **Vector Database**: The knowledge base uses the vector database for efficient retrieval
3. **NLP Service**: The reasoning engine uses the NLP service for generating answers and inferences
4. **Embeddings**: The knowledge base uses embeddings for semantic search

## Future Enhancements

Potential future enhancements for the knowledge management module:

1. **Knowledge Extraction**: Automatically extract knowledge from documents and conversations
2. **Knowledge Validation**: Validate knowledge items for accuracy and consistency
3. **Knowledge Versioning**: Track changes to knowledge items over time
4. **Knowledge Sharing**: Share knowledge between agents and users
5. **Knowledge Visualization**: Visualize knowledge graphs and relationships
