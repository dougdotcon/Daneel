"""
Task delegation and coordination for Parlant.

This module provides functionality for delegating and coordinating tasks between agents.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid
import json

from parlant.core.common import JSONSerializable, generate_id
from parlant.core.agents import Agent, AgentId, AgentStore
from parlant.core.loggers import Logger
from parlant.core.async_utils import ReaderWriterLock

from parlant.collaborative.protocol import (
    AgentCommunicator,
    AgentMessage,
    MessageBus,
    MessageType,
    MessagePriority,
)
from parlant.collaborative.team import Team, TeamId, TeamManager, TeamRole


class TaskStatus(str, Enum):
    """Status of a task."""
    
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Priority of a task."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskId(str):
    """Task ID."""
    pass


@dataclass
class TaskAssignment:
    """Assignment of a task to an agent."""
    
    agent_id: AgentId
    assignment_time: datetime
    status: TaskStatus
    progress: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Task:
    """Task that can be assigned to agents."""
    
    id: TaskId
    title: str
    description: str
    creation_utc: datetime
    status: TaskStatus
    priority: TaskPriority
    creator_id: AgentId
    team_id: Optional[TeamId] = None
    parent_task_id: Optional[TaskId] = None
    subtasks: List[TaskId] = field(default_factory=list)
    assignments: Dict[AgentId, TaskAssignment] = field(default_factory=dict)
    dependencies: List[TaskId] = field(default_factory=list)
    deadline: Optional[datetime] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class TaskManager:
    """Manager for tasks."""
    
    def __init__(
        self,
        agent_store: AgentStore,
        team_manager: TeamManager,
        message_bus: MessageBus,
        logger: Logger,
    ):
        """Initialize the task manager.
        
        Args:
            agent_store: Agent store
            team_manager: Team manager
            message_bus: Message bus for agent communication
            logger: Logger instance
        """
        self._agent_store = agent_store
        self._team_manager = team_manager
        self._message_bus = message_bus
        self._logger = logger
        self._tasks: Dict[TaskId, Task] = {}
        self._agent_tasks: Dict[AgentId, Set[TaskId]] = {}
        self._lock = ReaderWriterLock()
        
    async def create_task(
        self,
        title: str,
        description: str,
        creator_id: AgentId,
        priority: TaskPriority = TaskPriority.NORMAL,
        team_id: Optional[TeamId] = None,
        parent_task_id: Optional[TaskId] = None,
        dependencies: Optional[List[TaskId]] = None,
        deadline: Optional[datetime] = None,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> Task:
        """Create a new task.
        
        Args:
            title: Task title
            description: Task description
            creator_id: Creator agent ID
            priority: Task priority
            team_id: Team ID (if the task is for a team)
            parent_task_id: Parent task ID (if this is a subtask)
            dependencies: Task dependencies
            deadline: Task deadline
            metadata: Additional metadata
            
        Returns:
            Created task
        """
        async with self._lock.writer_lock:
            task_id = TaskId(generate_id())
            
            task = Task(
                id=task_id,
                title=title,
                description=description,
                creation_utc=datetime.now(timezone.utc),
                status=TaskStatus.PENDING,
                priority=priority,
                creator_id=creator_id,
                team_id=team_id,
                parent_task_id=parent_task_id,
                dependencies=dependencies or [],
                deadline=deadline,
                metadata=metadata or {},
            )
            
            self._tasks[task_id] = task
            
            # Add as subtask to parent
            if parent_task_id and parent_task_id in self._tasks:
                self._tasks[parent_task_id].subtasks.append(task_id)
                
        self._logger.info(f"Created task: {title} ({task_id})")
        
        return task
        
    async def get_task(self, task_id: TaskId) -> Optional[Task]:
        """Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        async with self._lock.reader_lock:
            return self._tasks.get(task_id)
            
    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        team_id: Optional[TeamId] = None,
        agent_id: Optional[AgentId] = None,
    ) -> List[Task]:
        """List tasks with optional filtering.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            team_id: Filter by team ID
            agent_id: Filter by assigned agent ID
            
        Returns:
            List of tasks
        """
        async with self._lock.reader_lock:
            tasks = list(self._tasks.values())
            
            # Apply filters
            if status:
                tasks = [task for task in tasks if task.status == status]
                
            if priority:
                tasks = [task for task in tasks if task.priority == priority]
                
            if team_id:
                tasks = [task for task in tasks if task.team_id == team_id]
                
            if agent_id:
                tasks = [task for task in tasks if agent_id in task.assignments]
                
            return tasks
            
    async def assign_task(
        self,
        task_id: TaskId,
        agent_id: AgentId,
    ) -> bool:
        """Assign a task to an agent.
        
        Args:
            task_id: Task ID
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        # Verify that the agent exists
        agent = await self._agent_store.get_agent(agent_id)
        if not agent:
            self._logger.error(f"Agent not found: {agent_id}")
            return False
            
        async with self._lock.writer_lock:
            # Verify that the task exists
            task = self._tasks.get(task_id)
            if not task:
                self._logger.error(f"Task not found: {task_id}")
                return False
                
            # Verify that the task is not already completed or cancelled
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                self._logger.error(f"Cannot assign task {task_id}: task is {task.status}")
                return False
                
            # Assign the task
            task.assignments[agent_id] = TaskAssignment(
                agent_id=agent_id,
                assignment_time=datetime.now(timezone.utc),
                status=TaskStatus.ASSIGNED,
            )
            
            # Update task status
            task.status = TaskStatus.ASSIGNED
            
            # Update agent tasks
            if agent_id not in self._agent_tasks:
                self._agent_tasks[agent_id] = set()
                
            self._agent_tasks[agent_id].add(task_id)
            
        self._logger.info(f"Assigned task {task_id} to agent {agent_id}")
        
        # Notify the agent
        await self._notify_task_assignment(task, agent_id)
        
        return True
        
    async def update_task_status(
        self,
        task_id: TaskId,
        agent_id: AgentId,
        status: TaskStatus,
        progress: Optional[float] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update the status of a task.
        
        Args:
            task_id: Task ID
            agent_id: Agent ID
            status: New status
            progress: Task progress (0.0 to 1.0)
            result: Task result (if completed)
            error: Error message (if failed)
            
        Returns:
            True if successful, False otherwise
        """
        async with self._lock.writer_lock:
            # Verify that the task exists
            task = self._tasks.get(task_id)
            if not task:
                self._logger.error(f"Task not found: {task_id}")
                return False
                
            # Verify that the agent is assigned to the task
            if agent_id not in task.assignments:
                self._logger.error(f"Agent {agent_id} is not assigned to task {task_id}")
                return False
                
            # Update the assignment
            assignment = task.assignments[agent_id]
            assignment.status = status
            
            if progress is not None:
                assignment.progress = max(0.0, min(1.0, progress))
                
            if result is not None:
                assignment.result = result
                
            if error is not None:
                assignment.error = error
                
            # Update task status based on assignments
            if status == TaskStatus.COMPLETED:
                # Check if all assignments are completed
                if all(a.status == TaskStatus.COMPLETED for a in task.assignments.values()):
                    task.status = TaskStatus.COMPLETED
            elif status == TaskStatus.FAILED:
                # If any assignment fails, the task fails
                task.status = TaskStatus.FAILED
            elif status == TaskStatus.IN_PROGRESS:
                task.status = TaskStatus.IN_PROGRESS
                
        self._logger.info(f"Updated task {task_id} status to {status} by agent {agent_id}")
        
        # Notify the task creator
        await self._notify_task_status_update(task, agent_id, status)
        
        return True
        
    async def cancel_task(
        self,
        task_id: TaskId,
        canceller_id: AgentId,
    ) -> bool:
        """Cancel a task.
        
        Args:
            task_id: Task ID
            canceller_id: Agent ID of the canceller
            
        Returns:
            True if successful, False otherwise
        """
        async with self._lock.writer_lock:
            # Verify that the task exists
            task = self._tasks.get(task_id)
            if not task:
                self._logger.error(f"Task not found: {task_id}")
                return False
                
            # Verify that the task is not already completed or cancelled
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                self._logger.error(f"Cannot cancel task {task_id}: task is {task.status}")
                return False
                
            # Cancel the task
            task.status = TaskStatus.CANCELLED
            
            # Update all assignments
            for agent_id, assignment in task.assignments.items():
                assignment.status = TaskStatus.CANCELLED
                
                # Notify the assigned agent
                await self._notify_task_cancellation(task, agent_id, canceller_id)
                
        self._logger.info(f"Cancelled task {task_id} by agent {canceller_id}")
        
        return True
        
    async def get_agent_tasks(
        self,
        agent_id: AgentId,
        status: Optional[TaskStatus] = None,
    ) -> List[Task]:
        """Get all tasks assigned to an agent.
        
        Args:
            agent_id: Agent ID
            status: Filter by status
            
        Returns:
            List of tasks
        """
        async with self._lock.reader_lock:
            task_ids = self._agent_tasks.get(agent_id, set())
            tasks = [self._tasks[task_id] for task_id in task_ids if task_id in self._tasks]
            
            # Apply status filter
            if status:
                tasks = [task for task in tasks if task.status == status]
                
            return tasks
            
    async def _notify_task_assignment(
        self,
        task: Task,
        agent_id: AgentId,
    ) -> None:
        """Notify an agent of a task assignment.
        
        Args:
            task: Task
            agent_id: Agent ID
        """
        # Create a communicator for the task creator
        communicator = AgentCommunicator(
            agent_id=task.creator_id,
            message_bus=self._message_bus,
        )
        
        # Create task assignment message
        content = json.dumps({
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "deadline": task.deadline.isoformat() if task.deadline else None,
        })
        
        # Send the message
        await communicator.send_message(
            receiver_id=agent_id,
            message_type=MessageType.TASK_ASSIGNMENT,
            content=content,
            priority=MessagePriority.HIGH,
            metadata={"task_id": task.id},
        )
        
    async def _notify_task_status_update(
        self,
        task: Task,
        agent_id: AgentId,
        status: TaskStatus,
    ) -> None:
        """Notify the task creator of a status update.
        
        Args:
            task: Task
            agent_id: Agent ID
            status: New status
        """
        # Create a communicator for the agent
        communicator = AgentCommunicator(
            agent_id=agent_id,
            message_bus=self._message_bus,
        )
        
        # Create task status message
        content = json.dumps({
            "task_id": task.id,
            "status": status.value,
            "progress": task.assignments[agent_id].progress,
            "result": task.assignments[agent_id].result,
            "error": task.assignments[agent_id].error,
        })
        
        # Send the message
        await communicator.send_message(
            receiver_id=task.creator_id,
            message_type=MessageType.TASK_STATUS,
            content=content,
            priority=MessagePriority.NORMAL,
            metadata={"task_id": task.id},
        )
        
    async def _notify_task_cancellation(
        self,
        task: Task,
        agent_id: AgentId,
        canceller_id: AgentId,
    ) -> None:
        """Notify an agent of a task cancellation.
        
        Args:
            task: Task
            agent_id: Agent ID
            canceller_id: Agent ID of the canceller
        """
        # Create a communicator for the canceller
        communicator = AgentCommunicator(
            agent_id=canceller_id,
            message_bus=self._message_bus,
        )
        
        # Create task cancellation message
        content = json.dumps({
            "task_id": task.id,
            "reason": "Task cancelled",
        })
        
        # Send the message
        await communicator.send_message(
            receiver_id=agent_id,
            message_type=MessageType.TASK_STATUS,
            content=content,
            priority=MessagePriority.HIGH,
            metadata={"task_id": task.id, "status": TaskStatus.CANCELLED.value},
        )
