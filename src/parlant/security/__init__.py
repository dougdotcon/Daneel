"""
Security and privacy module for Parlant.

This module provides functionality for security and privacy features.
"""

from parlant.security.auth import (
    AuthManager,
    User,
    UserId,
    Token,
    TokenId,
    AuthRole,
    AuthPermission,
    AuthenticationError,
    AuthorizationError,
)

from parlant.security.encryption import (
    EncryptionManager,
    EncryptionType,
    EncryptionError,
)

from parlant.security.privacy import (
    PrivacyManager,
    PrivacyEntity,
    PrivacyEntityType,
    PrivacyDetectionResult,
    PrivacyError,
)

from parlant.security.audit import (
    AuditLogger,
    AuditEvent,
    AuditEventId,
    AuditEventType,
    AuditEventSeverity,
)

from parlant.security.compliance import (
    ComplianceManager,
    ComplianceFramework,
    ComplianceRequirement,
    ComplianceRequirementId,
    ComplianceRequirementStatus,
    DataSubjectRequest,
)

__all__ = [
    # Authentication and Authorization
    "AuthManager",
    "User",
    "UserId",
    "Token",
    "TokenId",
    "AuthRole",
    "AuthPermission",
    "AuthenticationError",
    "AuthorizationError",
    
    # Encryption
    "EncryptionManager",
    "EncryptionType",
    "EncryptionError",
    
    # Privacy
    "PrivacyManager",
    "PrivacyEntity",
    "PrivacyEntityType",
    "PrivacyDetectionResult",
    "PrivacyError",
    
    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditEventId",
    "AuditEventType",
    "AuditEventSeverity",
    
    # Compliance
    "ComplianceManager",
    "ComplianceFramework",
    "ComplianceRequirement",
    "ComplianceRequirementId",
    "ComplianceRequirementStatus",
    "DataSubjectRequest",
]
