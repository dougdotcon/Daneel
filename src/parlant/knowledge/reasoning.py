"""
Knowledge reasoning module for Parlant.

This module provides reasoning capabilities over the knowledge base.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union, cast
from dataclasses import dataclass, field

from parlant.core.loggers import Logger
from parlant.core.nlp.service import NLPService
from parlant.core.nlp.generation_info import GenerationInfo

from parlant.knowledge.base import KnowledgeBase, KnowledgeItem, KnowledgeItemId, KnowledgeItemType
from parlant.knowledge.graph import KnowledgeGraph


@dataclass
class ReasoningResult:
    """Result of a reasoning operation."""
    
    answer: str
    confidence: float
    supporting_items: List[KnowledgeItem] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)
    generation_info: Optional[GenerationInfo] = None


class KnowledgeReasoner:
    """Reasoner for knowledge base."""
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        knowledge_graph: KnowledgeGraph,
        nlp_service: NLPService,
        logger: Logger,
    ):
        """Initialize the knowledge reasoner.
        
        Args:
            knowledge_base: Knowledge base
            knowledge_graph: Knowledge graph
            nlp_service: NLP service
            logger: Logger instance
        """
        self._knowledge_base = knowledge_base
        self._knowledge_graph = knowledge_graph
        self._nlp_service = nlp_service
        self._logger = logger
        
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
        # Search for relevant knowledge items
        search_results = await self._knowledge_base.search_items(
            query=question,
            k=max_items,
        )
        
        if not search_results:
            self._logger.warning(f"No knowledge items found for question: {question}")
            return ReasoningResult(
                answer="I don't have enough information to answer this question.",
                confidence=0.0,
                supporting_items=[],
                reasoning_steps=["No relevant knowledge items found."],
            )
            
        # Extract the knowledge items and their scores
        items = [item for item, _ in search_results]
        scores = [score for _, score in search_results]
        
        # Format the context for the LLM
        context = self._format_context(items)
        
        # Generate the answer
        prompt = self._create_reasoning_prompt(question, context)
        
        generator = await self._nlp_service.get_generator()
        generation_result = await generator.generate(prompt)
        
        # Parse the response
        answer, confidence, reasoning_steps = self._parse_reasoning_response(generation_result.text)
        
        return ReasoningResult(
            answer=answer,
            confidence=confidence,
            supporting_items=items,
            reasoning_steps=reasoning_steps,
            generation_info=generation_result.generation_info,
        )
        
    async def generate_inference(
        self,
        item_id: KnowledgeItemId,
        max_related_items: int = 3,
    ) -> ReasoningResult:
        """Generate an inference about a knowledge item.
        
        Args:
            item_id: Knowledge item ID
            max_related_items: Maximum number of related items to consider
            
        Returns:
            Reasoning result
        """
        # Get the knowledge item
        item = await self._knowledge_base.read_item(item_id)
        
        # Get related items from the knowledge graph
        related_items = await self._knowledge_graph.get_neighbors(
            item_id=item_id,
            direction="both",
        )
        
        # Limit the number of related items
        related_items = related_items[:max_related_items]
        
        # Format the context for the LLM
        items = [item] + related_items
        context = self._format_context(items)
        
        # Generate the inference
        prompt = self._create_inference_prompt(item.title, context)
        
        generator = await self._nlp_service.get_generator()
        generation_result = await generator.generate(prompt)
        
        # Parse the response
        inference, confidence, reasoning_steps = self._parse_reasoning_response(generation_result.text)
        
        return ReasoningResult(
            answer=inference,
            confidence=confidence,
            supporting_items=items,
            reasoning_steps=reasoning_steps,
            generation_info=generation_result.generation_info,
        )
        
    async def validate_relationship(
        self,
        source_id: KnowledgeItemId,
        target_id: KnowledgeItemId,
        relationship_type: str,
    ) -> ReasoningResult:
        """Validate a relationship between knowledge items.
        
        Args:
            source_id: Source item ID
            target_id: Target item ID
            relationship_type: Type of relationship
            
        Returns:
            Reasoning result
        """
        # Get the knowledge items
        source_item = await self._knowledge_base.read_item(source_id)
        target_item = await self._knowledge_base.read_item(target_id)
        
        # Format the context for the LLM
        context = self._format_context([source_item, target_item])
        
        # Generate the validation
        prompt = self._create_validation_prompt(
            source_item.title,
            target_item.title,
            relationship_type,
            context,
        )
        
        generator = await self._nlp_service.get_generator()
        generation_result = await generator.generate(prompt)
        
        # Parse the response
        validation, confidence, reasoning_steps = self._parse_reasoning_response(generation_result.text)
        
        return ReasoningResult(
            answer=validation,
            confidence=confidence,
            supporting_items=[source_item, target_item],
            reasoning_steps=reasoning_steps,
            generation_info=generation_result.generation_info,
        )
        
    def _format_context(self, items: List[KnowledgeItem]) -> str:
        """Format knowledge items as context for the LLM.
        
        Args:
            items: Knowledge items
            
        Returns:
            Formatted context
        """
        context_parts = []
        
        for i, item in enumerate(items):
            context_parts.append(f"[{i+1}] {item.title}: {item.content}")
            
        return "\n\n".join(context_parts)
        
    def _create_reasoning_prompt(self, question: str, context: str) -> str:
        """Create a prompt for reasoning about a question.
        
        Args:
            question: Question to answer
            context: Context information
            
        Returns:
            Reasoning prompt
        """
        return f"""You are a knowledge reasoning system. Answer the question based on the provided context.
If the context doesn't contain enough information to answer the question, say so.

Context:
{context}

Question: {question}

Provide your answer in the following format:
Answer: [Your answer]
Confidence: [A number between 0 and 1 indicating your confidence]
Reasoning:
- [Step 1 of your reasoning]
- [Step 2 of your reasoning]
- ...

Answer:"""
        
    def _create_inference_prompt(self, title: str, context: str) -> str:
        """Create a prompt for generating an inference.
        
        Args:
            title: Title of the knowledge item
            context: Context information
            
        Returns:
            Inference prompt
        """
        return f"""You are a knowledge reasoning system. Generate an inference about the item "{title}" based on the provided context.

Context:
{context}

Provide your inference in the following format:
Inference: [Your inference]
Confidence: [A number between 0 and 1 indicating your confidence]
Reasoning:
- [Step 1 of your reasoning]
- [Step 2 of your reasoning]
- ...

Inference:"""
        
    def _create_validation_prompt(
        self,
        source_title: str,
        target_title: str,
        relationship_type: str,
        context: str,
    ) -> str:
        """Create a prompt for validating a relationship.
        
        Args:
            source_title: Title of the source item
            target_title: Title of the target item
            relationship_type: Type of relationship
            context: Context information
            
        Returns:
            Validation prompt
        """
        return f"""You are a knowledge reasoning system. Validate whether the relationship "{relationship_type}" exists between "{source_title}" and "{target_title}" based on the provided context.

Context:
{context}

Provide your validation in the following format:
Validation: [Yes/No/Maybe]
Confidence: [A number between 0 and 1 indicating your confidence]
Reasoning:
- [Step 1 of your reasoning]
- [Step 2 of your reasoning]
- ...

Validation:"""
        
    def _parse_reasoning_response(self, response: str) -> Tuple[str, float, List[str]]:
        """Parse a reasoning response from the LLM.
        
        Args:
            response: LLM response
            
        Returns:
            Tuple of (answer, confidence, reasoning_steps)
        """
        answer = ""
        confidence = 0.0
        reasoning_steps = []
        
        # Extract the answer
        answer_lines = []
        confidence_line = ""
        reasoning_lines = []
        
        in_reasoning = False
        
        for line in response.strip().split("\n"):
            line = line.strip()
            
            if line.startswith("Answer:") or line.startswith("Inference:") or line.startswith("Validation:"):
                answer_lines.append(line.split(":", 1)[1].strip())
            elif line.startswith("Confidence:"):
                confidence_line = line.split(":", 1)[1].strip()
            elif line.startswith("Reasoning:"):
                in_reasoning = True
            elif in_reasoning and line.startswith("-"):
                reasoning_lines.append(line[1:].strip())
            elif in_reasoning and line:
                reasoning_lines.append(line)
                
        # Combine answer lines
        answer = " ".join(answer_lines)
        
        # Parse confidence
        try:
            confidence = float(confidence_line)
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        except (ValueError, TypeError):
            confidence = 0.5  # Default confidence
            
        # Process reasoning steps
        reasoning_steps = [step for step in reasoning_lines if step]
        
        return answer, confidence, reasoning_steps
