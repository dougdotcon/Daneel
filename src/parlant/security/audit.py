"""
Audit logging for Parlant.

This module provides functionality for audit logging and monitoring.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import json
import uuid
import os
import asyncio
from contextlib import asynccontextmanager

from parlant.core.common import JSONSerializable, generate_id
from parlant.core.loggers import Logger
from parlant.core.async_utils import ReaderWriterLock
from parlant.core.persistence.document_database import DocumentCollection, DocumentDatabase
from parlant.core.persistence.common import ItemNotFoundError, ObjectId, UniqueId, Where

from parlant.security.auth import User, UserId


class AuditEventType(str, Enum):
    """Types of audit events."""
    
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    
    SYSTEM_ERROR = "system_error"
    SECURITY_VIOLATION = "security_violation"
    
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    
    CUSTOM = "custom"


class AuditEventSeverity(str, Enum):
    """Severity levels for audit events."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEventId(str):
    """Audit event ID."""
    pass


@dataclass
class AuditEvent:
    """Audit event for logging."""
    
    id: AuditEventId
    type: AuditEventType
    timestamp: datetime
    user_id: Optional[UserId]
    resource: str
    action: str
    status: str
    severity: AuditEventSeverity
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class _AuditEventDocument(Dict[str, Any]):
    """Audit event document for storage."""
    pass


class AuditLogger:
    """Logger for audit events."""
    
    VERSION = "0.1.0"
    
    def __init__(
        self,
        document_db: DocumentDatabase,
        logger: Logger,
        retention_days: int = 90,
    ):
        """Initialize the audit logger.
        
        Args:
            document_db: Document database
            logger: Logger instance
            retention_days: Number of days to retain audit events
        """
        self._document_db = document_db
        self._logger = logger
        self._retention_days = retention_days
        
        self._event_collection: Optional[DocumentCollection[_AuditEventDocument]] = None
        self._lock = ReaderWriterLock()
        
        # Background task for cleanup
        self._cleanup_task = None
        
    async def __aenter__(self) -> AuditLogger:
        """Enter the context manager."""
        self._event_collection = await self._document_db.get_or_create_collection(
            name="audit_events",
            schema=_AuditEventDocument,
        )
        
        # Start the cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_old_events())
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        # Cancel the cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
    def _serialize_event(self, event: AuditEvent) -> _AuditEventDocument:
        """Serialize an audit event.
        
        Args:
            event: Audit event to serialize
            
        Returns:
            Serialized audit event document
        """
        return {
            "id": event.id,
            "version": self.VERSION,
            "type": event.type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "resource": event.resource,
            "action": event.action,
            "status": event.status,
            "severity": event.severity.value,
            "details": event.details,
            "ip_address": event.ip_address,
            "session_id": event.session_id,
            "metadata": event.metadata,
        }
        
    def _deserialize_event(self, document: _AuditEventDocument) -> AuditEvent:
        """Deserialize an audit event document.
        
        Args:
            document: Audit event document
            
        Returns:
            Deserialized audit event
        """
        return AuditEvent(
            id=AuditEventId(document["id"]),
            type=AuditEventType(document["type"]),
            timestamp=datetime.fromisoformat(document["timestamp"]),
            user_id=UserId(document["user_id"]) if document.get("user_id") else None,
            resource=document["resource"],
            action=document["action"],
            status=document["status"],
            severity=AuditEventSeverity(document["severity"]),
            details=document["details"],
            ip_address=document.get("ip_address"),
            session_id=document.get("session_id"),
            metadata=document.get("metadata", {}),
        )
        
    async def log_event(
        self,
        type: AuditEventType,
        user_id: Optional[UserId],
        resource: str,
        action: str,
        status: str,
        severity: AuditEventSeverity = AuditEventSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditEvent:
        """Log an audit event.
        
        Args:
            type: Event type
            user_id: User ID (if applicable)
            resource: Resource being accessed or modified
            action: Action being performed
            status: Status of the action (e.g., "success", "failure")
            severity: Event severity
            details: Additional details about the event
            ip_address: IP address of the user
            session_id: Session ID
            
        Returns:
            Created audit event
        """
        # Create the audit event
        event = AuditEvent(
            id=AuditEventId(generate_id()),
            type=type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            resource=resource,
            action=action,
            status=status,
            severity=severity,
            details=details or {},
            ip_address=ip_address,
            session_id=session_id,
        )
        
        # Save the event
        await self._event_collection.insert_one(
            document=self._serialize_event(event)
        )
        
        # Log the event
        log_message = f"Audit: {event.type} - {event.resource} - {event.action} - {event.status}"
        if event.severity == AuditEventSeverity.INFO:
            self._logger.info(log_message)
        elif event.severity == AuditEventSeverity.WARNING:
            self._logger.warning(log_message)
        elif event.severity == AuditEventSeverity.ERROR:
            self._logger.error(log_message)
        elif event.severity == AuditEventSeverity.CRITICAL:
            self._logger.critical(log_message)
            
        return event
        
    async def get_event(
        self,
        event_id: AuditEventId,
    ) -> Optional[AuditEvent]:
        """Get an audit event by ID.
        
        Args:
            event_id: Audit event ID
            
        Returns:
            Audit event if found, None otherwise
        """
        async with self._lock.reader_lock:
            # Get the event
            event_doc = await self._event_collection.find_one(
                filters={"id": {"$eq": event_id}}
            )
            
            if not event_doc:
                return None
                
            return self._deserialize_event(event_doc)
            
    async def search_events(
        self,
        type: Optional[AuditEventType] = None,
        user_id: Optional[UserId] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[AuditEventSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """Search for audit events.
        
        Args:
            type: Filter by event type
            user_id: Filter by user ID
            resource: Filter by resource
            action: Filter by action
            status: Filter by status
            severity: Filter by severity
            start_time: Filter by start time
            end_time: Filter by end time
            ip_address: Filter by IP address
            session_id: Filter by session ID
            limit: Maximum number of events to return
            offset: Offset for pagination
            
        Returns:
            List of audit events
        """
        async with self._lock.reader_lock:
            # Build filters
            filters = {}
            
            if type is not None:
                filters["type"] = {"$eq": type.value}
                
            if user_id is not None:
                filters["user_id"] = {"$eq": user_id}
                
            if resource is not None:
                filters["resource"] = {"$eq": resource}
                
            if action is not None:
                filters["action"] = {"$eq": action}
                
            if status is not None:
                filters["status"] = {"$eq": status}
                
            if severity is not None:
                filters["severity"] = {"$eq": severity.value}
                
            if start_time is not None or end_time is not None:
                filters["timestamp"] = {}
                
                if start_time is not None:
                    filters["timestamp"]["$gte"] = start_time.isoformat()
                    
                if end_time is not None:
                    filters["timestamp"]["$lte"] = end_time.isoformat()
                    
            if ip_address is not None:
                filters["ip_address"] = {"$eq": ip_address}
                
            if session_id is not None:
                filters["session_id"] = {"$eq": session_id}
                
            # Get events
            event_docs = await self._event_collection.find(
                filters=filters,
                sort=[("timestamp", -1)],
                limit=limit,
                skip=offset,
            )
            
            return [self._deserialize_event(doc) for doc in event_docs]
            
    async def count_events(
        self,
        type: Optional[AuditEventType] = None,
        user_id: Optional[UserId] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[AuditEventSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        """Count audit events.
        
        Args:
            type: Filter by event type
            user_id: Filter by user ID
            resource: Filter by resource
            action: Filter by action
            status: Filter by status
            severity: Filter by severity
            start_time: Filter by start time
            end_time: Filter by end time
            ip_address: Filter by IP address
            session_id: Filter by session ID
            
        Returns:
            Number of audit events
        """
        async with self._lock.reader_lock:
            # Build filters
            filters = {}
            
            if type is not None:
                filters["type"] = {"$eq": type.value}
                
            if user_id is not None:
                filters["user_id"] = {"$eq": user_id}
                
            if resource is not None:
                filters["resource"] = {"$eq": resource}
                
            if action is not None:
                filters["action"] = {"$eq": action}
                
            if status is not None:
                filters["status"] = {"$eq": status}
                
            if severity is not None:
                filters["severity"] = {"$eq": severity.value}
                
            if start_time is not None or end_time is not None:
                filters["timestamp"] = {}
                
                if start_time is not None:
                    filters["timestamp"]["$gte"] = start_time.isoformat()
                    
                if end_time is not None:
                    filters["timestamp"]["$lte"] = end_time.isoformat()
                    
            if ip_address is not None:
                filters["ip_address"] = {"$eq": ip_address}
                
            if session_id is not None:
                filters["session_id"] = {"$eq": session_id}
                
            # Count events
            return await self._event_collection.count(filters=filters)
            
    async def _cleanup_old_events(self):
        """Clean up old audit events."""
        while True:
            try:
                # Sleep for a day
                await asyncio.sleep(24 * 60 * 60)
                
                # Calculate the cutoff date
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=self._retention_days)
                
                # Delete old events
                result = await self._event_collection.delete_many(
                    filters={"timestamp": {"$lt": cutoff_date.isoformat()}}
                )
                
                if result.deleted_count > 0:
                    self._logger.info(f"Cleaned up {result.deleted_count} old audit events")
                    
            except asyncio.CancelledError:
                # Task was cancelled
                break
            except Exception as e:
                self._logger.error(f"Error cleaning up old audit events: {e}")
                
    @asynccontextmanager
    async def audit_context(
        self,
        type: AuditEventType,
        user_id: Optional[UserId],
        resource: str,
        action: str,
        severity: AuditEventSeverity = AuditEventSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Context manager for auditing operations.
        
        Args:
            type: Event type
            user_id: User ID (if applicable)
            resource: Resource being accessed or modified
            action: Action being performed
            severity: Event severity
            details: Additional details about the event
            ip_address: IP address of the user
            session_id: Session ID
            
        Yields:
            None
        """
        try:
            # Yield control to the context block
            yield
            
            # Log success event
            await self.log_event(
                type=type,
                user_id=user_id,
                resource=resource,
                action=action,
                status="success",
                severity=severity,
                details=details,
                ip_address=ip_address,
                session_id=session_id,
            )
            
        except Exception as e:
            # Log failure event
            error_details = details.copy() if details else {}
            error_details["error"] = str(e)
            
            await self.log_event(
                type=type,
                user_id=user_id,
                resource=resource,
                action=action,
                status="failure",
                severity=AuditEventSeverity.ERROR,
                details=error_details,
                ip_address=ip_address,
                session_id=session_id,
            )
            
            # Re-raise the exception
            raise
