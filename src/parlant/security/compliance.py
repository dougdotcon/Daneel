"""
Compliance frameworks for Parlant.

This module provides functionality for regulatory compliance.
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
from parlant.security.audit import AuditLogger, AuditEventType, AuditEventSeverity
from parlant.security.privacy import PrivacyManager


class ComplianceFramework(str, Enum):
    """Types of compliance frameworks."""

    GDPR = "gdpr"
    HIPAA = "hipaa"
    CCPA = "ccpa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    CUSTOM = "custom"


class ComplianceRequirementId(str):
    """Compliance requirement ID."""
    pass


class ComplianceRequirementStatus(str, Enum):
    """Status of compliance requirements."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"


@dataclass
class ComplianceRequirement:
    """Compliance requirement."""

    id: ComplianceRequirementId
    framework: ComplianceFramework
    code: str
    name: str
    description: str
    status: ComplianceRequirementStatus
    last_assessment: datetime
    next_assessment: datetime
    responsible_party: Optional[str] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class _ComplianceRequirementDocument(Dict[str, Any]):
    """Compliance requirement document for storage."""
    pass


@dataclass
class DataSubjectRequest:
    """Data subject request (e.g., GDPR right to access, right to be forgotten)."""

    id: str
    user_id: UserId
    request_type: str
    status: str
    creation_utc: datetime
    completion_utc: Optional[datetime] = None
    notes: Optional[str] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class _DataSubjectRequestDocument(Dict[str, Any]):
    """Data subject request document for storage."""
    pass


class ComplianceManager:
    """Manager for regulatory compliance."""

    VERSION = "0.1.0"

    def __init__(
        self,
        document_db: DocumentDatabase,
        audit_logger: AuditLogger,
        privacy_manager: PrivacyManager,
        logger: Logger,
    ):
        """Initialize the compliance manager.

        Args:
            document_db: Document database
            audit_logger: Audit logger
            privacy_manager: Privacy manager
            logger: Logger instance
        """
        self._document_db = document_db
        self._audit_logger = audit_logger
        self._privacy_manager = privacy_manager
        self._logger = logger

        self._requirement_collection: Optional[DocumentCollection[_ComplianceRequirementDocument]] = None
        self._request_collection: Optional[DocumentCollection[_DataSubjectRequestDocument]] = None
        self._lock = ReaderWriterLock()

        # Register default compliance frameworks
        self._gdpr_requirements = []
        self._hipaa_requirements = []
        self._ccpa_requirements = []
        self._soc2_requirements = []
        self._pci_dss_requirements = []

    async def __aenter__(self) -> ComplianceManager:
        """Enter the context manager."""
        self._requirement_collection = await self._document_db.get_or_create_collection(
            name="compliance_requirements",
            schema=_ComplianceRequirementDocument,
        )

        self._request_collection = await self._document_db.get_or_create_collection(
            name="data_subject_requests",
            schema=_DataSubjectRequestDocument,
        )

        # Initialize default requirements
        await self._initialize_default_requirements()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass

    def _serialize_requirement(self, requirement: ComplianceRequirement) -> _ComplianceRequirementDocument:
        """Serialize a compliance requirement.

        Args:
            requirement: Compliance requirement to serialize

        Returns:
            Serialized compliance requirement document
        """
        return {
            "id": requirement.id,
            "version": self.VERSION,
            "framework": requirement.framework.value,
            "code": requirement.code,
            "name": requirement.name,
            "description": requirement.description,
            "status": requirement.status.value,
            "last_assessment": requirement.last_assessment.isoformat(),
            "next_assessment": requirement.next_assessment.isoformat(),
            "responsible_party": requirement.responsible_party,
            "evidence": requirement.evidence,
            "notes": requirement.notes,
            "metadata": requirement.metadata,
        }

    def _deserialize_requirement(self, document: _ComplianceRequirementDocument) -> ComplianceRequirement:
        """Deserialize a compliance requirement document.

        Args:
            document: Compliance requirement document

        Returns:
            Deserialized compliance requirement
        """
        return ComplianceRequirement(
            id=ComplianceRequirementId(document["id"]),
            framework=ComplianceFramework(document["framework"]),
            code=document["code"],
            name=document["name"],
            description=document["description"],
            status=ComplianceRequirementStatus(document["status"]),
            last_assessment=datetime.fromisoformat(document["last_assessment"]),
            next_assessment=datetime.fromisoformat(document["next_assessment"]),
            responsible_party=document.get("responsible_party"),
            evidence=document.get("evidence"),
            notes=document.get("notes"),
            metadata=document.get("metadata", {}),
        )

    def _serialize_request(self, request: DataSubjectRequest) -> _DataSubjectRequestDocument:
        """Serialize a data subject request.

        Args:
            request: Data subject request to serialize

        Returns:
            Serialized data subject request document
        """
        return {
            "id": request.id,
            "version": self.VERSION,
            "user_id": request.user_id,
            "request_type": request.request_type,
            "status": request.status,
            "creation_utc": request.creation_utc.isoformat(),
            "completion_utc": request.completion_utc.isoformat() if request.completion_utc else None,
            "notes": request.notes,
            "metadata": request.metadata,
        }

    def _deserialize_request(self, document: _DataSubjectRequestDocument) -> DataSubjectRequest:
        """Deserialize a data subject request document.

        Args:
            document: Data subject request document

        Returns:
            Deserialized data subject request
        """
        return DataSubjectRequest(
            id=document["id"],
            user_id=UserId(document["user_id"]),
            request_type=document["request_type"],
            status=document["status"],
            creation_utc=datetime.fromisoformat(document["creation_utc"]),
            completion_utc=datetime.fromisoformat(document["completion_utc"]) if document.get("completion_utc") else None,
            notes=document.get("notes"),
            metadata=document.get("metadata", {}),
        )

    async def _initialize_default_requirements(self):
        """Initialize default compliance requirements."""
        # Check if requirements already exist
        count = await self._requirement_collection.count()
        if count > 0:
            return

        # Initialize GDPR requirements
        gdpr_requirements = [
            ComplianceRequirement(
                id=ComplianceRequirementId(generate_id()),
                framework=ComplianceFramework.GDPR,
                code="GDPR-1",
                name="Lawful Basis for Processing",
                description="Ensure personal data is processed lawfully, fairly, and transparently.",
                status=ComplianceRequirementStatus.PENDING,
                last_assessment=datetime.now(timezone.utc),
                next_assessment=datetime.now(timezone.utc) + timedelta(days=90),
            ),
            ComplianceRequirement(
                id=ComplianceRequirementId(generate_id()),
                framework=ComplianceFramework.GDPR,
                code="GDPR-2",
                name="Data Subject Rights",
                description="Implement mechanisms to handle data subject rights (access, rectification, erasure, etc.).",
                status=ComplianceRequirementStatus.PENDING,
                last_assessment=datetime.now(timezone.utc),
                next_assessment=datetime.now(timezone.utc) + timedelta(days=90),
            ),
            ComplianceRequirement(
                id=ComplianceRequirementId(generate_id()),
                framework=ComplianceFramework.GDPR,
                code="GDPR-3",
                name="Data Protection by Design",
                description="Implement appropriate technical and organizational measures for data protection.",
                status=ComplianceRequirementStatus.PENDING,
                last_assessment=datetime.now(timezone.utc),
                next_assessment=datetime.now(timezone.utc) + timedelta(days=90),
            ),
        ]

        # Initialize HIPAA requirements
        hipaa_requirements = [
            ComplianceRequirement(
                id=ComplianceRequirementId(generate_id()),
                framework=ComplianceFramework.HIPAA,
                code="HIPAA-1",
                name="Privacy Rule",
                description="Implement safeguards to protect the privacy of protected health information.",
                status=ComplianceRequirementStatus.PENDING,
                last_assessment=datetime.now(timezone.utc),
                next_assessment=datetime.now(timezone.utc) + timedelta(days=90),
            ),
            ComplianceRequirement(
                id=ComplianceRequirementId(generate_id()),
                framework=ComplianceFramework.HIPAA,
                code="HIPAA-2",
                name="Security Rule",
                description="Implement administrative, physical, and technical safeguards for electronic PHI.",
                status=ComplianceRequirementStatus.PENDING,
                last_assessment=datetime.now(timezone.utc),
                next_assessment=datetime.now(timezone.utc) + timedelta(days=90),
            ),
            ComplianceRequirement(
                id=ComplianceRequirementId(generate_id()),
                framework=ComplianceFramework.HIPAA,
                code="HIPAA-3",
                name="Breach Notification Rule",
                description="Implement procedures for breach notification.",
                status=ComplianceRequirementStatus.PENDING,
                last_assessment=datetime.now(timezone.utc),
                next_assessment=datetime.now(timezone.utc) + timedelta(days=90),
            ),
        ]

        # Save requirements
        for requirement in gdpr_requirements + hipaa_requirements:
            await self._requirement_collection.insert_one(
                document=self._serialize_requirement(requirement)
            )

        self._logger.info(f"Initialized default compliance requirements")

    async def add_requirement(
        self,
        framework: ComplianceFramework,
        code: str,
        name: str,
        description: str,
        status: ComplianceRequirementStatus = ComplianceRequirementStatus.PENDING,
        responsible_party: Optional[str] = None,
        evidence: Optional[str] = None,
        notes: Optional[str] = None,
        assessment_interval_days: int = 90,
    ) -> ComplianceRequirement:
        """Add a compliance requirement.

        Args:
            framework: Compliance framework
            code: Requirement code
            name: Requirement name
            description: Requirement description
            status: Requirement status
            responsible_party: Responsible party
            evidence: Evidence of compliance
            notes: Additional notes
            assessment_interval_days: Interval between assessments in days

        Returns:
            Created compliance requirement
        """
        async with self._lock.writer_lock:
            # Check if the requirement already exists
            existing = await self._requirement_collection.find_one(
                filters={
                    "framework": {"$eq": framework.value},
                    "code": {"$eq": code},
                }
            )

            if existing:
                raise ValueError(f"Requirement already exists: {framework.value}-{code}")

            # Create the requirement
            requirement = ComplianceRequirement(
                id=ComplianceRequirementId(generate_id()),
                framework=framework,
                code=code,
                name=name,
                description=description,
                status=status,
                last_assessment=datetime.now(timezone.utc),
                next_assessment=datetime.now(timezone.utc) + timedelta(days=assessment_interval_days),
                responsible_party=responsible_party,
                evidence=evidence,
                notes=notes,
            )

            # Save the requirement
            await self._requirement_collection.insert_one(
                document=self._serialize_requirement(requirement)
            )

            # Log the event
            await self._audit_logger.log_event(
                type=AuditEventType.CUSTOM,
                user_id=None,
                resource=f"compliance_requirement:{requirement.id}",
                action="create",
                status="success",
                severity=AuditEventSeverity.INFO,
                details={
                    "framework": framework.value,
                    "code": code,
                    "name": name,
                },
            )

            self._logger.info(f"Added compliance requirement: {framework.value}-{code}")

            return requirement

    async def update_requirement(
        self,
        requirement_id: ComplianceRequirementId,
        status: Optional[ComplianceRequirementStatus] = None,
        responsible_party: Optional[str] = None,
        evidence: Optional[str] = None,
        notes: Optional[str] = None,
        next_assessment: Optional[datetime] = None,
    ) -> Optional[ComplianceRequirement]:
        """Update a compliance requirement.

        Args:
            requirement_id: Requirement ID
            status: New status
            responsible_party: New responsible party
            evidence: New evidence
            notes: New notes
            next_assessment: New next assessment date

        Returns:
            Updated compliance requirement, or None if not found
        """
        async with self._lock.writer_lock:
            # Get the requirement
            requirement_doc = await self._requirement_collection.find_one(
                filters={"id": {"$eq": requirement_id}}
            )

            if not requirement_doc:
                return None

            # Update the requirement
            params = {}

            if status is not None:
                params["status"] = status.value

            if responsible_party is not None:
                params["responsible_party"] = responsible_party

            if evidence is not None:
                params["evidence"] = evidence

            if notes is not None:
                params["notes"] = notes

            if next_assessment is not None:
                params["next_assessment"] = next_assessment.isoformat()

            if params:
                # Update the last assessment date
                params["last_assessment"] = datetime.now(timezone.utc).isoformat()

                await self._requirement_collection.update_one(
                    filters={"id": {"$eq": requirement_id}},
                    params=params,
                )

                # Log the event
                await self._audit_logger.log_event(
                    type=AuditEventType.CUSTOM,
                    user_id=None,
                    resource=f"compliance_requirement:{requirement_id}",
                    action="update",
                    status="success",
                    severity=AuditEventSeverity.INFO,
                    details=params,
                )

                self._logger.info(f"Updated compliance requirement: {requirement_id}")

            # Get the updated requirement
            requirement_doc = await self._requirement_collection.find_one(
                filters={"id": {"$eq": requirement_id}}
            )

            return self._deserialize_requirement(requirement_doc)

    async def delete_requirement(
        self,
        requirement_id: ComplianceRequirementId,
    ) -> bool:
        """Delete a compliance requirement.

        Args:
            requirement_id: Requirement ID

        Returns:
            True if the requirement was deleted, False otherwise
        """
        async with self._lock.writer_lock:
            # Get the requirement
            requirement_doc = await self._requirement_collection.find_one(
                filters={"id": {"$eq": requirement_id}}
            )

            if not requirement_doc:
                return False

            # Delete the requirement
            result = await self._requirement_collection.delete_one(
                filters={"id": {"$eq": requirement_id}}
            )

            if result.deleted_count == 0:
                return False

            # Log the event
            await self._audit_logger.log_event(
                type=AuditEventType.CUSTOM,
                user_id=None,
                resource=f"compliance_requirement:{requirement_id}",
                action="delete",
                status="success",
                severity=AuditEventSeverity.INFO,
                details={
                    "framework": requirement_doc["framework"],
                    "code": requirement_doc["code"],
                },
            )

            self._logger.info(f"Deleted compliance requirement: {requirement_id}")

            return True

    async def get_requirement(
        self,
        requirement_id: ComplianceRequirementId,
    ) -> Optional[ComplianceRequirement]:
        """Get a compliance requirement by ID.

        Args:
            requirement_id: Requirement ID

        Returns:
            Compliance requirement if found, None otherwise
        """
        async with self._lock.reader_lock:
            # Get the requirement
            requirement_doc = await self._requirement_collection.find_one(
                filters={"id": {"$eq": requirement_id}}
            )

            if not requirement_doc:
                return None

            return self._deserialize_requirement(requirement_doc)

    async def list_requirements(
        self,
        framework: Optional[ComplianceFramework] = None,
        status: Optional[ComplianceRequirementStatus] = None,
        responsible_party: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ComplianceRequirement]:
        """List compliance requirements.

        Args:
            framework: Filter by framework
            status: Filter by status
            responsible_party: Filter by responsible party
            limit: Maximum number of requirements to return
            offset: Offset for pagination

        Returns:
            List of compliance requirements
        """
        async with self._lock.reader_lock:
            # Build filters
            filters = {}

            if framework is not None:
                filters["framework"] = {"$eq": framework.value}

            if status is not None:
                filters["status"] = {"$eq": status.value}

            if responsible_party is not None:
                filters["responsible_party"] = {"$eq": responsible_party}

            # Get requirements
            requirement_docs = await self._requirement_collection.find(
                filters=filters,
                sort=[("framework", 1), ("code", 1)],
                limit=limit,
                skip=offset,
            )

            return [self._deserialize_requirement(doc) for doc in requirement_docs]

    async def create_data_subject_request(
        self,
        user_id: UserId,
        request_type: str,
        notes: Optional[str] = None,
    ) -> DataSubjectRequest:
        """Create a data subject request.

        Args:
            user_id: User ID
            request_type: Request type (e.g., "access", "erasure")
            notes: Additional notes

        Returns:
            Created data subject request
        """
        async with self._lock.writer_lock:
            # Create the request
            request = DataSubjectRequest(
                id=generate_id(),
                user_id=user_id,
                request_type=request_type,
                status="pending",
                creation_utc=datetime.now(timezone.utc),
                notes=notes,
            )

            # Save the request
            await self._request_collection.insert_one(
                document=self._serialize_request(request)
            )

            # Log the event
            await self._audit_logger.log_event(
                type=AuditEventType.CUSTOM,
                user_id=user_id,
                resource=f"data_subject_request:{request.id}",
                action="create",
                status="success",
                severity=AuditEventSeverity.INFO,
                details={
                    "request_type": request_type,
                },
            )

            self._logger.info(f"Created data subject request: {request.id} ({request_type})")

            return request

    async def update_data_subject_request(
        self,
        request_id: str,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        completion_utc: Optional[datetime] = None,
    ) -> Optional[DataSubjectRequest]:
        """Update a data subject request.

        Args:
            request_id: Request ID
            status: New status
            notes: New notes
            completion_utc: Completion date

        Returns:
            Updated data subject request, or None if not found
        """
        async with self._lock.writer_lock:
            # Get the request
            request_doc = await self._request_collection.find_one(
                filters={"id": {"$eq": request_id}}
            )

            if not request_doc:
                return None

            # Update the request
            params = {}

            if status is not None:
                params["status"] = status

            if notes is not None:
                params["notes"] = notes

            if completion_utc is not None:
                params["completion_utc"] = completion_utc.isoformat()

            if params:
                await self._request_collection.update_one(
                    filters={"id": {"$eq": request_id}},
                    params=params,
                )

                # Log the event
                await self._audit_logger.log_event(
                    type=AuditEventType.CUSTOM,
                    user_id=request_doc["user_id"],
                    resource=f"data_subject_request:{request_id}",
                    action="update",
                    status="success",
                    severity=AuditEventSeverity.INFO,
                    details=params,
                )

                self._logger.info(f"Updated data subject request: {request_id}")

            # Get the updated request
            request_doc = await self._request_collection.find_one(
                filters={"id": {"$eq": request_id}}
            )

            return self._deserialize_request(request_doc)

    async def get_data_subject_request(
        self,
        request_id: str,
    ) -> Optional[DataSubjectRequest]:
        """Get a data subject request by ID.

        Args:
            request_id: Request ID

        Returns:
            Data subject request if found, None otherwise
        """
        async with self._lock.reader_lock:
            # Get the request
            request_doc = await self._request_collection.find_one(
                filters={"id": {"$eq": request_id}}
            )

            if not request_doc:
                return None

            return self._deserialize_request(request_doc)

    async def list_data_subject_requests(
        self,
        user_id: Optional[UserId] = None,
        request_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DataSubjectRequest]:
        """List data subject requests.

        Args:
            user_id: Filter by user ID
            request_type: Filter by request type
            status: Filter by status
            limit: Maximum number of requests to return
            offset: Offset for pagination

        Returns:
            List of data subject requests
        """
        async with self._lock.reader_lock:
            # Build filters
            filters = {}

            if user_id is not None:
                filters["user_id"] = {"$eq": user_id}

            if request_type is not None:
                filters["request_type"] = {"$eq": request_type}

            if status is not None:
                filters["status"] = {"$eq": status}

            # Get requests
            request_docs = await self._request_collection.find(
                filters=filters,
                sort=[("creation_utc", -1)],
                limit=limit,
                skip=offset,
            )

            return [self._deserialize_request(doc) for doc in request_docs]

    async def generate_compliance_report(
        self,
        framework: Optional[ComplianceFramework] = None,
    ) -> Dict[str, Any]:
        """Generate a compliance report.

        Args:
            framework: Filter by framework

        Returns:
            Compliance report
        """
        async with self._lock.reader_lock:
            # Get requirements
            requirements = await self.list_requirements(framework=framework, limit=1000)

            # Calculate statistics
            total = len(requirements)
            compliant = sum(1 for r in requirements if r.status == ComplianceRequirementStatus.COMPLIANT)
            non_compliant = sum(1 for r in requirements if r.status == ComplianceRequirementStatus.NON_COMPLIANT)
            partially_compliant = sum(1 for r in requirements if r.status == ComplianceRequirementStatus.PARTIALLY_COMPLIANT)
            not_applicable = sum(1 for r in requirements if r.status == ComplianceRequirementStatus.NOT_APPLICABLE)
            pending = sum(1 for r in requirements if r.status == ComplianceRequirementStatus.PENDING)

            # Group by framework
            framework_stats = {}
            for r in requirements:
                if r.framework.value not in framework_stats:
                    framework_stats[r.framework.value] = {
                        "total": 0,
                        "compliant": 0,
                        "non_compliant": 0,
                        "partially_compliant": 0,
                        "not_applicable": 0,
                        "pending": 0,
                    }

                framework_stats[r.framework.value]["total"] += 1

                if r.status == ComplianceRequirementStatus.COMPLIANT:
                    framework_stats[r.framework.value]["compliant"] += 1
                elif r.status == ComplianceRequirementStatus.NON_COMPLIANT:
                    framework_stats[r.framework.value]["non_compliant"] += 1
                elif r.status == ComplianceRequirementStatus.PARTIALLY_COMPLIANT:
                    framework_stats[r.framework.value]["partially_compliant"] += 1
                elif r.status == ComplianceRequirementStatus.NOT_APPLICABLE:
                    framework_stats[r.framework.value]["not_applicable"] += 1
                elif r.status == ComplianceRequirementStatus.PENDING:
                    framework_stats[r.framework.value]["pending"] += 1

            # Create the report
            report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "framework": framework.value if framework else "all",
                "summary": {
                    "total": total,
                    "compliant": compliant,
                    "non_compliant": non_compliant,
                    "partially_compliant": partially_compliant,
                    "not_applicable": not_applicable,
                    "pending": pending,
                    "compliance_rate": (compliant / total) if total > 0 else 0,
                },
                "framework_stats": framework_stats,
                "requirements": [
                    {
                        "id": r.id,
                        "framework": r.framework.value,
                        "code": r.code,
                        "name": r.name,
                        "status": r.status.value,
                        "last_assessment": r.last_assessment.isoformat(),
                        "next_assessment": r.next_assessment.isoformat(),
                    }
                    for r in requirements
                ],
            }

            # Log the event
            await self._audit_logger.log_event(
                type=AuditEventType.CUSTOM,
                user_id=None,
                resource="compliance_report",
                action="generate",
                status="success",
                severity=AuditEventSeverity.INFO,
                details={
                    "framework": framework.value if framework else "all",
                    "total": total,
                    "compliance_rate": (compliant / total) if total > 0 else 0,
                },
            )

            return report
