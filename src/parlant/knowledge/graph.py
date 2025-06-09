"""
Knowledge graph module for Daneel.

This module provides a knowledge graph for representing relationships between knowledge items.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union, cast
import networkx as nx

from Daneel.core.common import JSONSerializable, generate_id
from Daneel.core.loggers import Logger
from Daneel.core.persistence.common import ItemNotFoundError, ObjectId, UniqueId

from Daneel.knowledge.base import KnowledgeBase, KnowledgeItem, KnowledgeItemId


class KnowledgeGraph:
    """Knowledge graph for representing relationships between knowledge items."""
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        logger: Logger,
    ):
        """Initialize the knowledge graph.
        
        Args:
            knowledge_base: Knowledge base
            logger: Logger instance
        """
        self._knowledge_base = knowledge_base
        self._logger = logger
        self._graph = nx.DiGraph()
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the knowledge graph.
        
        This loads all knowledge items and relationships from the knowledge base.
        """
        if self._initialized:
            return
            
        # Load all knowledge items
        items = await self._knowledge_base.list_items()
        
        # Add nodes to the graph
        for item in items:
            self._graph.add_node(
                item.id,
                title=item.title,
                type=item.type.value,
                source=item.source.value,
            )
            
            # Add edges for relationships
            for target_id, relationship_type in item.relationships:
                self._graph.add_edge(
                    item.id,
                    target_id,
                    type=relationship_type,
                )
                
        self._initialized = True
        self._logger.info(f"Initialized knowledge graph with {len(self._graph.nodes)} nodes and {len(self._graph.edges)} edges")
        
    async def add_relationship(
        self,
        source_id: KnowledgeItemId,
        target_id: KnowledgeItemId,
        relationship_type: str,
    ) -> None:
        """Add a relationship between knowledge items.
        
        Args:
            source_id: Source item ID
            target_id: Target item ID
            relationship_type: Type of relationship
            
        Raises:
            ItemNotFoundError: If either item is not found
        """
        # Ensure the graph is initialized
        await self.initialize()
        
        # Verify that both items exist
        try:
            source_item = await self._knowledge_base.read_item(source_id)
            target_item = await self._knowledge_base.read_item(target_id)
        except ItemNotFoundError as e:
            self._logger.error(f"Failed to add relationship: {e}")
            raise
            
        # Add the relationship to the knowledge base
        source_item.relationships.append((target_id, relationship_type))
        await self._knowledge_base.update_item(
            item_id=source_id,
            title=source_item.title,
            content=source_item.content,
            metadata=source_item.metadata,
            tags=source_item.tags,
        )
        
        # Add the edge to the graph
        self._graph.add_edge(
            source_id,
            target_id,
            type=relationship_type,
        )
        
    async def remove_relationship(
        self,
        source_id: KnowledgeItemId,
        target_id: KnowledgeItemId,
        relationship_type: Optional[str] = None,
    ) -> None:
        """Remove a relationship between knowledge items.
        
        Args:
            source_id: Source item ID
            target_id: Target item ID
            relationship_type: Type of relationship (if None, remove all relationships)
            
        Raises:
            ItemNotFoundError: If either item is not found
        """
        # Ensure the graph is initialized
        await self.initialize()
        
        # Verify that the source item exists
        try:
            source_item = await self._knowledge_base.read_item(source_id)
        except ItemNotFoundError as e:
            self._logger.error(f"Failed to remove relationship: {e}")
            raise
            
        # Remove the relationship from the knowledge base
        if relationship_type is None:
            # Remove all relationships to the target
            source_item.relationships = [
                (rel_target_id, rel_type)
                for rel_target_id, rel_type in source_item.relationships
                if rel_target_id != target_id
            ]
        else:
            # Remove specific relationship
            source_item.relationships = [
                (rel_target_id, rel_type)
                for rel_target_id, rel_type in source_item.relationships
                if rel_target_id != target_id or rel_type != relationship_type
            ]
            
        await self._knowledge_base.update_item(
            item_id=source_id,
            title=source_item.title,
            content=source_item.content,
            metadata=source_item.metadata,
            tags=source_item.tags,
        )
        
        # Remove the edge from the graph
        if relationship_type is None:
            # Remove all edges between source and target
            if self._graph.has_edge(source_id, target_id):
                self._graph.remove_edge(source_id, target_id)
        else:
            # Remove specific edge
            if self._graph.has_edge(source_id, target_id):
                edge_data = self._graph.get_edge_data(source_id, target_id)
                if edge_data.get("type") == relationship_type:
                    self._graph.remove_edge(source_id, target_id)
                    
    async def get_neighbors(
        self,
        item_id: KnowledgeItemId,
        relationship_type: Optional[str] = None,
        direction: str = "outgoing",
    ) -> List[KnowledgeItem]:
        """Get neighbors of a knowledge item.
        
        Args:
            item_id: Item ID
            relationship_type: Type of relationship (if None, get all relationships)
            direction: Direction of relationships ("outgoing", "incoming", or "both")
            
        Returns:
            List of neighboring knowledge items
            
        Raises:
            ItemNotFoundError: If the item is not found
            ValueError: If the direction is invalid
        """
        # Ensure the graph is initialized
        await self.initialize()
        
        # Verify that the item exists
        try:
            await self._knowledge_base.read_item(item_id)
        except ItemNotFoundError as e:
            self._logger.error(f"Failed to get neighbors: {e}")
            raise
            
        # Get neighboring nodes
        if direction == "outgoing":
            neighbors = self._graph.successors(item_id)
        elif direction == "incoming":
            neighbors = self._graph.predecessors(item_id)
        elif direction == "both":
            neighbors = set(self._graph.successors(item_id)) | set(self._graph.predecessors(item_id))
        else:
            raise ValueError(f"Invalid direction: {direction}")
            
        # Filter by relationship type if specified
        if relationship_type is not None:
            filtered_neighbors = []
            for neighbor in neighbors:
                if direction in ["outgoing", "both"] and self._graph.has_edge(item_id, neighbor):
                    edge_data = self._graph.get_edge_data(item_id, neighbor)
                    if edge_data.get("type") == relationship_type:
                        filtered_neighbors.append(neighbor)
                if direction in ["incoming", "both"] and self._graph.has_edge(neighbor, item_id):
                    edge_data = self._graph.get_edge_data(neighbor, item_id)
                    if edge_data.get("type") == relationship_type:
                        filtered_neighbors.append(neighbor)
            neighbors = filtered_neighbors
            
        # Get the knowledge items
        result = []
        for neighbor_id in neighbors:
            try:
                item = await self._knowledge_base.read_item(neighbor_id)
                result.append(item)
            except ItemNotFoundError:
                # Skip items that no longer exist
                pass
                
        return result
        
    async def get_path(
        self,
        source_id: KnowledgeItemId,
        target_id: KnowledgeItemId,
    ) -> List[Tuple[KnowledgeItem, str]]:
        """Get the shortest path between two knowledge items.
        
        Args:
            source_id: Source item ID
            target_id: Target item ID
            
        Returns:
            List of knowledge items and relationship types along the path
            
        Raises:
            ItemNotFoundError: If either item is not found
            nx.NetworkXNoPath: If no path exists
        """
        # Ensure the graph is initialized
        await self.initialize()
        
        # Verify that both items exist
        try:
            await self._knowledge_base.read_item(source_id)
            await self._knowledge_base.read_item(target_id)
        except ItemNotFoundError as e:
            self._logger.error(f"Failed to get path: {e}")
            raise
            
        # Get the shortest path
        try:
            path = nx.shortest_path(self._graph, source_id, target_id)
        except nx.NetworkXNoPath:
            self._logger.warning(f"No path from {source_id} to {target_id}")
            raise
            
        # Get the knowledge items and relationship types
        result = []
        for i in range(len(path) - 1):
            source_node = path[i]
            target_node = path[i + 1]
            edge_data = self._graph.get_edge_data(source_node, target_node)
            relationship_type = edge_data.get("type", "related_to")
            
            try:
                item = await self._knowledge_base.read_item(source_node)
                result.append((item, relationship_type))
            except ItemNotFoundError:
                # Skip items that no longer exist
                pass
                
        # Add the target item
        try:
            item = await self._knowledge_base.read_item(target_id)
            result.append((item, ""))
        except ItemNotFoundError:
            # Skip if the target no longer exists
            pass
            
        return result
        
    async def get_subgraph(
        self,
        item_ids: List[KnowledgeItemId],
        include_neighbors: bool = False,
    ) -> Dict[str, Any]:
        """Get a subgraph of the knowledge graph.
        
        Args:
            item_ids: Item IDs to include
            include_neighbors: Whether to include neighbors of the specified items
            
        Returns:
            Dictionary representation of the subgraph
        """
        # Ensure the graph is initialized
        await self.initialize()
        
        # Create the subgraph
        nodes = set(item_ids)
        
        if include_neighbors:
            for item_id in item_ids:
                if self._graph.has_node(item_id):
                    nodes.update(self._graph.successors(item_id))
                    nodes.update(self._graph.predecessors(item_id))
                    
        subgraph = self._graph.subgraph(nodes)
        
        # Convert to dictionary representation
        result = {
            "nodes": [],
            "edges": [],
        }
        
        for node in subgraph.nodes:
            node_data = subgraph.nodes[node]
            result["nodes"].append({
                "id": node,
                "title": node_data.get("title", ""),
                "type": node_data.get("type", ""),
                "source": node_data.get("source", ""),
            })
            
        for source, target, data in subgraph.edges(data=True):
            result["edges"].append({
                "source": source,
                "target": target,
                "type": data.get("type", "related_to"),
            })
            
        return result
