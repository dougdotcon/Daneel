"""
Security and privacy module for Daneel.

This module provides functionality for security and privacy features.
"""

from Daneel.security.auth import (
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

from Daneel.security.encryption import (
    EncryptionManager,
    EncryptionType,
    EncryptionError,
)

from Daneel.security.privacy import (
    PrivacyManager,
    PrivacyEntity,
    PrivacyEntityType,
    PrivacyDetectionResult,
    PrivacyError,
)

from Daneel.security.audit import (
    AuditLogger,
    AuditEvent,
    AuditEventId,
    AuditEventType,
    AuditEventSeverity,
)

from Daneel.security.compliance import (
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
